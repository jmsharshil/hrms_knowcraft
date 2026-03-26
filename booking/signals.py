# interview/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking
from onboarding.utils.task_queue import TASK_QUEUE
from onboarding.utils.interview_feedback_reminder import interview_feedback_reminder_task
from django.utils import timezone

@receiver(post_save, sender=Booking)
def schedule_feedback_reminder(sender, instance, created, **kwargs):
    # Only enqueue if interview end time is passed
    if not instance.end:
        return

    delay = (instance.end - timezone.now()).total_seconds()

    # If already past (edge case)
    if delay <= 0:
        TASK_QUEUE.enqueue(interview_feedback_reminder_task, instance.id)
        return

    import threading

    threading.Timer(delay, lambda: TASK_QUEUE.enqueue(
        interview_feedback_reminder_task, instance.id
    )).start()