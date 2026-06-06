# interview/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking
from django.utils import timezone

@receiver(post_save, sender=Booking)
def schedule_feedback_reminder(sender, instance, created, **kwargs):
    # Only enqueue if interview end time is set
    if not instance.end:
        return

    delay = (instance.end - timezone.now()).total_seconds()

    # # If already past (edge case)
    # if delay <= 0:
    #     TASK_QUEUE.enqueue(interview_feedback_reminder_task, instance.id)
    #     return

    # import threading

    # threading.Timer(delay, lambda: TASK_QUEUE.enqueue(
    #     interview_feedback_reminder_task, instance.id
    # )).start()

    # Ensure non-negative delay
    if delay < 0:
        delay = 0

    from scheduler.services import TaskScheduler

    # Cancel existing pending tasks for this booking so we don't get duplicates if rescheduled
    TaskScheduler.cancel(
        task_type="interview_feedback_reminder",
        task_kwargs_filter={"booking_id": str(instance.id)}
    )

    TaskScheduler.schedule(
        task_type="interview_feedback_reminder",
        task_kwargs={"booking_id": str(instance.id)},
        delay_seconds=int(delay),
        is_recurring=True,
        interval_seconds=7200,  # re-check every 2 hours
    )