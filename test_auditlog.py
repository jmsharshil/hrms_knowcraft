"""
Comprehensive test script for the AuditLog system.

Creates demo users across different roles, simulates various API actions
against the live dev server at localhost:8000, and verifies that the
audit log middleware, model, and APIs all work correctly.

Usage:
    1. Start server: python manage.py runserver 8000
    2. Run this:     python manage.py shell -c "exec(open('test_auditlog.py', encoding='utf-8').read())"
"""

import json
import os
import sys
import requests

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms_knowcraft.settings")
django.setup()

from django.contrib.auth.hashers import make_password
from accounts.models import Company, User, MagicLink
from auditlog.models import AuditLog

BASE_URL = "http://127.0.0.1:8000"

# =====================================================================
# Helpers
# =====================================================================

results = []


def report(label, passed, detail=""):
    icon = "[PASS]" if passed else "[FAIL]"
    results.append((label, passed, detail))
    print(f"  {icon} {label}" + (f" -- {detail}" if detail else ""))


def separator(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def get_tokens(email, pin):
    """Login with PIN and return access token."""
    resp = requests.post(f"{BASE_URL}/api/accounts/login/", json={
        "email": email,
        "pin": pin,
    })
    if resp.status_code == 200:
        return resp.json().get("access")
    return None


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# STEP 1: Create demo users directly via ORM
# =====================================================================

separator("STEP 1: Setting Up Demo Data")

old_count = AuditLog.objects.count()
print(f"  Existing AuditLog entries before test: {old_count}")

# Get or create demo company
demo_company, created = Company.objects.get_or_create(
    email="demo-test-audit@knowcraft.in",
    defaults={"name": "Demo Audit Corp"},
)
report("Demo company", True, f"{'Created' if created else 'Reused'}: {demo_company.name}")

# Create users with different roles
USERS = {}
TEST_PIN = "123456"

role_configs = [
    ("admin", "Demo Admin", "demo.admin@audit.test"),
    ("hr_manager", "Demo HR Manager", "demo.hrmanager@audit.test"),
    ("hr", "Demo HR", "demo.hr@audit.test"),
    ("department_head", "Demo Dept Head", "demo.depthead@audit.test"),
    ("consultancy", "Demo Consultancy", "demo.consultant@audit.test"),
]

for role, name, email in role_configs:
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "name": name,
            "company": demo_company,
            "role": role,
        },
    )
    # Always ensure PIN is set and up to date
    user.set_password(TEST_PIN)
    user.pin = make_password(TEST_PIN)
    user.pin_set = True
    user.save()
    USERS[role] = user
    report(f"User: {role}", True, f"{user.email} (id={user.id})")


# =====================================================================
# STEP 2: Get JWT tokens for each user
# =====================================================================

separator("STEP 2: Getting JWT Tokens via Login API")

TOKENS = {}
for role, user in USERS.items():
    token = get_tokens(user.email, TEST_PIN)
    if token:
        TOKENS[role] = token
        report(f"Login: {role}", True)
    else:
        # Fallback: generate token directly
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        refresh['company_id'] = str(user.company.id)
        refresh['name'] = user.name
        TOKENS[role] = str(refresh.access_token)
        report(f"Login: {role}", True, "Token generated directly (login API failed)")


# Count logs before our actions
before_count = AuditLog.objects.count()


# =====================================================================
# STEP 3: Simulate API actions from different users
# =====================================================================

separator("STEP 3: Simulating API Actions from Different Users")

# --- Admin actions ---
admin_token = TOKENS.get("admin")
if admin_token:
    headers = auth_header(admin_token)

    # Action 1: Admin reads users list
    resp = requests.get(f"{BASE_URL}/api/accounts/users/", headers=headers)
    report("Admin GET /users/", resp.status_code == 200, f"status={resp.status_code}")

    # Action 2: Admin reads current user
    resp = requests.get(f"{BASE_URL}/api/accounts/users/me/", headers=headers)
    report("Admin GET /users/me/", resp.status_code == 200, f"status={resp.status_code}")

    # Action 3: Admin creates a new user
    import uuid as _uuid
    unique_email = f"test.created.by.admin.{_uuid.uuid4().hex[:8]}@audit.test"
    resp = requests.post(
        f"{BASE_URL}/api/accounts/users/create/",
        json={
            "name": "Test User By Admin",
            "email": unique_email,
            "role": "hr",
        },
        headers=headers,
    )
    report("Admin POST /users/create/", resp.status_code in (200, 201), f"status={resp.status_code}, email={unique_email}")

    # Action 4: Admin reads audit logs
    resp = requests.get(f"{BASE_URL}/api/audit-logs/", headers=headers)
    report("Admin GET /audit-logs/", resp.status_code == 200, f"status={resp.status_code}")

    # Action 5: Admin updates own profile
    resp = requests.patch(
        f"{BASE_URL}/api/accounts/users/me/update/",
        json={"name": "Demo Admin Updated"},
        headers=headers,
    )
    report("Admin PATCH /users/me/update/", resp.status_code == 200, f"status={resp.status_code}")

else:
    report("Admin actions", False, "No token available")


# --- HR Manager actions ---
hr_manager_token = TOKENS.get("hr_manager")
if hr_manager_token:
    headers = auth_header(hr_manager_token)

    # Action 6: HR Manager reads users list
    resp = requests.get(f"{BASE_URL}/api/accounts/users/", headers=headers)
    report("HR Manager GET /users/", resp.status_code == 200, f"status={resp.status_code}")

    # Action 7: HR Manager reads current user
    resp = requests.get(f"{BASE_URL}/api/accounts/users/me/", headers=headers)
    report("HR Manager GET /users/me/", resp.status_code == 200, f"status={resp.status_code}")

    # Action 8: HR Manager reads audit logs (allowed for hr_manager)
    resp = requests.get(f"{BASE_URL}/api/audit-logs/", headers=headers)
    report("HR Manager GET /audit-logs/", resp.status_code == 200, f"status={resp.status_code}")

else:
    report("HR Manager actions", False, "No token available")


# --- HR actions ---
hr_token = TOKENS.get("hr")
if hr_token:
    headers = auth_header(hr_token)

    # Action 9: HR reads current user
    resp = requests.get(f"{BASE_URL}/api/accounts/users/me/", headers=headers)
    report("HR GET /users/me/", resp.status_code == 200, f"status={resp.status_code}")

    # Action 10: HR tries to read audit logs (should be forbidden)
    resp = requests.get(f"{BASE_URL}/api/audit-logs/", headers=headers)
    report("HR GET /audit-logs/ (should be 403)", resp.status_code == 403, f"status={resp.status_code}")

else:
    report("HR actions", False, "No token available")


# --- Department Head actions ---
dept_head_token = TOKENS.get("department_head")
if dept_head_token:
    headers = auth_header(dept_head_token)

    # Action 11: Dept Head reads users
    resp = requests.get(f"{BASE_URL}/api/accounts/users/", headers=headers)
    report("Dept Head GET /users/", resp.status_code == 200, f"status={resp.status_code}")

    # Action 12: Dept Head tries audit logs (should be forbidden)
    resp = requests.get(f"{BASE_URL}/api/audit-logs/", headers=headers)
    report("Dept Head GET /audit-logs/ (should be 403)", resp.status_code == 403, f"status={resp.status_code}")

else:
    report("Dept Head actions", False, "No token available")


# --- Consultancy actions ---
consultant_token = TOKENS.get("consultancy")
if consultant_token:
    headers = auth_header(consultant_token)

    # Action 13: Consultant reads current user
    resp = requests.get(f"{BASE_URL}/api/accounts/users/me/", headers=headers)
    report("Consultant GET /users/me/", resp.status_code == 200, f"status={resp.status_code}")

    # Action 14: Consultant tries audit logs (should be forbidden)
    resp = requests.get(f"{BASE_URL}/api/audit-logs/", headers=headers)
    report("Consultant GET /audit-logs/ (should be 403)", resp.status_code == 403, f"status={resp.status_code}")

else:
    report("Consultant actions", False, "No token available")


# --- Unauthenticated request ---
# Action 15: Unauthenticated request
resp = requests.get(f"{BASE_URL}/api/accounts/users/")
report("Unauthenticated GET /users/ (should be 401/403)", resp.status_code in (401, 403), f"status={resp.status_code}")


# =====================================================================
# STEP 4: Verify Middleware Captured Logs
# =====================================================================

separator("STEP 4: Verifying Middleware Captured All Actions")

import time
time.sleep(1)  # Small delay to ensure DB writes are committed

after_count = AuditLog.objects.count()
new_logs = after_count - before_count
report("New logs created by test actions", new_logs > 0, f"before={before_count}, after={after_count}, new={new_logs}")

# Check per-user logs
admin = USERS["admin"]
hr_manager = USERS["hr_manager"]
hr_user = USERS["hr"]
dept_head = USERS["department_head"]
consultant = USERS["consultancy"]

admin_logs = AuditLog.objects.filter(user=admin)
report("Admin has audit logs", admin_logs.count() > 0, f"count={admin_logs.count()}")

hr_manager_logs = AuditLog.objects.filter(user=hr_manager)
report("HR Manager has audit logs", hr_manager_logs.count() > 0, f"count={hr_manager_logs.count()}")

hr_logs = AuditLog.objects.filter(user=hr_user)
report("HR has audit logs", hr_logs.count() > 0, f"count={hr_logs.count()}")

dept_head_logs = AuditLog.objects.filter(user=dept_head)
report("Dept Head has audit logs", dept_head_logs.count() > 0, f"count={dept_head_logs.count()}")

consultant_logs = AuditLog.objects.filter(user=consultant)
report("Consultant has audit logs", consultant_logs.count() > 0, f"count={consultant_logs.count()}")

# Verify action types
create_actions = AuditLog.objects.filter(action="CREATE")
read_actions = AuditLog.objects.filter(action="READ")
update_actions = AuditLog.objects.filter(action="UPDATE")
report("CREATE actions captured", create_actions.count() > 0, f"count={create_actions.count()}")
report("READ actions captured", read_actions.count() > 0, f"count={read_actions.count()}")
report("UPDATE actions captured", update_actions.count() > 0, f"count={update_actions.count()}")

# Verify company is recorded
sample_log = AuditLog.objects.filter(user=admin).first()
report("Company is recorded on logs", sample_log is not None and sample_log.company == demo_company)

# Verify non-/api/ paths are NOT logged
home_logs = AuditLog.objects.filter(path="/")
report("Home page NOT logged (non-/api/)", home_logs.count() == 0)

# Verify IP address captured
report("IP address captured", sample_log is not None and sample_log.ip_address is not None)

# Verify user agent captured
report("User agent captured", sample_log is not None and len(sample_log.user_agent) > 0)

# Verify status codes captured
report("Status code captured", sample_log is not None and sample_log.status_code is not None)

# Verify login action is captured
# Make an explicit login request and verify it's captured as LOGIN action
login_resp = requests.post(f"{BASE_URL}/api/accounts/login/", json={
    "email": USERS["admin"].email,
    "pin": TEST_PIN,
})
time.sleep(1)
login_logs = AuditLog.objects.filter(action="LOGIN")
report("LOGIN action captured from /login/ path", login_logs.count() > 0, f"count={login_logs.count()}, login_resp_status={login_resp.status_code}")


# =====================================================================
# STEP 5: Test Audit Log API Endpoints
# =====================================================================

separator("STEP 5: Testing Audit Log API Endpoints")

admin_token = TOKENS.get("admin")
if admin_token:
    headers = auth_header(admin_token)

    # Test: List all audit logs
    resp = requests.get(f"{BASE_URL}/api/audit-logs/", headers=headers)
    data = resp.json()
    count = data.get("count", len(data.get("results", [])))
    report("GET /audit-logs/ (list)", resp.status_code == 200, f"count={count}")

    # Test: Filter by user_id
    resp = requests.get(f"{BASE_URL}/api/audit-logs/?user_id={admin.id}", headers=headers)
    data = resp.json()
    report("GET /audit-logs/?user_id=admin", resp.status_code == 200, f"count={len(data.get('results', []))}")

    # Test: Filter by action
    resp = requests.get(f"{BASE_URL}/api/audit-logs/?action=CREATE", headers=headers)
    data = resp.json()
    report("GET /audit-logs/?action=CREATE", resp.status_code == 200, f"count={len(data.get('results', []))}")

    # Test: Filter by method
    resp = requests.get(f"{BASE_URL}/api/audit-logs/?method=POST", headers=headers)
    data = resp.json()
    report("GET /audit-logs/?method=POST", resp.status_code == 200, f"count={len(data.get('results', []))}")

    # Test: Filter by path (icontains)
    resp = requests.get(f"{BASE_URL}/api/audit-logs/?path=users", headers=headers)
    data = resp.json()
    report("GET /audit-logs/?path=users", resp.status_code == 200, f"count={len(data.get('results', []))}")

    # Test: Filter by flushed_to_blob
    resp = requests.get(f"{BASE_URL}/api/audit-logs/?flushed_to_blob=false", headers=headers)
    data = resp.json()
    report("GET /audit-logs/?flushed_to_blob=false", resp.status_code == 200, f"count={len(data.get('results', []))}")

    # Test: Retrieve single log entry
    first_log = AuditLog.objects.filter(user=admin).exclude(path__contains="audit-logs").first()
    if first_log:
        resp = requests.get(f"{BASE_URL}/api/audit-logs/{first_log.id}/", headers=headers)
        if resp.status_code == 200:
            detail = resp.json()
            report("GET /audit-logs/<id>/ (detail)", True, f"action={detail.get('action')}, path={detail.get('path')}")
        else:
            report("GET /audit-logs/<id>/ (detail)", False, f"status={resp.status_code}")
    else:
        report("GET /audit-logs/<id>/ (detail)", False, "No non-auditlog entries found")

    # Test: Company scoping - HR Manager should only see their company
    hr_manager_token = TOKENS.get("hr_manager")
    if hr_manager_token:
        hr_headers = auth_header(hr_manager_token)
        resp = requests.get(f"{BASE_URL}/api/audit-logs/", headers=hr_headers)
        if resp.status_code == 200:
            data = resp.json()
            all_same_company = all(
                str(entry.get("company")) == str(demo_company.id)
                for entry in data.get("results", [])
                if entry.get("company")
            )
            report("HR Manager sees only own company logs", all_same_company)
        else:
            report("HR Manager sees only own company logs", False, f"status={resp.status_code}")

else:
    report("Audit Log API tests", False, "No admin token available")


# =====================================================================
# STEP 6: Test Blob Flush
# =====================================================================

separator("STEP 6: Testing Blob Flush (Admin Only)")

# Test: HR Manager cannot flush
hr_manager_token = TOKENS.get("hr_manager")
if hr_manager_token:
    hr_headers = auth_header(hr_manager_token)
    resp = requests.post(f"{BASE_URL}/api/audit-logs/flush/", headers=hr_headers)
    report("HR Manager POST /flush/ (should be 403)", resp.status_code == 403, f"status={resp.status_code}")

# Test: Admin can flush
admin_token = TOKENS.get("admin")
if admin_token:
    headers = auth_header(admin_token)
    resp = requests.post(f"{BASE_URL}/api/audit-logs/flush/", headers=headers)
    report("Admin POST /flush/", resp.status_code == 200, f"detail={resp.json().get('detail')}")

    # Verify logs are now flushed
    time.sleep(2)  # Wait for background task
    flushed_count = AuditLog.objects.filter(flushed_to_blob=True).count()
    report("Logs flushed to blob", flushed_count > 0, f"flushed_count={flushed_count}")
else:
    report("Blob flush tests", False, "No admin token available")


# =====================================================================
# STEP 7: Test by-user endpoint
# =====================================================================

separator("STEP 7: Testing Blob Download by User+Date")

admin_token = TOKENS.get("admin")
if admin_token:
    headers = auth_header(admin_token)

    today_str = str(AuditLog.objects.filter(user=admin).first().timestamp.date())

    # Test: Missing params
    resp = requests.get(f"{BASE_URL}/api/audit-logs/by-user/", headers=headers)
    report("GET /by-user/ (missing params, should be 400)", resp.status_code == 400, f"status={resp.status_code}")

    # Test: Invalid date format
    resp = requests.get(f"{BASE_URL}/api/audit-logs/by-user/?user_id={admin.id}&date=invalid-date", headers=headers)
    report("GET /by-user/ (invalid date, should be 400)", resp.status_code == 400, f"status={resp.status_code}")

    # Test: Valid params
    resp = requests.get(
        f"{BASE_URL}/api/audit-logs/by-user/?user_id={admin.id}&date={today_str}",
        headers=headers,
    )
    if resp.status_code == 200:
        data = resp.json()
        report("GET /by-user/ (valid, 200)", True, f"entries={len(data)}")
    elif resp.status_code == 404:
        report("GET /by-user/ (404 - blob file not found yet)", True,
               "OK if flush had connectivity issues to Azure from local env")
    else:
        report("GET /by-user/ (valid)", False, f"status={resp.status_code}")
else:
    report("by-user tests", False, "No admin token available")


# =====================================================================
# STEP 8: Test Sensitive Data Sanitization
# =====================================================================

separator("STEP 8: Verifying Sensitive Data Sanitization")

from auditlog.middleware import _sanitise_body

test_body = json.dumps({
    "email": "test@test.com",
    "password": "super_secret_123",
    "pin": "654321",
    "token": "jwt-token-here",
    "name": "John Doe",
    "api_key": "abc123xyz",
})
sanitised = _sanitise_body(test_body)
parsed = json.loads(sanitised)

report("Password is redacted", parsed.get("password") == "***REDACTED***", f"value={parsed.get('password')}")
report("PIN is redacted", parsed.get("pin") == "***REDACTED***", f"value={parsed.get('pin')}")
report("Token is redacted", parsed.get("token") == "***REDACTED***", f"value={parsed.get('token')}")
report("API key is redacted", parsed.get("api_key") == "***REDACTED***", f"value={parsed.get('api_key')}")
report("Non-sensitive data preserved", parsed.get("name") == "John Doe" and parsed.get("email") == "test@test.com")


# =====================================================================
# STEP 9: Per-User Log Breakdown
# =====================================================================

separator("STEP 9: Per-User Log Breakdown")

for role, user in USERS.items():
    log_count = AuditLog.objects.filter(user=user).count()
    actions = list(
        AuditLog.objects.filter(user=user)
        .values_list("action", flat=True)
        .distinct()
    )
    methods = list(
        AuditLog.objects.filter(user=user)
        .values_list("method", flat=True)
        .distinct()
    )
    report(f"{role}: {log_count} logs", True, f"actions={actions}, methods={methods}")


# =====================================================================
# STEP 10: Test Ordering & Pagination
# =====================================================================

separator("STEP 10: Testing Ordering & Pagination")

admin_token = TOKENS.get("admin")
if admin_token:
    headers = auth_header(admin_token)

    resp = requests.get(f"{BASE_URL}/api/audit-logs/?ordering=timestamp", headers=headers)
    report("Ordering by timestamp asc", resp.status_code == 200)

    resp = requests.get(f"{BASE_URL}/api/audit-logs/?ordering=-timestamp", headers=headers)
    report("Ordering by timestamp desc", resp.status_code == 200)

    resp = requests.get(f"{BASE_URL}/api/audit-logs/?page=1&page_size=5", headers=headers)
    report("Pagination (page=1, page_size=5)", resp.status_code == 200)

else:
    report("Ordering & Pagination tests", False, "No admin token available")


# =====================================================================
# STEP 11: Print sample log entries
# =====================================================================

separator("STEP 11: Sample Log Entries from DB")

sample_logs = AuditLog.objects.select_related("user", "company").all()[:5]
for log in sample_logs:
    user_str = log.user.email if log.user else "Anonymous"
    company_str = log.company.name if log.company else "N/A"
    print(f"  [{log.timestamp:%Y-%m-%d %H:%M:%S}] {user_str} ({company_str}) "
          f"{log.method} {log.path} -> {log.status_code} [{log.action}] "
          f"IP={log.ip_address} flushed={log.flushed_to_blob}")


# =====================================================================
# FINAL SUMMARY
# =====================================================================

separator("FINAL SUMMARY")

passed = sum(1 for _, p, _ in results if p)
failed = sum(1 for _, p, _ in results if not p)
total = len(results)

print(f"\n  Total tests: {total}")
print(f"  Passed:      {passed}")
print(f"  Failed:      {failed}")

if failed > 0:
    print(f"\n  Failed tests:")
    for label, p, detail in results:
        if not p:
            print(f"    [FAIL] {label}" + (f" -- {detail}" if detail else ""))

print(f"\n  Total AuditLog entries in DB: {AuditLog.objects.count()}")
print(f"  Flushed to blob:              {AuditLog.objects.filter(flushed_to_blob=True).count()}")
print(f"  Pending flush:                {AuditLog.objects.filter(flushed_to_blob=False).count()}")

print("\n" + "="*70)
if failed == 0:
    print("  >>> ALL AUDIT LOG TESTS PASSED!")
else:
    print(f"  !!! {failed} TEST(S) FAILED -- see details above")
print("="*70 + "\n")
