# scheduler/apps.py

import os
import sys
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


def _seconds_until_next_friday_630pm():
    """
    Return the number of seconds from *now* (IST) until the next
    Friday at 18:30 IST (UTC+5:30).

    If today is already Friday but before 18:30, the delay targets
    today's 18:30.  If it is Friday at/after 18:30 the next Friday
    (7 days later) is targeted instead.
    """
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    ist = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(ist)

    # weekday(): Monday=0 … Friday=4 … Sunday=6
    days_ahead = (4 - now_ist.weekday()) % 7          # 0 if today is Friday
    target = now_ist.replace(
        hour=18, minute=30, second=0, microsecond=0
    )
    if days_ahead == 0 and now_ist >= target:
        # Already past 18:30 on Friday — aim for next Friday
        days_ahead = 7

    target += timedelta(days=days_ahead)

    delay = (target - now_ist).total_seconds()
    logger.info(
        "[SCHEDULER] Next weekly report scheduled in %.0fs (at %s IST).",
        delay, target.strftime("%A %Y-%m-%d %H:%M %Z"),
    )
    return int(max(delay, 0))


def _seconds_until_next_morning_9am():
    """
    Return the number of seconds from *now* (IST) until the next
    morning at 09:00 IST (UTC+5:30).

    If today is before 09:00 IST, the delay targets today's 09:00 IST.
    If it is at/after 09:00 IST, targets tomorrow's 09:00 IST.
    """
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    ist = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(ist)

    target = now_ist.replace(hour=9, minute=0, second=0, microsecond=0)
    if now_ist >= target:
        target += timedelta(days=1)

    delay = (target - now_ist).total_seconds()
    logger.info(
        "[SCHEDULER] Next daily onboarding check scheduled in %.0fs (at %s IST).",
        delay, target.strftime("%A %Y-%m-%d %H:%M %Z"),
    )
    return int(max(delay, 0))


class SchedulerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "scheduler"
    _started = False  # Class-level flag to prevent duplicate starts

    def ready(self):
        # Prevent during management commands
        ignored_commands = [
            "test", "makemigrations", "migrate", "showmigrations",
            "collectstatic", "reconcile_tasks", "check", "check_migrations",
        ]
        if any(cmd in sys.argv for cmd in ignored_commands):
            return

        # Prevent duplicate starts
        if SchedulerConfig._started:
            return

        # Only in the main process
        run_main = os.environ.get("RUN_MAIN")
        werkzeug_main = os.environ.get("WERKZEUG_RUN_MAIN")

        is_main_process = (
            run_main == "true"
            or werkzeug_main == "true"
            or (run_main is None and werkzeug_main is None)
        )

        if not is_main_process:
            print("[SCHEDULER APP] Not main process — skipping startup.")
            return

        SchedulerConfig._started = True
        print("[SCHEDULER APP] Initialising persistent task scheduler...")

        # ── Register all known task types ────────────────────────
        self._register_tasks()

        # ── Reconcile incomplete tasks from DB ───────────────────
        from onboarding.utils.task_queue import TASK_QUEUE

        def _startup():
            """Run coordinated recovery and start this worker's poller."""
            from django.db import close_old_connections
            from .services import TaskScheduler

            close_old_connections()

            def _coordinate_startup():
                print("[SCHEDULER APP] Running startup reconciliation...")
                self._ensure_recurring_tasks()
                TaskScheduler.reconcile()
                TaskScheduler.reschedule_future_pending()

            try:
                if TaskScheduler.run_if_coordinator(_coordinate_startup):
                    print("[SCHEDULER APP] Startup reconciliation complete.")
            except Exception:
                logger.exception("[SCHEDULER APP] Startup reconciliation failed.")
            finally:
                # Each worker has a poller; the shared PostgreSQL advisory lock
                # ensures only one worker reconciles at a time.
                self._start_background_poller()
                close_old_connections()

        # Enqueue so it runs after Django is fully loaded
        TASK_QUEUE.enqueue(_startup)

    def _register_tasks(self):
        """Register all task_type → callable mappings."""
        from .services import TaskScheduler

        # Interview feedback reminder (supports optional round_name for per-round targeting)
        from onboarding.utils.interview_feedback_reminder import (
            interview_feedback_reminder_task,
        )
        TaskScheduler.register(
            "interview_feedback_reminder",
            interview_feedback_reminder_task,  # directly register; accepts booking_id + round_name=None
        )

        # MRF approval reminder (submit reminder — fires while MRF is in draft)
        from onboarding.utils.mrf_send_reminder import mrf_approval_reminder_task
        TaskScheduler.register(
            "mrf_approval_reminder",
            lambda mrf_id: mrf_approval_reminder_task(mrf_id),
        )

        # MRF pending approval reminder (fires 48h after submit/approval to remind the next approver)
        from mrf.utils import mrf_pending_approval_reminder_task
        TaskScheduler.register(
            "mrf_pending_approval_reminder",
            lambda mrf_id: mrf_pending_approval_reminder_task(mrf_id),
        )

        # BGV status poll
        from bgv.tasks import run_bgv_status_poll
        TaskScheduler.register("bgv_status_poll", lambda: run_bgv_status_poll())

        # BGV schedule check
        from bgv.tasks import run_bgv_schedule_check
        TaskScheduler.register("bgv_schedule_check", lambda: run_bgv_schedule_check())

        # BGV form reminder
        from bgv.tasks import bgv_form_reminder_task
        TaskScheduler.register(
            "bgv_form_reminder",
            lambda bgv_id: bgv_form_reminder_task(bgv_id)
        )

        # Audit log flush
        from auditlog.tasks import flush_logs_to_blob
        TaskScheduler.register("audit_log_flush", lambda: flush_logs_to_blob())

        # Joining date check
        from onboarding.utils.joining_check import run_joining_date_check
        TaskScheduler.register("joining_date_check", lambda: run_joining_date_check())

        # Daily Onboarding Check
        from onboarding.utils.onboarding_tasks import daily_onboarding_check
        TaskScheduler.register("daily_onboarding_check", lambda: daily_onboarding_check())

        # Auto-reject stale on-hold MRFs (> 60 days)
        from mrf.utils import auto_reject_stale_held_mrfs
        TaskScheduler.register("mrf_auto_reject_held", lambda: auto_reject_stale_held_mrfs())

        # Weekly Department Head Report
        from mrf.utils import dept_head_weekly_report_task
        TaskScheduler.register("dept_head_weekly_report", lambda: dept_head_weekly_report_task())

        # Candidate Experience Feedback 24h Reminder
        from onboarding.utils.notifications import candidate_feedback_reminder_task
        TaskScheduler.register(
            "candidate_feedback_reminder",
            lambda feedback_id=None: candidate_feedback_reminder_task(feedback_id),
        )

        print("[SCHEDULER APP] All task types registered.")

    def _ensure_recurring_tasks(self):
        """
        Make sure each recurring system task has at least one pending row.
        If not (fresh deploy or all completed), create one.
        """
        from .services import TaskScheduler

        RECURRING_TASKS = [
            {
                "task_type": "bgv_status_poll",
                "interval_seconds": 3600,        # 1 hour
                "delay_seconds": 10,             # first run after 10s
                "max_retries": 3,
            },
            {
                "task_type": "audit_log_flush",
                "interval_seconds": 300,         # 5 minutes
                "delay_seconds": 30,             # first run after 30s
                "max_retries": 3,
            },
            {
                "task_type": "joining_date_check",
                "interval_seconds": 3600,        # 1 hour
                "delay_seconds": 15,             # first run after 15s
                "max_retries": 3,
            },
            {
                "task_type": "daily_onboarding_check",
                "interval_seconds": 86400,       # 1 day
                "delay_seconds": _seconds_until_next_morning_9am(),  # 09:00 IST every morning
                "max_retries": 3,
            },
            {
                "task_type": "mrf_auto_reject_held",
                "interval_seconds": 86400,       # 1 day
                "delay_seconds": 25,             # first run after 25s
                "max_retries": 3,
            },
            {
                "task_type": "dept_head_weekly_report",
                "interval_seconds": 604800,      # 7 days (weekly) — kept for fallback
                "delay_seconds": _seconds_until_next_friday_630pm(),  # next Friday 18:30 IST
                "max_retries": 2,
            },
        ]

        import datetime as _dt
        from .models import ScheduledTask
        from django.utils import timezone as tz

        for cfg in RECURRING_TASKS:
            # Deduplicate any duplicate pending rows that may have accumulated
            pending_rows = list(ScheduledTask.objects.filter(
                task_type=cfg["task_type"],
                status="pending"
            ).order_by("-created_at"))
            if len(pending_rows) > 1:
                dup_ids = [r.id for r in pending_rows[1:]]
                ScheduledTask.objects.filter(id__in=dup_ids).update(
                    status="cancelled",
                    error_message="Cancelled duplicate recurring task during multi-worker deduplication"
                )
                logger.info("[SCHEDULER] Cancelled %d duplicate pending '%s' task(s).", len(dup_ids), cfg["task_type"])

            # ── Weekly report: guard against stale scheduled_at ───────────────
            # If a pending row already exists but its scheduled_at is in the
            # past (server was down over the weekend / restart after a crash),
            # bump it forward to the next Friday 18:30 IST BEFORE reconcile()
            # runs, so reconcile() does not fire the report immediately.
            # The in-memory timer is then re-armed by reschedule_future_pending()
            # which runs right after _ensure_recurring_tasks().
            if cfg["task_type"] == "dept_head_weekly_report" and pending_rows:
                surviving_row = pending_rows[0]
                if surviving_row.scheduled_at <= tz.now():
                    new_delay = _seconds_until_next_friday_630pm()
                    new_scheduled_at = tz.now() + _dt.timedelta(seconds=new_delay)
                    ScheduledTask.objects.filter(id=surviving_row.id).update(
                        scheduled_at=new_scheduled_at,
                    )
                    logger.info(
                        "[SCHEDULER] Bumped stale 'dept_head_weekly_report' "
                        "scheduled_at to %s IST (in %ds). "
                        "reschedule_future_pending() will re-arm the in-memory timer.",
                        new_scheduled_at, new_delay,
                    )
                    continue  # skip schedule() — row already exists and will be re-armed

            # ── Daily onboarding check: guard against stale scheduled_at ─────
            # If a pending row already exists but its scheduled_at is in the
            # past (e.g. server restart), bump it to the next morning 09:00 IST
            # so it does not fire immediately on startup.
            if cfg["task_type"] == "daily_onboarding_check" and pending_rows:
                surviving_row = pending_rows[0]
                if surviving_row.scheduled_at <= tz.now():
                    new_delay = _seconds_until_next_morning_9am()
                    new_scheduled_at = tz.now() + _dt.timedelta(seconds=new_delay)
                    ScheduledTask.objects.filter(id=surviving_row.id).update(
                        scheduled_at=new_scheduled_at,
                    )
                    logger.info(
                        "[SCHEDULER] Bumped stale 'daily_onboarding_check' "
                        "scheduled_at to %s IST (in %ds).",
                        new_scheduled_at, new_delay,
                    )
                    continue

            TaskScheduler.schedule(
                task_type=cfg["task_type"],
                delay_seconds=cfg["delay_seconds"],
                is_recurring=True,
                interval_seconds=cfg["interval_seconds"],
                max_retries=cfg["max_retries"],
            )

    def _start_background_poller(self):
        """
        Start a poller in this worker. A PostgreSQL advisory lock ensures only
        one Gunicorn worker reconciles tasks during each polling interval.
        """
        import threading
        import time
        from django.db import close_old_connections
        from .services import TaskScheduler

        def _poller_worker():
            print("[SCHEDULER POLLER] Dedicated poller thread started (polling every 30s).")
            # Wait 5 seconds before first poll to let Django finish booting
            time.sleep(5)
            while True:
                try:
                    close_old_connections()
                    TaskScheduler.run_if_coordinator(TaskScheduler.reconcile)
                except Exception as exc:
                    logger.exception("[SCHEDULER POLLER] Exception during task poll: %s", exc)
                finally:
                    close_old_connections()
                time.sleep(30)

        t = threading.Thread(target=_poller_worker, name="TaskSchedulerPoller", daemon=True)
        t.start()
        print("[SCHEDULER APP] Background poller daemon armed (every 30s).")
