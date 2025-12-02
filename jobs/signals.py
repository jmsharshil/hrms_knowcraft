"""
Signal to automatically create Job when MRF is approved
Add this to your MRF app's signals.py file
"""

from django.db.models.signals import post_save
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
            no_of_positions=instance.no_of_vacancies,
            key_responsibility=instance.key_responsibility,
            required_qualifications=instance.required_qualifications,
            experience_range=instance.experience_range,
            skills_competencies=instance.skills_competencies,
            salary_range=instance.salary_range,
            priority='medium',  # Default priority
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


# Add this to your MRF app's apps.py
"""
from django.apps import AppConfig

class MrfsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mrfs'
    
    def ready(self):
        import mrfs.signals  # Import signals when app is ready
"""