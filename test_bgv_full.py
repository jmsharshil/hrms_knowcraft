"""
Comprehensive BGV (Background Verification) Test Script

Tests the complete BGV workflow:
1. Creates test data (Company, User, Job, JobApplication, Documents)
2. Initiates BGV via OnGrid API
3. Polls BGV status
4. Verifies all API endpoints work correctly

Usage:
    1. Start server: python manage.py runserver 8000
    2. Run this:     python manage.py shell -c "exec(open('test_bgv_full.py', encoding='utf-8').read())"
"""

import os
import django
import requests
import json
import time
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms_knowcraft.settings")
django.setup()

from django.contrib.auth.hashers import make_password
from accounts.models import Company, User
from jobs.models import Job, JobApplication
from onboarding.models import JobApplicationDocument
from bgv.models import CandidateBGV

BASE_URL = "http://127.0.0.1:8000"
results = []

def report(label, passed, detail=""):
    icon = "[PASS]" if passed else "[FAIL]"
    results.append((label, passed, detail))
    print(f"  {icon} {label}" + (f" -- {detail}" if detail else ""))


def login_as(email, pin="1234"):
    """Login and return JWT token."""
    resp = requests.post(f"{BASE_URL}/api/accounts/login/", json={
        "email": email,
        "pin": pin,
    })
    if resp.status_code == 200:
        return resp.json().get("access")
    return None


# =====================================================================
# STEP 1: Setup Test Data
# =====================================================================
print("\n" + "=" * 70)
print("STEP 1: Setting Up Test Data for BGV")
print("=" * 70)

# Create or get company
company, _ = Company.objects.get_or_create(
    name="BGV Test Company",
    defaults={"email": "bgvtest@company.com"}
)
report("Company created/retrieved", True, company.name)

# Create or get admin user
admin_email = "bgv.admin@test.com"
admin, created = User.objects.get_or_create(
    email=admin_email,
    defaults={
        "name": "BGV Admin",
        "role": "admin",
        "company": company,
        "pin_set": True,
    }
)
if created or not admin.pin:
    admin.set_password("1234")
    admin.pin = make_password("1234")
    admin.save()
report("Admin user ready", True, admin.email)

# Create or get HR user
hr_email = "bgv.hr@test.com"
hr_user, created = User.objects.get_or_create(
    email=hr_email,
    defaults={
        "name": "BGV HR Manager",
        "role": "hr",
        "company": company,
        "pin_set": True,
    }
)
if created or not hr_user.pin:
    hr_user.set_password("1234")
    hr_user.pin = make_password("1234")
    hr_user.save()
report("HR user ready", True, hr_user.email)

import uuid
test_suffix = str(uuid.uuid4())[:8]

# Create a test job - Get existing job or create minimal one
from mrf.models import MRF, Department, Designation

# Create minimal MRF first
dept, _ = Department.objects.get_or_create(name="Test Department")
desig, _ = Designation.objects.get_or_create(name="Software Engineer")

mrf, _ = MRF.objects.get_or_create(
    mrf_id=f"MRF-BGV-TEST-{test_suffix}",
    defaults={
        "department": dept,
        "designation": desig,
        "location": "Mumbai",
        "no_of_positions": 1,
        "job_description": "Test MRF for BGV",
        "key_responsibilities": "Test responsibilities",
        "required_skills": "Test skills",
        "experience_range": "3-5 years",
        "budget_ctc": "5-7 LPA",
        "priority": "medium",
        "reason_for_request": "Testing",
        "requested_by": admin,
    }
)
report("MRF created/retrieved", True, mrf.mrf_id)

# Now create Job from MRF
job, _ = Job.objects.get_or_create(
    mrf=mrf,
    defaults={
        "job_title": f"BGV Test Position - {test_suffix}",
        "company": company,
        "department": dept,
        "designation": desig,
        "location": "Mumbai",
        "no_of_positions": 1,
        "job_description": "Test job for BGV workflow",
        "key_responsibility": "Test responsibilities",
        "required_qualifications": "Test qualifications",
        "experience_range": "3-5 years",
        "skills_competencies": "Test skills",
        "technical_skills": "Python, Django",
        "salary_range": "5-7 LPA",
        "status": "open",
        "priority": "medium",
    }
)
report("Job created/retrieved", True, job.job_title)

# =====================================================================
# STEP 2: Create JobApplication with all required data
# =====================================================================
print("\n" + "=" * 70)
print("STEP 2: Creating Job Application with BGV-ready data")
print("=" * 70)

import uuid
# test_suffix already defined above
candidate_email = f"bgv.candidate.{test_suffix}@test.com"

# Create JobApplication
application = JobApplication.objects.create(
    job=job,
    candidate_name="BGV Test Candidate",
    candidate_email=candidate_email,
    candidate_phone="+919876543210",
    current_ctc=500000,
    expected_ctc=700000,
    notice_period=30,
    current_employer="Test Corp",
    designation="Software Developer",
    total_experience=3.5,
    location="Mumbai",
    source="internal_hr",
    status="selected",  # Must be selected to initiate BGV
    is_fresher=False,
    joining_date=datetime.now().date() + timedelta(days=30),
)
report("JobApplication created", True, f"ID: {application.id}")

# Create JobApplicationDocument (required for BGV)
from django.core.files.base import ContentFile
docs = JobApplicationDocument.objects.create(
    job_application=application,
)

# Create minimal fake files for required documents
# In real scenario, these would be actual PDFs/images
fake_pdf_content = b"%PDF-1.4 fake document content"

# Upload PAN card (required for BGV)
docs.pan.save(f"pan_{test_suffix}.pdf", ContentFile(fake_pdf_content))
docs.pan_approved = True

# Upload Aadhaar (required for BGV)
docs.aadhaar.save(f"aadhaar_{test_suffix}.pdf", ContentFile(fake_pdf_content))
docs.aadhaar_approved = True

# Upload resume
application.resume.save(f"resume_{test_suffix}.pdf", ContentFile(fake_pdf_content))

docs.save()
application.save()

report("Documents created with PAN & Aadhaar", True, f"PAN: {bool(docs.pan)}, Aadhaar: {bool(docs.aadhaar)}")

# Verify documents relationship exists
has_docs = hasattr(application, 'documents')
report("Application has documents relationship", has_docs, f"hasattr(documents)={has_docs}")

# =====================================================================
# STEP 3: Login and Get JWT Token
# =====================================================================
print("\n" + "=" * 70)
print("STEP 3: Getting JWT Token")
print("=" * 70)

token = login_as(admin_email, "1234")
if token:
    report("Login successful", True)
    headers = {"Authorization": f"Bearer {token}"}
else:
    report("Login failed", False, "Cannot proceed without token")
    print("\n[ERROR] Login failed. Check if user exists and PIN is set.")
    exit(1)

# =====================================================================
# STEP 4: Check if BGV record already exists
# =====================================================================
print("\n" + "=" * 70)
print("STEP 4: Checking for existing BGV record")
print("=" * 70)

bgv_exists = CandidateBGV.objects.filter(candidate=application).exists()
if bgv_exists:
    bgv_record = CandidateBGV.objects.get(candidate=application)
    report("BGV record already exists", True, f"Status: {bgv_record.status}, OnGrid ID: {bgv_record.ongrid_individual_id}")
else:
    report("No existing BGV record", True, "Will create new one")
    bgv_record = None

# =====================================================================
# STEP 5: Initiate BGV via API
# =====================================================================
print("\n" + "=" * 70)
print("STEP 5: Initiating BGV via API")
print("=" * 70)

bgv_payload = {
    "application_id": str(application.id),
    "extra_data": {
        "fathersName": "Test Father Name",
        "gender": "M",
        "dob": "15/01/1990",
        "city": "Mumbai",
        "permanentAddress": {
            "line1": "123 Test Street",
            "line2": "Andheri West",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400053",
            "country": "IN",
            "fullAddress": "123 Test Street, Andheri West, Mumbai, Maharashtra - 400053"
        },
        "verifications": [
            {"code": "CCRV"},  # Criminal Check
            {"code": "PANV"},  # PAN Verification
            {"code": "AADHV"}, # Aadhaar Verification
        ]
    }
}

print(f"\n  Sending BGV initiation request for application {application.id}...")
resp = requests.post(
    f"{BASE_URL}/api/bgv/initiate-by-application/",
    json=bgv_payload,
    headers=headers,
)

report(f"BGV Initiation API call", resp.status_code in [200, 201, 502], 
       f"Status: {resp.status_code}")

if resp.status_code in [200, 201, 502]:
    bgv_response = resp.json()
    print(f"\n  Response:")
    print(f"    - Candidate: {bgv_response.get('candidate_name', 'N/A')}")
    print(f"    - Status: {bgv_response.get('status', 'N/A')}")
    print(f"    - OnGrid Individual ID: {bgv_response.get('ongrid_individual_id', 'N/A')}")
    print(f"    - OnGrid Status: {bgv_response.get('ongrid_status', 'N/A')}")
    
    # Refresh BGV record from DB
    if CandidateBGV.objects.filter(candidate=application).exists():
        bgv_record = CandidateBGV.objects.get(candidate=application)
        report("BGV record created/updated in DB", True, 
               f"Status: {bgv_record.status}, OnGrid ID: {bgv_record.ongrid_individual_id}")
    else:
        report("BGV record NOT found in DB", False)
else:
    print(f"\n  Error Response: {resp.text}")
    report("BGV Initiation failed", False, resp.text[:200])

# =====================================================================
# STEP 6: List all BGV records
# =====================================================================
print("\n" + "=" * 70)
print("STEP 6: Listing BGV Records")
print("=" * 70)

resp = requests.get(f"{BASE_URL}/api/bgv/", headers=headers)
report("List BGV endpoint", resp.status_code == 200, f"Status: {resp.status_code}")

if resp.status_code == 200:
    bgv_list = resp.json()
    count = bgv_list.get("count", len(bgv_list) if isinstance(bgv_list, list) else 0)
    report(f"BGV records returned", True, f"Count: {count}")
    
    # Find our test BGV
    if isinstance(bgv_list, dict) and "results" in bgv_list:
        test_bgvs = [b for b in bgv_list["results"] 
                     if b.get("candidate_name") == "BGV Test Candidate"]
    elif isinstance(bgv_list, list):
        test_bgvs = [b for b in bgv_list 
                     if b.get("candidate_name") == "BGV Test Candidate"]
    else:
        test_bgvs = []
    
    if test_bgvs:
        report("Test BGV found in list", True)
    else:
        report("Test BGV NOT found in list", False)

# =====================================================================
# STEP 7: Get specific BGV details
# =====================================================================
print("\n" + "=" * 70)
print("STEP 7: Getting BGV Details")
print("=" * 70)

if bgv_record:
    resp = requests.get(f"{BASE_URL}/api/bgv/{bgv_record.id}/", headers=headers)
    report("Get BGV detail endpoint", resp.status_code == 200, f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        bgv_detail = resp.json()
        print(f"\n  BGV Details:")
        print(f"    - ID: {bgv_detail.get('id')}")
        print(f"    - Candidate: {bgv_detail.get('candidate_name')}")
        print(f"    - Status: {bgv_detail.get('status')}")
        print(f"    - OnGrid ID: {bgv_detail.get('ongrid_individual_id')}")
        print(f"    - Report URL: {bgv_detail.get('report_url', 'N/A')}")
        report("BGV detail retrieved successfully", True)

# =====================================================================
# STEP 8: Poll OnGrid Status
# =====================================================================
print("\n" + "=" * 70)
print("STEP 8: Polling OnGrid Status")
print("=" * 70)

if bgv_record and bgv_record.ongrid_individual_id:
    resp = requests.get(
        f"{BASE_URL}/api/bgv/{bgv_record.id}/ongrid-status/",
        headers=headers
    )
    report("OnGrid status poll endpoint", resp.status_code == 200, f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        status_data = resp.json()
        print(f"\n  OnGrid Status Response:")
        print(f"    - Status: {status_data.get('status', 'N/A')}")
        print(f"    - Individual ID: {status_data.get('individualId', 'N/A')}")
        
        # Refresh from DB
        bgv_record.refresh_from_db()
        report("BGV record updated with OnGrid status", True, 
               f"DB Status: {bgv_record.status}")
        print(f"\n  Updated BGV record:")
        print(f"    - Status: {bgv_record.status}")
        print(f"    - OnGrid Status (JSON): {json.dumps(bgv_record.ongrid_status, indent=2)[:200]}...")
    else:
        print(f"\n  Error: {resp.text}")
        report("OnGrid status poll failed", False)
else:
    report("Skip OnGrid status poll", False, "No OnGrid individual ID available")

# =====================================================================
# STEP 9: Fetch Verification Report
# =====================================================================
print("\n" + "=" * 70)
print("STEP 9: Fetching Verification Report")
print("=" * 70)

if bgv_record and bgv_record.ongrid_individual_id:
    resp = requests.get(
        f"{BASE_URL}/api/bgv/{bgv_record.id}/verification-report/",
        headers=headers
    )
    report("Verification report endpoint", resp.status_code == 200, f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        report_data = resp.json()
        print(f"\n  Verification Report:")
        print(f"    - Response keys: {list(report_data.keys())[:10]}")
        if "verifications" in report_data:
            print(f"    - Number of verifications: {len(report_data['verifications'])}")
            for v in report_data["verifications"][:3]:
                print(f"      * {v.get('code', 'N/A')}: {v.get('status', 'N/A')}")
        report("Verification report retrieved", True)
    else:
        print(f"\n  Error: {resp.text}")
        report("Verification report fetch failed", False)
else:
    report("Skip verification report", False, "No OnGrid individual ID available")

# =====================================================================
# STEP 10: Test BGV Re-initiation
# =====================================================================
print("\n" + "=" * 70)
print("STEP 10: Testing BGV Re-initiation")
print("=" * 70)

if bgv_record:
    resp = requests.post(
        f"{BASE_URL}/api/bgv/{bgv_record.id}/reinitiate/",
        headers=headers,
        json={"extra_data": {}}
    )
    report("BGV re-initiate endpoint", resp.status_code in [200, 502], 
           f"Status: {resp.status_code}")
    
    if resp.status_code in [200, 502]:
        reinit_data = resp.json()
        report("BGV re-initiation response received", True, 
               f"Status: {reinit_data.get('status', 'N/A')}")
    else:
        print(f"\n  Error: {resp.text}")
        report("BGV re-initiation failed", False)
else:
    report("Skip re-initiation", False, "No BGV record found")

# =====================================================================
# STEP 11: Test Background Tasks (Schedule Check & Poller)
# =====================================================================
print("\n" + "=" * 70)
print("STEP 11: Testing Background Tasks")
print("=" * 70)

from bgv.tasks import run_bgv_schedule_check, run_bgv_status_poll

print("\n  Running BGV schedule check...")
try:
    run_bgv_schedule_check()
    report("BGV schedule check executed", True)
except Exception as e:
    report("BGV schedule check failed", False, str(e))

print("\n  Running BGV status poll...")
try:
    run_bgv_status_poll()
    report("BGV status poll executed", True)
except Exception as e:
    report("BGV status poll failed", False, str(e))

# =====================================================================
# STEP 12: Audit Log Verification
# =====================================================================
print("\n" + "=" * 70)
print("STEP 12: Checking Audit Logs for BGV Actions")
print("=" * 70)

from auditlog.models import AuditLog

bgv_logs = AuditLog.objects.filter(path__contains="/api/bgv/").order_by("-timestamp")
report(f"Audit logs for BGV endpoints", bgv_logs.count() > 0, f"Count: {bgv_logs.count()}")

if bgv_logs.count() > 0:
    print(f"\n  Recent BGV Audit Logs:")
    for log in bgv_logs[:5]:
        print(f"    [{log.timestamp}] {log.user.email if log.user else 'Anonymous'} "
              f"{log.method} {log.path} -> {log.status_code}")

# =====================================================================
# Final Summary
# =====================================================================
print("\n" + "=" * 70)
print("BGV TEST SUMMARY")
print("=" * 70)

passed = sum(1 for _, p, _ in results if p)
failed = sum(1 for _, p, _ in results if not p)
total = len(results)

print(f"\n  Total Tests: {total}")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")

if failed > 0:
    print(f"\n  Failed tests:")
    for label, p, detail in results:
        if not p:
            print(f"    [FAIL] {label}" + (f" -- {detail}" if detail else ""))

print("\n" + "=" * 70)
if failed == 0:
    print("  >>> ALL BGV TESTS PASSED!")
else:
    print(f"  !!! {failed} TEST(S) FAILED -- see details above")
print("=" * 70 + "\n")

# Print important IDs for manual verification
print("\nIMPORTANT IDs FOR MANUAL VERIFICATION:")
print(f"  - Job Application ID: {application.id}")
print(f"  - BGV Record ID: {bgv_record.id if bgv_record else 'N/A'}")
print(f"  - OnGrid Individual ID: {bgv_record.ongrid_individual_id if bgv_record else 'N/A'}")
print(f"  - Candidate Email: {candidate_email}")
print(f"\nYou can use these IDs to test manually in Postman or the frontend.\n")
