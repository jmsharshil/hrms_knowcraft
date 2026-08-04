import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_knowcraft.settings')
django.setup()

from jobs.models import JobApplication, Job
from onboarding.utils.onboarding_tasks import daily_onboarding_check
from django.utils import timezone
from datetime import timedelta

def test_daily_check():
    today = timezone.now().date()
    print(f"Testing daily_onboarding_check for today: {today}")
    
    # 1. Mock ManageEngineClient
    import onboarding.utils.onboarding_tasks as tasks
    class MockManageEngineClient:
        def update_ticket(self, ticket_id, update_payload, note=None):
            print(f"  [ManageEngine] update_ticket {ticket_id}: note={note}")
        def close_ticket(self, ticket_id):
            print(f"  [ManageEngine] close_ticket {ticket_id}")
            
    tasks.ManageEngineClient = MockManageEngineClient

    # 2. Mock notifications
    def mock_notify_internal(app, template, cc=None):
        print(f"  [Notify Internal] to HR for {app.candidate_name}: template={template}")
    def mock_notify_candidate(app, template, cc=None, feedback_link=None):
        print(f"  [Notify Candidate] to {app.candidate_name}: template={template}")
        
    tasks.notify_internal = mock_notify_internal
    tasks.notify_candidate = mock_notify_candidate

    # 3. Better mock: patch the queryset to avoid model creation issues with new required fields
    from unittest.mock import patch, MagicMock
    
    mock_apps = []
    for tc in [
        {"name": "DOJ_minus_15", "delta": 15, "status": "offer_accepted", "job_type": "work_from_office"},
        {"name": "DOJ_minus_7", "delta": 7, "status": "offer_accepted", "job_type": "work_from_office"},
        {"name": "DOJ_minus_2", "delta": 2, "status": "offer_accepted", "job_type": "work_from_office"},
        {"name": "DOJ_plus_7", "delta": -7, "status": "joined", "job_type": "work_from_office"},
        {"name": "DOJ_plus_30", "delta": -30, "status": "joined", "job_type": "work_from_office"},
        {"name": "DOJ_plus_45", "delta": -45, "status": "joined", "job_type": "work_from_office"},
        {"name": "DOJ_plus_90", "delta": -90, "status": "joined", "job_type": "work_from_office"},
    ]:
        app = MagicMock()
        app.candidate_name = tc["name"]
        app.candidate_email = f"{tc['name']}@example.com"
        app.candidate_phone = "1234567890"
        app.status = tc["status"]
        app.it_ticket_ref = f"TICKET_{tc['name']}"
        app.joining_date = today + timedelta(days=tc["delta"])
        app.created_at = timezone.now() - timedelta(days=30)  # for debug
        app.job = MagicMock()
        app.job.job_type = tc.get("job_type", "work_from_office")
        app.job.is_private = False
        app.is_satisfaction_survey_filled = False
        app.is_hod_survey_filled = False
        app.is_d45_call_scheduled = False
        app.is_d90_call_scheduled = False
        app.is_escalated = False
        mock_apps.append(app)

    with patch('onboarding.utils.onboarding_tasks.JobApplication.objects.filter') as mock_filter:
        mock_filter.return_value = mock_apps
        try:
            tasks.daily_onboarding_check()
            print("✅ daily_onboarding_check executed successfully with all mock triggers.")
        except Exception as e:
            print(f"❌ Error during check: {e}")
            
test_daily_check()
