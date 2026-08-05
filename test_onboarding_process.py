import os
import sys
import time
from datetime import timedelta
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms_knowcraft.settings")
django.setup()

from django.utils import timezone
from unittest.mock import patch
from jobs.models import JobApplication, Job
from mrf.models import MRF, Designation, Department
from onboarding.utils.onboarding_tasks import daily_onboarding_check

def test_full_onboarding():
    print("========================================")
    print("STARTING FULL ONBOARDING PROCESS TEST (-15 to +90 Days)")
    print("========================================")
    
    from django.conf import settings
    settings.ONBOARDING_DEBUG_MINUTES = True
    
    # 1. Create dependencies to satisfy validation
    from accounts.models import Company, User
    
    comp, _ = Company.objects.get_or_create(name="Test Company", defaults={"company_email": "testco@example.com"})
    usr, _ = User.objects.get_or_create(email="hr_tester@example.com", defaults={"company": comp, "role": "hr", "name": "HR Tester"})
    
    dept, _ = Department.objects.get_or_create(name="Engineering", company=comp)
    desig, _ = Designation.objects.get_or_create(name="Software Engineer", department=dept, company=comp)
    
    # Create a Department Head user for MRF requested_by
    hod, _ = User.objects.get_or_create(email="hod_tester@example.com", defaults={"company": comp, "role": "department_head", "name": "HOD Tester"})
    
    mrf, _ = MRF.objects.get_or_create(
        designation=desig, 
        department=dept, 
        company=comp, 
        requested_by=hod, 
        defaults={
            "mrf_name": "Test MRF", 
            "no_of_vacancies": 1, 
            "expected_date_of_joining": timezone.now().date(),
            "is_private": True,
            "position_department":dept,
        }
    )
    job, _ = Job.objects.get_or_create(mrf=mrf, job_title="Test Engineer", defaults={"assigned_to_internal_hr": usr})

    
    # 2. Create the Candidate
    candidate = JobApplication.objects.create(
        job=job,
        candidate_name="Test Onboarding Candidate",
        candidate_email="test_onboarding@example.com",
        status="offer_accepted",
        is_active=True,
        joining_date=timezone.now().date(),
        it_ticket_ref="MOCK-TICKET-12345" # Initialized so ME updates run
        # created_at is automatically set to now, which represents DOJ - 15 in debug mode
    )
    
    # Create a cleared BGV record to prevent DOJ+7 escalation from halting the workflow
    from bgv.models import CandidateBGV
    CandidateBGV.objects.create(
        candidate=candidate,
        status="clear"
    )
    
    print(f"Created candidate: {candidate.candidate_name} (ID: {candidate.id})")
    print(f"Base created_at: {candidate.created_at}")
    print("\nRunning simulated cron checks...\n")
    
    # 3. Simulate time progression
    # In debug mode:
    # minute 0: DOJ-15
    # minute 8: DOJ-7
    # minute 13: DOJ-2
    # minute 15: DOJ (0)
    # minute 22: DOJ+7
    # minute 45: DOJ+30
    # minute 60: DOJ+45
    # minute 105: DOJ+90
    
    key_minutes = [0, 8, 13, 15, 22, 45, 60, 105]
    
    base_time = candidate.created_at
    
    for minutes_passed in range(0, 106):
        # We physically shift time backwards to make it look like created_at is older
        # so when daily_onboarding_check calls timezone.now(), the difference is `minutes_passed`.
        # Alternatively, since we can't easily mock timezone.now() globally without a library,
        # we just change the created_at of the candidate.
        
        candidate.created_at = timezone.now() - timedelta(minutes=minutes_passed)
        candidate.save(update_fields=['created_at'])
        
        if minutes_passed in key_minutes:
            print(f"\n--- Minute {minutes_passed} (Simulated day {(minutes_passed - 15)}) ---")
            
            # For D45 and D90, we also need to fake scheduled calls if we want to bypass the scheduler check
            if minutes_passed == 60: # DOJ + 45
                print("Simulating HR scheduling the D45 Call...")
                # We do what the ScheduleD45CallAPI does
                from onboarding.models import OnboardingCall
                OnboardingCall.objects.create(
                    job_application=candidate,
                    call_type="d45",
                    organizer_email="hr_tester@example.com",
                    start_time=timezone.now(),
                    end_time=timezone.now() + timedelta(hours=1),
                    meeting_id="FAKE-MEETING-45",
                    meeting_link="http://fake-teams-link.com/d45"
                )
                candidate.is_d45_call_scheduled = True
                candidate.save(update_fields=['is_d45_call_scheduled'])
                
            if minutes_passed == 105: # DOJ + 90
                print("Simulating HR scheduling the D90 Call...")
                from onboarding.models import OnboardingCall
                OnboardingCall.objects.create(
                    job_application=candidate,
                    call_type="d90",
                    organizer_email="hr_tester@example.com",
                    start_time=timezone.now(),
                    end_time=timezone.now() + timedelta(hours=1),
                    meeting_id="FAKE-MEETING-90",
                    meeting_link="http://fake-teams-link.com/d90"
                )
                candidate.is_d90_call_scheduled = True
                candidate.save(update_fields=['is_d90_call_scheduled'])
                
            # Run the cron job manually with ManageEngineClient mocked
            try:
                with patch('onboarding.utils.onboarding_tasks.ManageEngineClient') as MockClient:
                    # Setup the mock so close_ticket returns True and create_ticket returns a fake ID
                    mock_instance = MockClient.return_value
                    mock_instance.create_ticket.return_value = {"request": {"id": "MOCK-TICKET-12345"}}
                    mock_instance.close_ticket.return_value = True
                    
                    daily_onboarding_check()
            except Exception as e:
                print(f"Error during cron execution: {e}")
            
            # Fetch fresh candidate data to see flag changes
            candidate.refresh_from_db()
            print(f"Flags State:")
            print(f"  - Emp Account Active: {candidate.emp_account_active}")
            print(f"  - IT Ticket Ref: {candidate.it_ticket_ref}")
            print(f"  - D45 Call Scheduled: {candidate.is_d45_call_scheduled}")
            print(f"  - D90 Call Scheduled: {candidate.is_d90_call_scheduled}")
            print(f"  - D90 Survey Sent: {candidate.is_d90_survey_sent}")
            print(f"  - D90 Survey Filled: {candidate.is_d90_survey_filled}")
            
            # check onboarding models
            from onboarding.models import SurveyResponse, OnboardingCall
            surveys = SurveyResponse.objects.filter(job_application=candidate)
            print(f"  - Surveys created: {[s.survey_type for s in surveys]}")
            calls = OnboardingCall.objects.filter(job_application=candidate)
            print(f"  - Calls scheduled: {[c.call_type for c in calls]}")
            
            time.sleep(1) # Small pause for readability
            
    print("\n========================================")
    print("TEST COMPLETE")
    print("========================================")
    print("You can clean up this candidate from the DB if needed.")

if __name__ == "__main__":
    test_full_onboarding()
