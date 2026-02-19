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
    if instance.end and instance.end >= timezone.now():
        TASK_QUEUE.enqueue(interview_feedback_reminder_task, instance.id)
