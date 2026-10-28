# scheduler/services.py

"""
TaskScheduler — central service for DB-persisted background tasks.

Usage:
    from scheduler.services import TaskScheduler

    # one-shot delayed task
    TaskScheduler.schedule(
        task_type="interview_feedback_reminder",
        task_kwargs={"booking_id": str(booking.id)},
        delay_seconds=7200,
    )

    # recurring task
    TaskScheduler.schedule(
        task_type="bgv_status_poll",
        delay_seconds=0,
        is_recurring=True,
        interval_seconds=3600,
    )
"""

import logging
import threading
from datetime import timedelta

from django.db import connection, transaction
from django.utils import timezone

logger = logging.getLogger(__name__)
SCHEDULER_COORDINATOR_LOCK_ID = 7241956831201


class TaskScheduler:
    """
    Manages DB-persisted scheduled tasks with in-process execution.

    - ``schedule()``    → create DB row + start an in-memory timer
    - ``cancel()``      → mark matching pending tasks as cancelled
    - ``reconcile()``   → re-schedule all incomplete/missed tasks from DB
    - ``register()``    → map a *task_type* string to a callable
    """

    # task_type → callable
    _registry: dict = {}

    # task IDs that have been armed in-memory in this process lifetime.
    # Used to prevent reconcile/reschedule_future_pending from double-arming
    # tasks that schedule() already armed.
    _armed_task_ids: set = set()

    @classmethod
    def run_if_coordinator(cls, callback):
        """
        Run scheduler-wide coordination under a PostgreSQL transaction lock.

        Every Gunicorn worker may start a poller, but only one worker can
        reconcile or create recurring tasks at a time. The lock is released
        automatically if the database connection or process goes away.
        """
        if connection.vendor != "postgresql":
            raise RuntimeError(
                "The multi-worker scheduler requires PostgreSQL advisory locks."
            )

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_try_advisory_xact_lock(%s)",
                    [SCHEDULER_COORDINATOR_LOCK_ID],
                )
                acquired = cursor.fetchone()[0]

            if not acquired:
                return False

            callback()
            return True

    # ── Registration ─────────────────────────────────────────────

    @classmethod
    def register(cls, task_type: str, fn):
        """Register a callable under *task_type*."""
        cls._registry[task_type] = fn
        logger.info("[SCHEDULER] Registered task type: %s", task_type)

    # ── Scheduling ───────────────────────────────────────────────

    @classmethod
    def schedule(
        cls,
        task_type: str,
        task_kwargs: dict | None = None,
        delay_seconds: int = 0,
        is_recurring: bool = False,
        interval_seconds: int | None = None,
        max_retries: int = 3,
    ):
        """
        Persist a new task to the DB and schedule it in memory.

        For recurring tasks that should be singletons (e.g. BGV poll),
        this skips creation if a pending task of the same type already exists.
        """
        from .models import ScheduledTask

        task_kwargs = task_kwargs or {}

        # ── Singleton guard for recurring tasks ───────────
        if is_recurring:
            # Check for existing pending row
            existing_qs = ScheduledTask.objects.filter(
                task_type=task_type,
                status="pending",
            )
            if task_kwargs:
                existing_qs = existing_qs.filter(task_kwargs=task_kwargs)
            else:
                existing_qs = existing_qs.filter(task_kwargs__in=[{}, None])

            existing_task = existing_qs.order_by("-created_at").first()
            if existing_task:
                # If the existing pending task is already due or overdue, ensure it's armed/reconciled
                now = timezone.now()
                if existing_task.scheduled_at <= now:
                    logger.info(
                        "[SCHEDULER] Recurring task '%s' already pending and due (%s) — re-arming.",
                        task_type, existing_task.scheduled_at
                    )
                    cls._armed_task_ids.discard(existing_task.id)
                    cls._schedule_in_memory(existing_task.id, delay_seconds=0)
                else:
                    logger.info(
                        "[SCHEDULER] Recurring task '%s' already pending for %s — skipped duplicate.",
                        task_type, existing_task.scheduled_at
                    )
                return existing_task

        scheduled_at = timezone.now() + timedelta(seconds=delay_seconds)

        task = ScheduledTask.objects.create(
            task_type=task_type,
            task_kwargs=task_kwargs,
            status="pending",
            scheduled_at=scheduled_at,
            is_recurring=is_recurring,
            interval_seconds=interval_seconds,
            max_retries=max_retries,
        )

        print(
            f"[SCHEDULER] Created task {task.id} "
            f"type={task_type} delay={delay_seconds}s "
            f"recurring={is_recurring}"
        )

        cls._schedule_in_memory(task.id, max(delay_seconds, 0))
        return task

    # ── Cancellation ─────────────────────────────────────────────

    @classmethod
    def cancel(cls, task_type: str, task_kwargs_filter: dict | None = None):
        """
        Cancel all *pending* tasks that match *task_type*.

        If *task_kwargs_filter* is supplied, only tasks whose ``task_kwargs``
        is a superset of the filter dict are cancelled.

        Also removes matching IDs from _armed_task_ids so in-memory timers
        for cancelled tasks are ignored on fire (more foolproof against races).
        """
        from .models import ScheduledTask

        qs = ScheduledTask.objects.filter(
            task_type=task_type,
            status="pending",
        )

        if task_kwargs_filter:
            # JSONField containment lookup
            qs = qs.filter(task_kwargs__contains=task_kwargs_filter)

        # Fetch IDs before update so we can clean armed set
        task_ids = list(qs.values_list("id", flat=True))

        count = qs.update(status="cancelled", updated_at=timezone.now())
        if count:
            for tid in task_ids:
                cls._armed_task_ids.discard(tid)
            print(f"[SCHEDULER] Cancelled {count} pending '{task_type}' task(s).")
        return count

    # ── Execution ────────────────────────────────────────────────

    @classmethod
    def _execute(cls, task_id):
        """
        Called by TASK_QUEUE workers. Loads the DB row, runs the
        registered function, and updates the status accordingly.
        """
        from django.db import transaction, close_old_connections
        from .models import ScheduledTask

        close_old_connections()

        # ── Phase 1: Claim the task inside a short atomic block ──────
        with transaction.atomic():
            try:
                # Use select_for_update to lock the row and skip if another worker already grabbed it
                task = ScheduledTask.objects.select_for_update(skip_locked=True).get(id=task_id)
            except ScheduledTask.DoesNotExist:
                # Already grabbed by another worker or not in DB
                return

            # ── Guard: skip if already cancelled, completed, or running ────────
            if task.status in ("cancelled", "completed", "running"):
                return

            fn = cls._registry.get(task.task_type)
            if fn is None:
                logger.error(
                    "[SCHEDULER] No registered function for task_type='%s'",
                    task.task_type,
                )
                task.status = "failed"
                task.error_message = f"Unknown task_type: {task.task_type}"
                task.save(update_fields=["status", "error_message", "updated_at"])
                return

            # ── Mark running ─────────────────────────────────────────
            task.status = "running"
            task.started_at = timezone.now()
            task.save(update_fields=["status", "started_at", "updated_at"])

        # ── Phase 2: Execute OUTSIDE the transaction ─────────────────
        kwargs = task.task_kwargs or {}
        try:
            print(f"[SCHEDULER] Executing task {task_id} ({task.task_type})...")
            close_old_connections()
            result = fn(**kwargs)

            close_old_connections()
            task.refresh_from_db()
            if task.status == "cancelled":
                print(f"[SCHEDULER] Task {task_id} was cancelled during execution — not rescheduling.")
                return

            # ── Success ──────────────────────────────────────────
            task.status = "completed"
            task.completed_at = timezone.now()
            task.save(update_fields=["status", "completed_at", "updated_at"])
            print(f"[SCHEDULER] Task {task_id} completed successfully.")

            # Recurring only on success and if the task function did not return False
            if (
                task.is_recurring
                and task.interval_seconds
                and result is not False
            ):
                print(
                    f"[SCHEDULER] Recurring task '{task.task_type}' — "
                    f"scheduling next run in {task.interval_seconds}s"
                )
                cls.schedule(
                    task_type=task.task_type,
                    task_kwargs=task.task_kwargs if task.task_kwargs else None,
                    delay_seconds=task.interval_seconds,
                    is_recurring=True,
                    interval_seconds=task.interval_seconds,
                    max_retries=task.max_retries,
                )

        except Exception as exc:
            logger.exception(
                "[SCHEDULER] Task %s (%s) failed: %s",
                task_id, task.task_type, exc,
            )
            close_old_connections()
            task.refresh_from_db()
            task.retry_count += 1

            if task.retry_count < task.max_retries:
                # ── Retry with exponential backoff ───────────────
                backoff = 2 ** task.retry_count
                task.status = "pending"
                task.scheduled_at = timezone.now() + timedelta(seconds=backoff)
                task.error_message = str(exc)
                task.save(update_fields=[
                    "status", "retry_count", "scheduled_at",
                    "error_message", "updated_at",
                ])
                print(
                    f"[SCHEDULER] Task {task_id} will retry "
                    f"({task.retry_count}/{task.max_retries}) in {backoff}s"
                )
                cls._schedule_in_memory(task_id, backoff)
            else:
                task.status = "failed"
                task.error_message = str(exc)
                task.save(update_fields=[
                    "status", "retry_count", "error_message", "updated_at",
                ])
                print(f"[SCHEDULER] Task {task_id} failed permanently after {task.max_retries} retries.")

                # If recurring, schedule the next cycle so recurrence doesn't die forever
                if task.is_recurring and task.interval_seconds:
                    logger.warning(
                        "[SCHEDULER] Recurring task '%s' failed all retries. "
                        "Scheduling next run in %ds to keep recurrence alive.",
                        task.task_type, task.interval_seconds
                    )
                    cls.schedule(
                        task_type=task.task_type,
                        task_kwargs=task.task_kwargs if task.task_kwargs else None,
                        delay_seconds=task.interval_seconds,
                        is_recurring=True,
                        interval_seconds=task.interval_seconds,
                        max_retries=task.max_retries,
                    )
        finally:
            close_old_connections()

    # ── Reconciliation ───────────────────────────────────────────

    @classmethod
    def reconcile(cls):
        """
        Re-schedule overdue pending tasks. Running tasks are not retried
        automatically because they may still be performing external side effects.
        """
        from django.db import close_old_connections
        from .models import ScheduledTask

        if not connection.in_atomic_block:
            close_old_connections()
        now = timezone.now()

        # 1. Tasks that were pending and their time has arrived/passed
        missed_pending = list(
            ScheduledTask.objects.filter(
                status="pending",
                scheduled_at__lte=now,
            ).values_list("id", flat=True)
        )

        if not missed_pending:
            return

        print(
            f"[SCHEDULER] Reconciliation: re-scheduling {len(missed_pending)} overdue task(s)."
        )

        for task_id in missed_pending:
            # Force discard from armed set so it is guaranteed to run
            cls._armed_task_ids.discard(task_id)
            cls._schedule_in_memory(task_id, delay_seconds=0)

    # ── Future pending tasks ─────────────────────────────────────

    @classmethod
    def reschedule_future_pending(cls):
        """
        Re-arm future pending tasks in this worker.
        """
        from .models import ScheduledTask

        if not connection.in_atomic_block:
            from django.db import close_old_connections

            close_old_connections()
        now = timezone.now()
        future_tasks = list(
            ScheduledTask.objects.filter(
                status="pending",
                scheduled_at__gt=now,
            ).values_list("id", "scheduled_at")
        )

        if not future_tasks:
            return

        print(
            f"[SCHEDULER] Re-arming {len(future_tasks)} future pending task(s)."
        )
        for task_id, scheduled_at in future_tasks:
            if task_id in cls._armed_task_ids:
                continue
            delay = max((scheduled_at - now).total_seconds(), 0)
            cls._schedule_in_memory(task_id, delay)

    # ── In-memory scheduling ─────────────────────────────────────

    @classmethod
    def _schedule_in_memory(cls, task_id, delay_seconds: float):
        """
        Create a daemon ``threading.Timer`` that enqueues ``_execute``
        into the global TASK_QUEUE after *delay_seconds*.
        """
        from onboarding.utils.task_queue import TASK_QUEUE

        # Track that we've armed this task in this process lifetime
        cls._armed_task_ids.add(task_id)

        def _enqueue():
            # Remove from armed set so it can be re-armed after execution
            cls._armed_task_ids.discard(task_id)
            TASK_QUEUE.enqueue(cls._execute, task_id)

        if delay_seconds <= 0:
            # Execute immediately
            _enqueue()
        else:
            timer = threading.Timer(delay_seconds, _enqueue)
            timer.daemon = True
            timer.start()
