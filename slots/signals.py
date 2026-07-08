from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import InterviewFeedback
from jobs.models import JobApplication
import logging

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=InterviewFeedback)
def update_consolidated_feedback_avg(sender, instance, **kwargs):
    application = instance.job_application

    feedbacks = application.interview_feedbacks.all()

    scores = []

    for feedback in feedbacks:
        avg = feedback.get_round_avg()
        if avg is not None:
            scores.append(avg)

    consolidated_avg = round(sum(scores) / len(scores), 2) if scores else 0
    JobApplication.objects.filter(id=application.id).update(
        consolidated_feedback_avg=consolidated_avg
    )


@receiver(post_save, sender=InterviewFeedback)
def cancel_reminder_on_feedback_submit(sender, instance, created, **kwargs):
    """
    When an InterviewFeedback record is created (or updated), proactively
    cancel all pending/running feedback-reminder tasks for every booking
    belonging to this candidate.  This is the definitive stop mechanism:
    even if the view-level cancel fails or the feedback is submitted via
    a different code path, this signal ensures no stale reminder fires.
    """
    if not created:
        # Only trigger on initial submission; updates don't need a new cancel.
        return

    try:
        from booking.models import Booking
        from scheduler.services import TaskScheduler
        from scheduler.models import ScheduledTask
        from django.utils import timezone

        application = instance.job_application
        bookings = Booking.objects.filter(candidate=application)

        for booking in bookings:
            cancelled = TaskScheduler.cancel(
                "interview_feedback_reminder",
                task_kwargs_filter={"booking_id": str(booking.id)},
            )
            # Also forcibly mark any currently-running tasks as cancelled so
            # they won't reschedule themselves once they finish.
            ScheduledTask.objects.filter(
                task_type="interview_feedback_reminder",
                status="running",
                task_kwargs__contains={"booking_id": str(booking.id)},
            ).update(status="cancelled", updated_at=timezone.now())

            if cancelled:
                logger.info(
                    "[FEEDBACK SIGNAL] Cancelled %d reminder task(s) for booking %s "
                    "(feedback submitted for round=%s, candidate=%s).",
                    cancelled, booking.id, instance.interview_round, application.id
                )
    except Exception as exc:
        logger.warning(
            "[FEEDBACK SIGNAL] Failed to cancel reminder tasks after feedback submit: %s", exc
        )
