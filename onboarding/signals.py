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
from django.utils import timezone

@receiver(pre_save, sender=JobApplication)
def store_old_job(sender, instance, **kwargs):
    """
    Store old job before saving to detect changes.
    """
    if not instance.pk:
        instance._old_job_id = None
        instance._old_status = None
        instance._old_joining_date = None
        instance._old_crafter_id = None
        instance._old_team_manager_name = None
        instance._old_team_manager_email = None
        return

    try:
        old_instance = JobApplication.objects.get(pk=instance.pk)
        instance._old_job_id = old_instance.job_id
        instance._old_status = old_instance.status
        instance._old_joining_date = old_instance.joining_date
        instance._old_crafter_id = old_instance.crafter_id
        instance._old_team_manager_name = getattr(old_instance, "team_manager_name", None)
        instance._old_team_manager_email = getattr(old_instance, "team_manager_email", None)
    except JobApplication.DoesNotExist:
        instance._old_job_id = None
        instance._old_status = None
        instance._old_joining_date = None
        instance._old_crafter_id = None
        instance._old_team_manager_name = None
        instance._old_team_manager_email = None

@receiver(post_save, sender=JobApplication)
def update_approval_note_status(sender, instance, created, **kwargs):
    if created:
        return  # skip on create

    if instance.status == 'approved':
        ApprovalNote.objects.filter(
            candidate=instance
        ).update(status=instance.status,approved_at=timezone.now())
    elif instance.status == 'approval_rejected':
        ApprovalNote.objects.filter(
            candidate=instance
        ).update(status=instance.status,rejected_at=timezone.now())
    else:
        ApprovalNote.objects.filter(
            candidate=instance
        ).update(status=instance.status)

    # New: Bidirectional sync for fields
    approval_notes = instance.approval_notes.all()

    # New: Sync job changes to approval note and shift interview rounds if applicable
    old_job_id = getattr(instance, '_old_job_id', None)
    if old_job_id and old_job_id != instance.job_id:
        if approval_notes.exists():
            approval_note = approval_notes.first()
            payload = approval_note.payload or {}
            changed = False

            # Sync job-related fields
            if instance.job and instance.job.department:
                new_dept = instance.job.department.name
                if payload.get('department') != new_dept:
                    payload['department'] = new_dept
                    changed = True

            if instance.job and instance.job.designation:
                new_desig = instance.job.designation.name
                if payload.get('designation') != new_desig:
                    payload['designation'] = new_desig
                    changed = True

            if instance.job and instance.job.mrf:
                new_mrf = instance.job.mrf.mrf_name
                if payload.get('mrf') != new_mrf:
                    payload['mrf'] = new_mrf
                    changed = True

            if instance.job and instance.job.location:
                new_loc = instance.job.location
                if payload.get('office_location') != new_loc:
                    payload['office_location'] = new_loc
                    changed = True

            # Optionally sync other fields like hiring_type if derivable from job
            # e.g., if hasattr(instance.job, 'hiring_type') ...

            if changed:
                approval_note.payload = payload
                approval_note.updated_at = timezone.now()
                approval_note.save(update_fields=['payload', 'updated_at'])

        # Shift interview round / update slot links if candidate is in interview pipeline
        if instance.status in [
            "shortlisted",
            "interview_next_2",
            "interview_next_3",
            "interview_next_final",
            "interview_next_management_client",
        ]:
            update_candidate_slot_link(instance)

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
    if not document.annexure_uploaded_at:
        document.annexure_uploaded_at = timezone.now()
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

# from .utils.docusign import process_offer_letter_docusign
# from .models import DocuSignOffer
# #docusign
# @receiver(post_save, sender=JobApplicationDocument)
# def auto_send_offer_to_docusign(sender, instance, created, **kwargs):
#     """
#     Auto send offer letter via DocuSign when file is added.
#     """

#     new_file = instance.created_offer_letter
#     old_file = getattr(instance, "_old_file", None)

#     # ❌ No file → do nothing
#     if not new_file:
#         return

#     application = instance.job_application

#     # ❌ Prevent duplicate sending (UPDATED)
#     if DocuSignOffer.objects.filter(job_application=application).exists():
#         return

#     # 🚀 Trigger function
#     def trigger_docusign():
#         process_offer_letter_docusign(instance)

#     # Case 1: Object created with file
#     if created and new_file:
#         transaction.on_commit(trigger_docusign)
#         return

#     # Case 2: File added later
#     if not old_file and new_file:
#         transaction.on_commit(trigger_docusign)

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
    if getattr(candidate, '_in_slot_link_update', False):
        return

    mrf = getattr(getattr(candidate, 'job', None), 'mrf', None)
    if not mrf:
        return

    interviewer_email = None
    status = candidate.status

    hr_email = mrf.interviewer_email_1 or (mrf.hr_interviewer.email if getattr(mrf, 'hr_interviewer', None) else None)
    tech_email = mrf.interviewer_email_2 or (mrf.technical_interviewers.first().email if mrf.technical_interviewers.exists() else None)
    case_email = mrf.interviewer_email_3 or (mrf.case_study_interviewer.email if getattr(mrf, 'case_study_interviewer', None) else None)
    final_email = mrf.interviewer_email_final or (mrf.final_interviewer.email if getattr(mrf, 'final_interviewer', None) else None)
    mgmt_email = mrf.interviewer_email_management_client or (mrf.management_client_interviewer.email if getattr(mrf, 'management_client_interviewer', None) else None)

    if status == 'shortlisted':
        if hr_email:
            interviewer_email = hr_email
            candidate.round_name = "hr_round"
        elif tech_email:
            interviewer_email = tech_email
            candidate.round_name = "technical_round"
        elif case_email:
            interviewer_email = case_email
            candidate.round_name = "case_study_round"
        elif final_email:
            interviewer_email = final_email
            candidate.round_name = "final_round"
        elif mgmt_email:
            interviewer_email = mgmt_email
            candidate.round_name = "management_client_round"
    elif status == "interview_next_2":
        interviewer_email = tech_email
        candidate.round_name = "technical_round"
    elif status == "interview_next_3":
        interviewer_email = case_email
        candidate.round_name = "case_study_round"
    elif status == "interview_next_final":
        interviewer_email = final_email
        candidate.round_name = "final_round"
    elif status == "interview_next_management_client":
        interviewer_email = mgmt_email
        candidate.round_name = "management_client_round"

    interviewer = None
    if interviewer_email:
        name = interviewer_email.split("@")[0].replace(".", " ").title()
        interviewer, _ = Interviewer.objects.get_or_create(
            email=interviewer_email,
            defaults={"name": name}
        )

    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net')
    if interviewer:
        candidate.slot_link = (
            f"{frontend_url}/api/slots/available/"
            f"?candidate_id={candidate.id}&interviewer_id={interviewer.id}"
        )
        candidate.inperson_link = (
            f"{frontend_url}/api/inperson/interview/"
            f"?candidate_id={candidate.id}&interviewer_id={interviewer.id}"
        )
    else:
        candidate.slot_link = ""
        candidate.inperson_link = ""

    candidate._in_slot_link_update = True
    candidate.save(update_fields=["slot_link", "inperson_link", "round_name"])
    candidate._in_slot_link_update = False


@receiver(post_save, sender=JobApplication)
def handle_job_application_advanced_logic(sender, instance, created, **kwargs):
    """
    Handles crafter_id syncing to OnboardingForm and reverting to joining_pending
    if the joining_date is moved to a future date while status is 'joined'.
    """
    if created:
        return
    
    old_status = getattr(instance, '_old_status', None)
    old_joining_date = getattr(instance, '_old_joining_date', None)
    old_crafter_id = getattr(instance, '_old_crafter_id', None)

    # 1. Auto-sync crafter_id to OnboardingForm
    if old_crafter_id != instance.crafter_id:
        try:
            if hasattr(instance, 'onboarding_form') and instance.onboarding_form:
                from onboarding.models import OnboardingForm
                OnboardingForm.objects.filter(pk=instance.onboarding_form.pk).update(crafter_id=instance.crafter_id)
        except Exception:
            pass

    # 2. Revert joining_pending logic
    from datetime import date
    if old_status == 'joined' and old_joining_date != instance.joining_date and (instance.joining_date is None or instance.joining_date > date.today()):
        if instance.status == 'joined':
            job = instance.job
            if job:
                other_joined = job.applications.filter(status='joined').exclude(pk=instance.pk).count()
                job.positions_filled = other_joined
                if job.positions_filled < job.no_of_positions:
                    job.status = 'joining_pending'
                job.save(update_fields=['positions_filled', 'status'])
                
                if hasattr(job, 'mrf') and job.mrf:
                    try:
                        if job.mrf.status == 'filled' and job.positions_filled < job.no_of_positions:
                            job.mrf.status = 'joining_pending'
                            job.mrf.save(update_fields=['status'])
                    except Exception:
                        pass
            
            # Revert candidate status
            JobApplication.objects.filter(pk=instance.pk).update(status='joining_pending', updated_at=timezone.now())
            ApprovalNote.objects.filter(candidate=instance.pk).update(status='joining_pending', updated_at=timezone.now())


from onboarding.models import OnboardingForm

@receiver(pre_save, sender=OnboardingForm)
def store_old_onboarding_form(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_crafter_id = None
        instance._old_team_manager = None
        return
    
    try:
        old_instance = OnboardingForm.objects.get(pk=instance.pk)
        instance._old_crafter_id = old_instance.crafter_id
        instance._old_team_manager = old_instance.team_manager
    except OnboardingForm.DoesNotExist:
        instance._old_crafter_id = None
        instance._old_team_manager = None

@receiver(post_save, sender=OnboardingForm)
def sync_onboarding_form_crafter_id(sender, instance, created, **kwargs):
    """
    Auto-sync crafter_id back to JobApplication if changed from OnboardingForm
    """
    old_crafter_id = getattr(instance, '_old_crafter_id', None)
    
    if old_crafter_id != instance.crafter_id and instance.job_application_id:
        JobApplication.objects.filter(pk=instance.job_application_id).update(crafter_id=instance.crafter_id)

@receiver(post_save, sender=OnboardingForm)
def sync_onboarding_form_team_manager(sender, instance, created, **kwargs):
    """
    Auto-sync team_manager back to JobApplication if changed from OnboardingForm
    """
    old_tm = getattr(instance, '_old_team_manager', None)
    if instance.job_application_id:
        from onboarding.views import sync_team_manager
        app = JobApplication.objects.filter(pk=instance.job_application_id).first()
        if not app:
            return
        if instance.team_manager and (created or old_tm != instance.team_manager):
            sync_team_manager(app, team_manager_raw=instance.team_manager)
        elif not instance.team_manager and (app.team_manager_email or app.team_manager_name):
            val = app.team_manager_email or app.team_manager_name
            OnboardingForm.objects.filter(pk=instance.pk).update(team_manager=val)
            instance.team_manager = val

@receiver(post_save, sender=JobApplication)
def sync_job_application_team_manager(sender, instance, created, **kwargs):
    """
    Auto-sync team_manager_name/email to OnboardingForm.team_manager
    """
    old_name = getattr(instance, '_old_team_manager_name', None)
    old_email = getattr(instance, '_old_team_manager_email', None)
    if (created or old_name != instance.team_manager_name or old_email != instance.team_manager_email):
        val = instance.team_manager_email or instance.team_manager_name
        if val:
            OnboardingForm.objects.filter(job_application=instance).exclude(team_manager=val).update(team_manager=val)


