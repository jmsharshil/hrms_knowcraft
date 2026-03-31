# from django.db.models.signals import post_save, pre_save
# from django.dispatch import receiver
# from django.core.mail import send_mail
# from django.conf import settings
# from .models import MRFRequest, MRFStatusHistory


# @receiver(pre_save, sender=MRFRequest)
# def auto_fill_position_department(sender, instance, **kwargs):
#     """
#     Auto-fill position_department from department if not set
#     """
#     if not instance.position_department_id and instance.department_id:
#         instance.position_department = instance.department


# @receiver(post_save, sender=MRFRequest)
# def send_status_notification(sender, instance, created, **kwargs):
#     """
#     Send email notifications on status changes
#     Note: Configure email settings in settings.py for this to work
#     """
#     if created:
#         return  # Don't send email on creation
    
#     # Check if status changed
#     if hasattr(instance, '_status_changed'):
#         status = instance.status
        
#         # Prepare notification based on status
#         subject = None
#         message = None
#         recipients = []
        
#         if status == 'submitted':
#             subject = f'New MRF Submitted - {instance.designation}'
#             message = f'''
# A new MRF has been submitted and requires your approval.

# MRF Details:
# - Designation: {instance.designation}
# - Department: {instance.department.name}
# - Requested by: {instance.requested_by.get_full_name()}
# - Number of Vacancies: {instance.no_of_vacancies}

# Please review and approve/reject this request.
#             '''
#             # Send to HR Managers
#             from django.contrib.auth import get_user_model
#             User = get_user_model()
#             hr_managers = User.objects.filter(role='hr_manager')
#             recipients = [u.email for u in hr_managers if u.email]
        
#         elif status == 'l1_approved':
#             subject = f'MRF L1 Approved - {instance.designation}'
#             message = f'''
# An MRF has been approved at Level 1 and requires your Level 2 approval.

# MRF Details:
# - Designation: {instance.designation}
# - Department: {instance.department.name}
# - Requested by: {instance.requested_by.get_full_name()}
# - L1 Approved by: {instance.l1_approver.get_full_name()}

# Please review and approve/reject this request.
#             '''
#             # Send to Admins and HR Managers for L2 approval
#             from django.contrib.auth import get_user_model
#             User = get_user_model()
#             approvers = User.objects.filter(role__in=['admin', 'hr_manager'])
#             recipients = [u.email for u in approvers if u.email]
        
#         elif status == 'l2_approved':
#             subject = f'MRF Approved - Job Created: {instance.designation}'
#             message = f'''
# Congratulations! Your MRF has been fully approved.

# MRF Details:
# - Requisition No: {instance.requisition_no}
# - Designation: {instance.designation}
# - Department: {instance.department.name}
# - Number of Vacancies: {instance.no_of_vacancies}
# - Date Received: {instance.date_received}

# The job posting can now be created.
#             '''
#             # Send to requester
#             if instance.requested_by.email:
#                 recipients = [instance.requested_by.email]
        
#         elif status == 'rejected':
#             rejection_reason = instance.l2_rejection_reason or instance.l1_rejection_reason
#             rejected_by = 'Level 2' if instance.l2_rejection_reason else 'Level 1'
            
#             subject = f'MRF Rejected - {instance.designation}'
#             message = f'''
# Your MRF has been rejected at {rejected_by}.

# MRF Details:
# - Designation: {instance.designation}
# - Department: {instance.department.name}
# - Rejection Reason: {rejection_reason}

# You can revise and resubmit this MRF.
#             '''
#             # Send to requester
#             if instance.requested_by.email:
#                 recipients = [instance.requested_by.email]
        
#         # Send email if configured
#         if subject and message and recipients:
#             try:
#                 send_mail(
#                     subject=subject,
#                     message=message,
#                     from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@company.com'),
#                     recipient_list=recipients,
#                     fail_silently=True,
#                 )
#             except Exception as e:
#                 # Log error but don't fail the request
#                 print(f"Error sending email: {e}")


# @receiver(post_save, sender=MRFRequest)
# def log_status_change(sender, instance, created, **kwargs):
#     """
#     Log significant field changes for audit purposes
#     """
#     if created:
#         return
    
#     # This is just a placeholder for additional logging
#     # You can extend this to log specific field changes
#     pass

from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import MRF
from onboarding.utils.task_queue import TASK_QUEUE
from onboarding.utils.mrf_send_reminder import mrf_approval_reminder_task
from django.utils import timezone

@receiver(post_save, sender=MRF)
def schedule_mrf_reminder(sender, instance, created, **kwargs):
    # Only enqueue if new MRF
    if created:
        print("reminder started!")
        TASK_QUEUE.enqueue(mrf_approval_reminder_task, instance.id)

@receiver(pre_save, sender=MRF)
def store_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = MRF.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except MRF.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

@receiver(post_save, sender=MRF)
def sync_mrf_to_job_status(sender, instance, created, **kwargs):
    """
    Signal to sync MRF status changes to related Job.
    - When MRF goes to 'on_hold': Set Job to 'on_hold' and save previous status.
    - When MRF resumes from 'on_hold': Restore Job's previous status.
    """
    if created:
        # New MRF - no sync needed yet (Job created separately)
        return
    
    previous_status = getattr(instance, '_previous_status', None)

    # Only sync if status changed
    if instance.status == previous_status:
        return

    job = getattr(instance, 'job', None)
    if not job:
        return
    
    if instance.status == 'on_hold' and previous_status != 'on_hold':
        if job.status != 'on_hold':
            job.previous_status = job.status
            job.held_at = timezone.now()
            job.hold_reason = instance.hold_reason
            job.status = 'on_hold'
            job.save(update_fields=['previous_status', 'held_at', 'hold_reason', 'status'])

    elif previous_status == 'on_hold' and instance.status != 'on_hold':
        if job.status == 'on_hold':
            restore_status = job.previous_status or 'open'
            job.status = restore_status
            job.previous_status = None
            job.held_at = None
            job.hold_reason = ''
            job.save(update_fields=['status', 'previous_status', 'held_at', 'hold_reason'])