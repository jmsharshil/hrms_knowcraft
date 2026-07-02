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

    # Normalize to aware datetime (prevents TZ comparison bugs between
    # stored Booking.end and scheduler/task checks). Schedule first reminder
    # 30 minutes AFTER interview end time. This prevents reminders before
    # the interview has actually ended.
    end = instance.end
    if timezone.is_naive(end):
        end = timezone.make_aware(end, timezone.get_current_timezone())
    buffer_after_end = timedelta(minutes=30)
    target_time = end + buffer_after_end
    delay = (target_time - timezone.now()).total_seconds()

    # Ensure non-negative delay (if booking created/updated after end time,
    # run the task immediately — the task's own check will still skip if needed).
    if delay < 0:
        delay = 0

    from scheduler.services import TaskScheduler

    # Compute canonical round_name at schedule time using full status map.
    # This decouples from later status changes on the candidate and ensures
    # we always pass a valid interview_round value that matches both the
    # InterviewFeedback.interview_round choices and the get_feedback_link mapping.
    status_to_round = {
        "shortlisted": "hr_round",
        "interview_pending_1": "hr_round",
        "interview_done_1": "hr_round",
        "interview_rejected_1": "hr_round",
        "interview_next_2": "technical_round",
        "interview_pending_2": "technical_round",
        "interview_done_2": "technical_round",
        "interview_rejected_2": "technical_round",
        "interview_next_3": "case_study_round",
        "interview_pending_3": "case_study_round",
        "interview_done_3": "case_study_round",
        "interview_rejected_3": "case_study_round",
        "interview_next_final": "final_round",
        "interview_pending_final": "final_round",
        "interview_done_final": "final_round",
        "interview_rejected_final": "final_round",
        "interview_next_management_client": "management_client_round",
        "interview_pending_management_client": "management_client_round",
        "interview_done_management_client": "management_client_round",
        "interview_rejected_management_client": "management_client_round",
    }

    computed_round = status_to_round.get(
        instance.candidate.status,
        getattr(instance.candidate, "round_name", None)
    )
    round_name = computed_round or "final_round"

    # Pass both booking_id and the round_name so that the task can target the
    # exact feedback round immediately. The task falls back to its own
    # status-to-round mapping if the passed round_name is None.

    # Cancel existing pending tasks for this booking (by booking_id) so we don't
    # get duplicates if a booking is rescheduled.
    TaskScheduler.cancel(
        task_type="interview_feedback_reminder",
        task_kwargs_filter={"booking_id": str(instance.id)}
    )

    TaskScheduler.schedule(
        task_type="interview_feedback_reminder",
        task_kwargs={
            "booking_id": str(instance.id),
            "round_name": round_name,
        },
        delay_seconds=int(delay),
        is_recurring=True,
        interval_seconds=7200,  # re-check every 2 hours
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