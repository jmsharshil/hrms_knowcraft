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

    # 3. Create mock applications with varying dates
    try:
        job = Job.objects.filter(job_type="work_from_office").first()
        if not job:
            job = Job.objects.create(title="Test Job", job_type="work_from_office")
    except Exception:
        job = Job.objects.first()

    test_cases = [
        {"name": "DOJ_minus_15", "delta": 15, "status": "offer_accepted"},
        {"name": "DOJ_minus_7", "delta": 7, "status": "offer_accepted"},
        {"name": "DOJ_minus_2", "delta": 2, "status": "offer_accepted"},
        {"name": "DOJ_plus_7", "delta": -7, "status": "offer_accepted"}, # BGV check
        {"name": "DOJ_plus_30", "delta": -30, "status": "joined"},
        {"name": "DOJ_plus_45", "delta": -45, "status": "joined"},
        {"name": "DOJ_plus_90", "delta": -90, "status": "joined"},
    ]

    apps_created = []
    for tc in test_cases:
        joining_date = today + timedelta(days=tc["delta"])
        app = JobApplication.objects.create(
            candidate_name=tc["name"],
            candidate_email=f"{tc['name']}@example.com",
            candidate_phone="1234567890",
            job=job,
            status=tc["status"],
            joining_date=joining_date,
            it_ticket_ref=f"TICKET_{tc['name']}"
        )
        apps_created.append(app)

    try:
        tasks.daily_onboarding_check()
    finally:
        # Cleanup
        for app in apps_created:
            app.delete()
            
test_daily_check()
