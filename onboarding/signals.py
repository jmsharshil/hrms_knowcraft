from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import ApprovalNote
from jobs.models import JobApplication
from onboarding.models import JobApplicationDocument,OfferDocument
from .utils.zoho_sign import process_offer_letter
from django.db import transaction

@receiver(post_save, sender=JobApplication)
def update_approval_note_status(sender, instance, created, **kwargs):
    if created:
        return  # skip on create

    ApprovalNote.objects.filter(
        candidate=instance
    ).update(status=instance.status)

@receiver(pre_save, sender=JobApplicationDocument)
def store_old_file(sender, instance, **kwargs):
    """
    Store old file value before saving.
    """
    if not instance.pk:
        instance._old_file = None
        return

    try:
        old_instance = JobApplicationDocument.objects.get(pk=instance.pk)
        instance._old_file = old_instance.created_offer_letter
    except JobApplicationDocument.DoesNotExist:
        instance._old_file = None


@receiver(post_save, sender=JobApplicationDocument)
def auto_send_offer_to_zoho(sender, instance, created, **kwargs):
    """
    Trigger Zoho only when file is newly added.
    """

    new_file = instance.created_offer_letter
    old_file = getattr(instance, "_old_file", None)

    # No file at all
    if not new_file:
        return

    # Prevent duplicate sending
    if OfferDocument.objects.filter(
        application=instance.job_application
    ).exists():
        print("duplicate....................")
        return

    # Case 1: Object just created with file
    if created and new_file:
        transaction.on_commit(lambda: process_offer_letter(instance))
        return

    # Case 2: File added later
    if not old_file and new_file:
        transaction.on_commit(lambda: process_offer_letter(instance))
        print("sucess...............")
