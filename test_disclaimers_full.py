"""
Comprehensive verification test for corporate automated message disclaimers across:
1. onboarding.utils.disclaimers
2. onboarding.utils.sender (send_email, send_text, send_document, send_image, send_location)
3. onboarding.utils.templates (HTML_TEMPLATES, NOTIFY_INTERNAL_HTML_TEMPLATES)
4. booking.email_templates (all templates & dynamic generator)
"""
import os
import sys
from unittest.mock import patch, MagicMock

# 1. Test onboarding.utils.disclaimers directly
from onboarding.utils.disclaimers import (
    EMAIL_DISCLAIMER_HTML,
    EMAIL_DISCLAIMER_TEXT,
    SMS_DISCLAIMER_TEXT,
    append_email_html_disclaimer,
    append_email_text_disclaimer,
    append_sms_disclaimer,
)

print("--- TEST 1: Disclaimers Module ---")
# Check content of disclaimers
assert "Automated Notification" in EMAIL_DISCLAIMER_HTML
assert "do not reply directly to this email" in EMAIL_DISCLAIMER_HTML
assert "talent@knowcraft.in" in EMAIL_DISCLAIMER_HTML

assert "do not reply directly to this email" in EMAIL_DISCLAIMER_TEXT
assert "talent@knowcraft.in" in EMAIL_DISCLAIMER_TEXT

assert "*Please Note:*" in SMS_DISCLAIMER_TEXT
assert "Inbound replies to this number are not monitored" in SMS_DISCLAIMER_TEXT
assert "talent@knowcraft.in" in SMS_DISCLAIMER_TEXT

# Test append_email_html_disclaimer
test_html = "<html><body><p>Hello World</p></body></html>"
appended_html = append_email_html_disclaimer(test_html)
assert "Automated Notification" in appended_html
assert appended_html.endswith("</body></html>")
# Idempotency
assert append_email_html_disclaimer(appended_html) == appended_html

# Test append_email_text_disclaimer
test_text = "Hello Candidate, your application is under review."
appended_text = append_email_text_disclaimer(test_text)
assert "do not reply directly to this email" in appended_text
assert append_email_text_disclaimer(appended_text) == appended_text

# Test append_sms_disclaimer
test_sms = "Your interview has been scheduled."
appended_sms = append_sms_disclaimer(test_sms)
assert "*Please Note:*" in appended_sms
assert "Inbound replies to this number are not monitored" in appended_sms
assert append_sms_disclaimer(appended_sms) == appended_sms

print("  [PASS] Unit tests for disclaimers.py succeeded!")

# 2. Test templates in onboarding.utils.templates
print("\n--- TEST 2: Templates in onboarding.utils.templates ---")
# To import templates.py without Django setup, mock settings
import types
settings_mock = types.ModuleType("django.conf")
class SettingsObj:
    FRONTEND_URL = "https://example.com"
settings_mock.settings = SettingsObj()
sys.modules["django.conf"] = settings_mock

# Now read templates
with open("onboarding/utils/templates.py", "r", encoding="utf-8") as f:
    code = f.read()

# Exec in controlled namespace
ns = {
    "__name__": "onboarding.utils.templates",
    "__package__": "onboarding.utils",
    "FRONTEND_URL": "https://example.com",
    "settings": SettingsObj(),
}
exec(code, ns)

html_templates = ns["HTML_TEMPLATES"]
notify_internal = ns["NOTIFY_INTERNAL_HTML_TEMPLATES"]

print(f"Checking {len(html_templates)} candidate HTML templates...")
for k, tpl in html_templates.items():
    assert "Automated Notification" in tpl, f"Template {k} missing disclaimer!"
print(f"  [PASS] All {len(html_templates)} HTML_TEMPLATES have the disclaimer!")

print(f"Checking {len(notify_internal)} internal notification HTML templates...")
for k, tpl in notify_internal.items():
    assert "Automated Notification" in tpl, f"Internal template {k} missing disclaimer!"
print(f"  [PASS] All {len(notify_internal)} NOTIFY_INTERNAL_HTML_TEMPLATES have the disclaimer!")

# 3. Test booking.email_templates
print("\n--- TEST 3: booking.email_templates ---")
with open("booking/email_templates.py", "r", encoding="utf-8") as f:
    booking_code = f.read()

b_ns = {}
exec(booking_code, b_ns)

template_vars = [k for k in b_ns if k.endswith("_template") and isinstance(b_ns[k], str)]
print(f"Checking {len(template_vars)} booking email template variables...")
for var in template_vars:
    assert "Automated Notification" in b_ns[var], f"Booking template {var} missing disclaimer!"
print(f"  [PASS] All {len(template_vars)} booking template variables have the disclaimer!")

# Test dynamic generator
mock_candidate = MagicMock()
mock_candidate.job.mrf.designation.name = "Software Engineer"
mock_interviewer = MagicMock()
mock_interviewer.name = "John Doe"

gen_html = b_ns["get_interviewer_email_template"](
    action="scheduled",
    candidate=mock_candidate,
    interviewer=mock_interviewer,
    start_str="2026-10-20 10:00 AM",
    meeting_link="https://teams.microsoft.com",
    feedback_link="https://example.com/feedback"
)
assert "Automated Notification" in gen_html
print("  [PASS] get_interviewer_email_template produces disclaimer!")

# 4. Test sender.py hooks
print("\n--- TEST 4: onboarding.utils.sender integration ---")
# Test send_text appends disclaimer
with patch("onboarding.utils.sender.SEND_QUEUE") as mock_queue:
    from onboarding.utils.sender import send_text, send_document, send_image, send_location

    send_text("919999999999", "Your application is shortlisted.")
    enqueued_payload = mock_queue.enqueue.call_args[0][0]
    assert "*Please Note:*" in enqueued_payload["text"]
    assert "Inbound replies to this number are not monitored" in enqueued_payload["text"]
    print("  [PASS] send_text properly appends disclaimer to outgoing payload!")

    # Test send_document
    mock_queue.reset_mock()
    send_document("919999999999", "https://example.com/doc.pdf", "offer.pdf", text="Please find your offer letter.")
    doc_payload = mock_queue.enqueue.call_args[0][0]
    assert "*Please Note:*" in doc_payload["text"]
    print("  [PASS] send_document properly appends disclaimer!")

    # Test send_image
    mock_queue.reset_mock()
    send_image("919999999999", "https://example.com/img.png", caption="Office location map")
    img_payload = mock_queue.enqueue.call_args[0][0]
    assert "*Please Note:*" in img_payload["text"]
    print("  [PASS] send_image properly appends disclaimer to caption!")

    # Test send_location
    mock_queue.reset_mock()
    send_location("919999999999", 23.0, 72.0, "Our Office", "Address details", "HQ")
    loc_payload = mock_queue.enqueue.call_args[0][0]
    assert "*Please Note:*" in loc_payload["text"]
    print("  [PASS] send_location properly appends disclaimer!")

print("\n" + "=" * 60)
print("ALL VERIFICATION SUITES PASSED SUCCESSFULLY!")
print("=" * 60)
