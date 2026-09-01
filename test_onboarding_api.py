"""
Quick test script for POST /onboarding/application/<id>/initiate-onboarding/
Runs against the BACKEND_URL from .env
"""
import psycopg2, requests, os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── 1. Find a valid application ID ──────────────────────────────────────────
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
cur.execute("SELECT id, candidate_name, status FROM job_applications ORDER BY created_at DESC LIMIT 5")
rows = cur.fetchall()
print("=== Available Applications ===")
for r in rows:
    print(f"  ID: {r[0]}  |  Name: {r[1]}  |  Status: {r[2]}")

if not rows:
    print("No applications found!")
    exit(1)

app_id = str(rows[0][0])
print(f"\nUsing application: {app_id}")

# ── 2. Get a JWT token ─────────────────────────────────────────────────────
cur.execute("SELECT email FROM accounts_user WHERE role='admin' LIMIT 1")
admin_row = cur.fetchone()

# Check table name
if not admin_row:
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%user%'")
    tables = cur.fetchall()
    print(f"User tables: {tables}")
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%account%'")
    tables2 = cur.fetchall()
    print(f"Account tables: {tables2}")
    
conn.close()

if admin_row:
    admin_email = admin_row[0]
    print(f"Admin email: {admin_email}")
else:
    print("No admin user found, will try without auth first")
    admin_email = None

# ── 3. Try to get JWT token via login ──────────────────────────────────────
token = None
if admin_email:
    # Try common login endpoints
    login_urls = [
        f"{BACKEND}/api/auth/login/",
        f"{BACKEND}/api/token/",
        f"{BACKEND}/api/accounts/login/",
    ]
    for url in login_urls:
        try:
            r = requests.post(url, json={"email": admin_email, "password": "admin"}, timeout=5)
            print(f"  Login attempt {url}: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                token = data.get("access") or data.get("token") or data.get("access_token")
                if token:
                    print(f"  ✅ Got token from {url}")
                    break
        except Exception as e:
            print(f"  ❌ {url}: {e}")

# ── 4. Call the initiate-onboarding endpoint ───────────────────────────────
api_url = f"{BACKEND}/api/onboarding/application/{app_id}/initiate-onboarding/"
print(f"\n=== Testing POST {api_url} ===")

payload = {
    "subject": "Onboarding Request – Test Candidate",
    "first_name": "Test",
    "last_name": "Candidate",
    "personal_email_id": "test.candidate@gmail.com",
    "contact_number": "+919876543210",
    "joining_date": "2026-09-15",
    "designation": "Software Engineer",
    "department": "Engineering",
    "employee_category": "Full-time",
    "center_office_location": "Mumbai Office",
    "mode_for_collecting_assets": "Office Pickup",
    "team_manager": "manager@knowcraft.com",
    "work_from": "Hybrid",
    "emails_to_notify": "it@knowcraft.com, admin@knowcraft.com",
    "current_address": "Flat 302, MG Road, Mumbai 400069",
    "description": "New hire for Platform team",
    "custom_notes": "Test submission via script",
}

headers = {"Content-Type": "application/json"}
if token:
    headers["Authorization"] = f"Bearer {token}"

resp = requests.post(api_url, json=payload, headers=headers, timeout=15)

print(f"\nStatus Code: {resp.status_code}")
print(f"Response Headers: {dict(resp.headers)}")
try:
    print(f"Response Body: {resp.json()}")
except:
    print(f"Response Text: {resp.text[:500]}")
