import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms_knowcraft.settings")
django.setup()

from django.conf import settings
# Ensure testserver or localhost is allowed
if "*" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("*")

from jobs.models import JobApplication
from onboarding.models import OnboardingForm
from accounts.models import User
from rest_framework.test import APIClient

def run_tests():
    print("=" * 60)
    print("STARTING ONBOARDING INITIATION API TEST")
    print("=" * 60)

    # 1. Fetch or get a test user for authentication
    user = User.objects.filter(role="admin").first() or User.objects.first()
    if not user:
        print("ERROR: No user found in database to authenticate test requests.")
        return
    print(f"Authenticated Test User: {user.email} (Role: {getattr(user, 'role', 'N/A')})")

    # Initialize DRF APIClient
    client = APIClient()
    client.force_authenticate(user=user)

    # 2. Fetch a valid JobApplication
    application = JobApplication.objects.first()
    if not application:
        print("ERROR: No JobApplication found in database.")
        return
    
    app_id = str(application.id)
    print(f"Testing with Application ID: {app_id} (Candidate: {application.candidate_name})")

    url = f"/api/application/{app_id}/initiate-onboarding/"
    print(f"Target URL: {url}")

    # 3. Define full payload matching OnboardingForm fields
    payload = {
        "assets": "MacBook Pro M3, 27-inch Monitor, Ergonomic Mouse",
        "site": "Mumbai Tech Hub",
        "subject": f"Onboarding Initiation - {application.candidate_name}",
        "first_name": "TestFirst",
        "last_name": "TestLast",
        "personal_email_id": "test.candidate.onboarding@example.com",
        "contact_number": "+919876543210",
        "joining_date": "2026-09-15",
        "designation": "Senior Full Stack Engineer",
        "department": "Engineering & Technology",
        "employee_category": "Full Time Regular",
        "center_office_location": "Mumbai - BKC Tower B",
        "mode_for_collecting_assets": "Courier to Home",
        "team_manager": "tech.lead@knowcraft.com",
        "work_from": "Hybrid",
        "crafter_id": "KC-2026-8899",
        "emails_to_notify": "it-support@knowcraft.com, hr-team@knowcraft.com",
        "current_address": "402, High Tech Residency, BKC Road, Mumbai",
        "description": "Standard onboarding hardware and software provisioning request.",
        "custom_notes": "Requires admin access to AWS staging and Docker setup.",
        "requester_email_id": user.email,
        "requester_name": getattr(user, "name", "HR Admin"),
        "requester_id": str(user.id),
    }

    print("\n--- TEST CASE 1: Valid Post Request ---")
    response = client.post(url, payload, format="json", HTTP_HOST="localhost")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Data: {response.data}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "onboarding_form_id" in response.data, "Response missing 'onboarding_form_id'"

    form_id = response.data["onboarding_form_id"]
    print(f"[OK] Created OnboardingForm ID: {form_id}")

    # 4. Verify DB Persistence
    saved_form = OnboardingForm.objects.filter(id=form_id).first()
    assert saved_form is not None, "Saved form not found in DB!"
    print(f"\n[OK] DB Persistence Verified:")
    print(f"   - Job Application Link ID: {saved_form.job_application_id}")
    print(f"   - Submitted By User: {saved_form.submitted_by}")
    print(f"   - Subject: {saved_form.subject}")
    print(f"   - Designation: {saved_form.designation}")
    print(f"   - Department: {saved_form.department}")
    print(f"   - Personal Email: {saved_form.personal_email_id}")
    print(f"   - Contact Number: {saved_form.contact_number}")
    print(f"   - Joining Date: {saved_form.joining_date}")
    print(f"   - Office Location: {saved_form.center_office_location}")
    print(f"   - Work From: {saved_form.work_from}")
    print(f"   - Team Manager: {saved_form.team_manager}")
    print(f"   - Custom Notes: {saved_form.custom_notes}")

    # 5. TEST CASE 2: Non-existent application ID (404 test)
    fake_id = "00000000-0000-0000-0000-000000000000"
    fake_url = f"/api/application/{fake_id}/initiate-onboarding/"
    print("\n--- TEST CASE 2: Non-existent Application ID (404) ---")
    res_404 = client.post(fake_url, payload, format="json", HTTP_HOST="localhost")
    print(f"Response Status Code: {res_404.status_code}")
    print(f"Response Data: {res_404.data}")
    assert res_404.status_code == 404, f"Expected 404, got {res_404.status_code}"
    print("[OK] 404 Handled correctly.")

    # 6. TEST CASE 3: Unauthenticated user test (401)
    print("\n--- TEST CASE 3: Unauthenticated Request (401/403) ---")
    unauth_client = APIClient()
    res_401 = unauth_client.post(url, payload, format="json", HTTP_HOST="localhost")
    print(f"Response Status Code: {res_401.status_code}")
    print(f"Response Data: {res_401.data}")
    assert res_401.status_code in [401, 403], f"Expected 401/403, got {res_401.status_code}"
    print("[OK] 401/403 Handled correctly.")

    print("\n" + "=" * 60)
    print("ALL API TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
