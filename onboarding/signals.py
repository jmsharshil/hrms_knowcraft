from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import ApprovalNote
from jobs.models import JobApplication
from onboarding.models import JobApplicationDocument,OfferDocument
from .utils.zoho_sign import process_offer_letter
from django.db import transaction
from mrf.models import MRF
from slots.models import Interviewer
from django.conf import settings

@receiver(post_save, sender=JobApplication)
def update_approval_note_status(sender, instance, created, **kwargs):
    if created:
        return  # skip on create

    ApprovalNote.objects.filter(
        candidate=instance
    ).update(status=instance.status)

@receiver(pre_save, sender=JobApplicationDocument)
def store_old_annexure(sender, instance, **kwargs):
    """
    Store old salary_annexure before saving, to detect new upload.
    """
    if not instance.pk:
        instance._old_annexure = None
        return

    try:
        old_instance = JobApplicationDocument.objects.get(pk=instance.pk)
        instance._old_annexure = old_instance.salary_annexure
    except JobApplicationDocument.DoesNotExist:
        instance._old_annexure = None

@receiver(post_save, sender=JobApplicationDocument)
def auto_stage_on_annexure(sender, instance, created, **kwargs):
    """
    Trigger stage change when salary_annexure is newly uploaded.
    """

    new_file = instance.salary_annexure
    old_file = getattr(instance, "_old_annexure", None)

    # No file uploaded → do nothing
    if not new_file:
        return

    # Prevent duplicate triggers
    # if instance.job_application.salary_annexure_uploaded:
    #     return

    # Case 1: Object just created with file
    if created and new_file:
        transaction.on_commit(lambda: change_stage_for_annexure(instance))
        return

    # Case 2: File added later
    if not old_file and new_file:
        transaction.on_commit(lambda: change_stage_for_annexure(instance))

def change_stage_for_annexure(document):
    """
    Custom logic to change the JobApplication stage once annexure is uploaded.
    """
    app = document.job_application
    # Example: move from docs_pending → docs_approved
    from .utils.engine import automation_engine
    ok,reason = automation_engine(app,app.status,'salary_annexure_review')
    document.joining_docs_status = 'pending'
    document.save()
    if not ok:
        print(reason)

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
        return

    # Case 1: Object just created with file
    if created and new_file:
        transaction.on_commit(lambda: process_offer_letter(instance))
        return

    # Case 2: File added later
    if not old_file and new_file:
        transaction.on_commit(lambda: process_offer_letter(instance))

@receiver(post_save, sender=MRF)
def update_slot_links_when_interviewer_assigned(sender, instance, **kwargs):
    """
    When interviewer fields are updated in MRF,
    update slot links for all candidates in interview stages.
    """
    candidates = JobApplication.objects.filter(
        job__mrf=instance,
        status__in=[
            "shortlisted",
            "interview_next_2",
            "interview_next_3",
            "interview_next_final",
            "interview_next_management_client",
        ],
    )
    for candidate in candidates:
        update_candidate_slot_link(candidate)

def update_candidate_slot_link(candidate):
    interviewer_email = None

    status = candidate.status

    if status == 'shortlisted':
        if candidate.job.mrf.interviewer_email_1:
            interviewer_email = candidate.job.mrf.interviewer_email_1
            candidate.round_name = "hr_round"
        elif candidate.job.mrf.interviewer_email_2:
            interviewer_email = candidate.job.mrf.interviewer_email_2
            candidate.round_name = "technical_round"
        elif candidate.job.mrf.interviewer_email_3:
            interviewer_email = candidate.job.mrf.interviewer_email_3
            candidate.round_name = "case_study_round"
        elif candidate.job.mrf.interviewer_email_final:
            interviewer_email = candidate.job.mrf.interviewer_email_final
            candidate.round_name = "final_round"
    elif status == "interview_next_2":
        interviewer_email = candidate.job.mrf.interviewer_email_2
    elif status == "interview_next_3":
        interviewer_email = candidate.job.mrf.interviewer_email_3
    elif status == "interview_next_final":
        interviewer_email = candidate.job.mrf.interviewer_email_final
    elif status == "interview_next_management_client":
        interviewer_email = candidate.job.mrf.interviewer_email_management_client

    interviewer = None
    if interviewer_email:
        interviewer = Interviewer.objects.filter(email=interviewer_email).first()

    if interviewer:
        candidate.slot_link = (
            f"{settings.FRONTEND_URL}/api/slots/available/"
            f"?candidate_id={candidate.id}&interviewer_id={interviewer.id}"
        )
        candidate.inperson_link = (
            f"{settings.FRONTEND_URL}/api/inperson/interview/"
            f"?candidate_id={candidate.id}&interviewer_id={interviewer.id}"
        )
    else:
        candidate.slot_link = ""
        candidate.inperson_link = ""

    candidate.save(update_fields=["slot_link","inperson_link","round_name"])