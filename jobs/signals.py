"""
Signal to automatically create Job when MRF is approved
Add this to your MRF app's signals.py file
"""

from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from mrf.models import MRF

@receiver(post_save, sender=MRF)
def create_job_on_mrf_approval(sender, instance, created, **kwargs):
    """
    Automatically create a Job when MRF status changes to 'approved'
    """
    # Only proceed if MRF is approved
    if instance.status != 'approved':
        return
    
    # Check if job already exists for this MRF
    if hasattr(instance, 'job'):
        return
    
    # Import here to avoid circular imports
    from jobs.models import Job
    
    # Create job from MRF
    try:
        job = Job.objects.create(
            mrf=instance,
            job_title=instance.mrf_name,
            department=instance.department,
            designation=instance.designation,
            location=instance.location,
            job_type=instance.job_type,
            no_of_positions=instance.no_of_vacancies,
            key_responsibility=instance.key_responsibility,
            required_qualifications=instance.required_qualifications,
            experience_range=instance.experience_range,
            skills_competencies=instance.skills_competencies,
            salary_range=instance.salary_range,
            priority=instance.priority or 'medium',  # Default priority
            expected_closure_date=instance.expected_date_of_joining,
            posted_by=instance.requested_by,
            company=instance.requested_by.company if hasattr(instance.requested_by, 'company') else None,
            status='open',
            is_active=True,
            visible_to_consultancy=False  # Not visible to consultancy by default
        )
        
        print(f"Job created automatically for MRF: {instance.requisition_no}")
        
    except Exception as e:
        print(f"Error creating job for MRF {instance.requisition_no}: {str(e)}")

from .models import Job

@receiver(pre_save, sender=Job)
def store_previous_job_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Job.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Job.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

@receiver(post_save, sender=Job)
def sync_job_status_to_links(sender, instance, created, **kwargs):
    if created:
        return

    previous_status = getattr(instance, '_previous_status', None)

    # Only sync if status changed
    if instance.status == previous_status:
        return

    links = instance.application_links.all()
    if not links.exists():
        return

    if instance.status == 'on_hold' and previous_status != 'on_hold':
        updated_count = links.update(is_active=False)
        print(f"Deactivated {updated_count} links for on-hold Job {instance.id}")

    elif previous_status == 'on_hold' and instance.status != 'on_hold':
        updated_count = links.update(is_active=True)
        print(f"Reactivated {updated_count} links for resumed Job {instance.id}")