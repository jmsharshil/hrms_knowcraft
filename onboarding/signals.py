from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ApprovalNote
from jobs.models import JobApplication


@receiver(post_save, sender=JobApplication)
def update_approval_note_status(sender, instance, created, **kwargs):
    if created:
        return  # skip on create

    ApprovalNote.objects.filter(
        candidate=instance
    ).update(status=instance.status)
