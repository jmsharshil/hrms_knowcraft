import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_knowcraft.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from onboarding.models import JobApplication, SurveyResponse
from onboarding.views import BulkSurveyDataAPI, DownloadSurveyAPI
from django.utils import timezone
from django.contrib.auth import get_user_model

def run_test():
    User = get_user_model()
    # Use any existing staff user to bypass constraint issues
    user = User.objects.filter(is_staff=True).first()
    if not user:
        user = User.objects.first()
        
    app = JobApplication.objects.first()
    if not app:
        print("[ERROR] No JobApplication found.")
        return

    print(f"[INFO] Using candidate: {app.candidate_name}")

    sr, _ = SurveyResponse.objects.get_or_create(
        job_application=app,
        survey_type="30_day_candidate",
        defaults={
            "respondent_name": app.candidate_name,
            "respondent_email": "test@example.com",
            "submitted_at": timezone.now(),
            "responses": {
                "1": "strongly_agree",
                "2": "agree",
                "EXTRA_1": "This is a dynamic text response!",
                "999": "Another dynamic response"
            }
        }
    )
    sr.responses = {
        "1": "strongly_agree",
        "2": "agree",
        "EXTRA_1": "This is a dynamic text response!",
        "999": "Another dynamic response"
    }
    sr.save()

    factory = APIRequestFactory()

    print("\n--- Testing BulkSurveyDataAPI ---")
    req = factory.get('/api/onboarding/survey-data/bulk/')
    force_authenticate(req, user=user)
    resp = BulkSurveyDataAPI.as_view()(req)
    print("Bulk API Status:", resp.status_code)
    if resp.status_code == 200:
        ctype = resp.get('Content-Type')
        print("Bulk API Content-Type:", ctype)
        if 'spreadsheetml' in ctype or 'excel' in ctype:
            print("[OK] Excel file returned successfully!")
        else:
            print("[ERROR] Did not return Excel content type.")
    else:
        print("[ERROR] Failed:", resp.content)

    print("\n--- Testing DownloadSurveyAPI ---")
    req = factory.get(f'/api/onboarding/application/{app.id}/survey-download/?survey_type=30_day_candidate')
    force_authenticate(req, user=user)
    resp = DownloadSurveyAPI.as_view()(req, id=app.id)
    print("Download API Status:", resp.status_code)
    if resp.status_code == 200:
        ctype = resp.get('Content-Type')
        print("Download API Content-Type:", ctype)
        if 'application/pdf' in ctype:
            print("[OK] PDF returned successfully! Size:", len(resp.content), "bytes")
        else:
            print("[ERROR] Did not return PDF content type.")
    else:
        print("[ERROR] Failed:", resp.content)

if __name__ == "__main__":
    run_test()
