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

    # Ensure non-negative delay
    if delay < 0:
        delay = 0

    from scheduler.services import TaskScheduler

    TaskScheduler.schedule(
        task_type="interview_feedback_reminder",
        task_kwargs={"booking_id": str(instance.id)},
        delay_seconds=int(delay),
        is_recurring=True,
        interval_seconds=7200,  # re-check every 2 hours
    )