import os
import django
import sys
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms_knowcraft.settings")
django.setup()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("onboarding.utils.onboarding_tasks")
logger.setLevel(logging.INFO)

notif_logger = logging.getLogger("onboarding.utils.notifications")
notif_logger.setLevel(logging.INFO)

from onboarding.models import JobApplication
from jobs.models import Job
from mrf.models import MRF
from onboarding.utils.onboarding_tasks import run_onboarding_check_for_candidate
from django.utils import timezone
from datetime import timedelta
import uuid

def run_test():
    # Create a completely fresh job application with DOJ = today
    print("Creating fresh test application...")
    
    # We need a job and MRF for some fields to work
    mrf = MRF.objects.first()
    if not mrf:
        print("No MRF found to link.")
        return
        
    job = Job.objects.filter(mrf=mrf).first()
    
    today = timezone.now().date()
    
    app = JobApplication.objects.create(
        job=job,
        candidate_name=f"Fresh Test Candidate {uuid.uuid4().hex[:6]}",
        candidate_email="fresh_test@example.com",
        status="joined", # To simulate they should be onboarding
        joining_date=today,
        # No work_email provided
    )
    
    print(f"\nFresh Candidate created: {app.candidate_name}")
    print(f"Work email: {getattr(app, 'work_email', None)}")
    print(f"Joining date: {app.joining_date} (DOJ is today)")
    print(f"is_doj_0_triggered: {getattr(app, 'is_doj_0_triggered', False)}")
    
    # Run the onboarding check
    print("\n>>> FIRST RUN: Without work email")
    run_onboarding_check_for_candidate(app)
    
    # Check if flags were set (they shouldn't be)
    app.refresh_from_db()
    print(f"\nAfter first run:")
    print(f"is_doj_0_triggered: {app.is_doj_0_triggered}")
    print(f"is_esign_packet_generated: {app.is_esign_packet_generated}")
    
    # Simulating HR adding the email
    print("\n>>> Simulating HR adding work email...")
    app.work_email = "fresh_test@knowcraft.in"
    app.save()
    
    print("\n>>> SECOND RUN: With work email")
    run_onboarding_check_for_candidate(app)
    
    # Check if flags were set now
    app.refresh_from_db()
    print(f"\nAfter second run:")
    print(f"is_doj_0_triggered: {app.is_doj_0_triggered}")
    print(f"is_esign_packet_generated: {app.is_esign_packet_generated}")
    
    print("\nDone! Cleaning up...")
    app.delete()
    job.delete()

if __name__ == "__main__":
    run_test()
