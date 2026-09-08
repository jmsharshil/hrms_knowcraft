import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_knowcraft.settings')
django.setup()
from django.conf import settings
settings.ONBOARDING_DEBUG_MINUTES = True

from onboarding.utils.zoho_manageengine import ManageEngineClient

print("=== Zoho ManageEngine Credential & Permission Diagnostic ===")
print("Base URL:", 'https://itsm.knowcraft.in/api/v3')
print("Debug mode:", getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False))
print("\nTesting client initialization...")

client = ManageEngineClient()

print("\n1. Testing access token...")
token = client._get_access_token()
if token:
    print("✅ Token acquired (first 15 chars):", token[:15] + "...")
else:
    print("❌ No token - check ZOHO_CLIENT_ID/SECRET/REFRESH_TOKEN in .env")

print("\n2. Testing READ permission (get_requesters)...")
requesters = client.get_requesters()
print("✅ READ worked - found", len(requesters) if isinstance(requesters, list) else 0, "requesters")

print("\n3. Testing CREATE permission (create_requester for anand@jmstech.co)...")
result = client.create_requester("Anand Shah", "anand@jmstech.co")
print("CREATE result:", result)

print("\n=== Required OAuth Scopes ===")
print("For full functionality the app must have these scopes granted during OAuth:")
print(" - SDP_OnDemand_Users.READ")
print(" - SDP_OnDemand_Users.CREATE")
print(" - SDP_OnDemand_Users.UPDATE")
print(" - SDP_OnDemand_Requests.CREATE")
print(" - SDP_OnDemand_Requests.READ")
print("\nIf CREATE fails with 403 but READ works, the token/user lacks the CREATE scope/permission.")
print("Re-generate the refresh_token with the full list of scopes at:")
print("https://accounts.zoho.in/oauth/v2/auth?scope=SDP_OnDemand_Users.READ,SDP_OnDemand_Users.CREATE,SDP_OnDemand_Users.UPDATE,SDP_OnDemand_Requests.CREATE&client_id=...&response_type=code&redirect_uri=...")
print("\nTest complete.")
