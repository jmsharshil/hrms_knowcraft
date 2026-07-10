# booking/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Booking
from django.utils import timezone
from datetime import timedelta

@receiver(post_save, sender=Booking)
def schedule_feedback_reminder(sender, instance, created, **kwargs):
    # Only enqueue if interview end time is set
    if not instance.end:
        return

    from scheduler.services import TaskScheduler
    from scheduler.models import ScheduledTask

    # Map candidate status → interview round name (frozen at booking time
    # so it survives later status changes).
    # Only statuses that represent an active/pending interview should
    # trigger a reminder. Once the candidate has moved past the interview
    # (done/rejected/next) the booking signal should NOT create a new task.
    PENDING_STATUS_TO_ROUND = {
        "shortlisted": "hr_round",
        "interview_pending_1": "hr_round",
        "interview_pending_2": "technical_round",
        "interview_pending_3": "case_study_round",
        "interview_pending_final": "final_round",
        "interview_pending_management_client": "management_client_round",
    }

    candidate_status = instance.candidate.status
    round_name = PENDING_STATUS_TO_ROUND.get(
        candidate_status,
        getattr(instance.candidate, "round_name", None)
    )

    if not round_name:
        # Status is not an interview_pending_* — nothing to remind about.
        import logging
        logging.getLogger(__name__).info(
            "[BOOKING SIGNAL] Skipping reminder schedule: candidate %s has status '%s' "
            "which is not an interview-pending state.",
            instance.candidate.id, candidate_status
        )
        return

    # Normalize end to aware datetime and compute delay.
    end = instance.end
    if timezone.is_naive(end):
        end = timezone.make_aware(end, timezone.get_current_timezone())
    target_time = end + timedelta(minutes=30)
    delay = max((target_time - timezone.now()).total_seconds(), 0)

    # Cancel any existing tasks for this booking before creating a fresh one
    # (prevents duplicates on booking reschedule / save).
    TaskScheduler.cancel(
        task_type="interview_feedback_reminder",
        task_kwargs_filter={"booking_id": str(instance.id)}
    )
    ScheduledTask.objects.filter(
        task_type="interview_feedback_reminder",
        status="running",
        task_kwargs__contains={"booking_id": str(instance.id)},
    ).update(status="cancelled", updated_at=timezone.now())

    TaskScheduler.schedule(
        task_type="interview_feedback_reminder",
        task_kwargs={
            "booking_id": str(instance.id),
            "round_name": round_name,
        },
        delay_seconds=int(delay),
        is_recurring=True,
        interval_seconds=7200,  # re-check every 2 hours if feedback still pending
    )


@receiver(pre_delete, sender=Booking)
def cancel_feedback_reminder_on_delete(sender, instance, **kwargs):
    """
    Cancel all pending/running feedback reminder tasks when a Booking is
    deleted (cancelled interview, graph webhook deletion, admin action, etc.).
    This is the safety-net — ensures no orphan reminders survive regardless
    of the deletion path.
    """
    from scheduler.services import TaskScheduler
    from scheduler.models import ScheduledTask

    TaskScheduler.cancel(
        task_type="interview_feedback_reminder",
        task_kwargs_filter={"booking_id": str(instance.id)},
    )
    # Also cancel any currently-running tasks (race condition guard)
    ScheduledTask.objects.filter(
        task_type="interview_feedback_reminder",
        status="running",
        task_kwargs__contains={"booking_id": str(instance.id)},
    ).update(status="cancelled", updated_at=timezone.now())