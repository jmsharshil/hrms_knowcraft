"""
Standalone onboarding email tester - no Django setup required.
Reads templates directly, sends via smtplib to bypass scheduler interference.
"""
import os, sys, smtplib, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import urllib.request
import urllib.parse

# ── Config ──────────────────────────────────────────────────────────────────
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "testing251299@gmail.com"
EMAIL_PASS = "hqnc uhzo lwch iwss"
FROM_ADDR  = "testing251299@gmail.com"
TO_ADDR    = "anand@jmstech.co"

MAX_ATTACH_BYTES = 15 * 1024 * 1024   # 15 MB – skip & rely on in-body URL

ATTACHMENT_URLS = {
    "hr_handbook":    "https://hireprostorage.blob.core.windows.net/media/4.1%20Attachment-Handbook%202026.pdf",
    "culture_values": "https://hireprostorage.blob.core.windows.net/media/4.2%20Attachment-Culture%20and%20Values%20Handbook.pdf",
    "chatbot_manual": "https://hireprostorage.blob.core.windows.net/media/4.4.%20Attachment-Knowcraft%20Chatbot.pdf",
    "posh_policy":    "https://hireprostorage.blob.core.windows.net/media/4.3%20Email%20Body-POSH.jpg",
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def fetch_attachment(url):
    """Download URL; return (filename, bytes, mimetype) or None if > 15 MB."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            ctype = resp.headers.get_content_type() or "application/octet-stream"
        filename = urllib.parse.unquote(url.split("/")[-1])
        mb = len(data) / (1024*1024)
        if len(data) > MAX_ATTACH_BYTES:
            print(f"   [SKIP] '{filename}' is {mb:.1f} MB > 15 MB limit — URL in email body is sufficient.")
            return None
        print(f"   [ATTACH] '{filename}' ({mb:.2f} MB)")
        return (filename, data, ctype)
    except Exception as e:
        print(f"   [ERROR] Could not fetch {url}: {e}")
        return None


def send_email(subject, html_body, attachment_tuple=None):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = FROM_ADDR
    msg["To"]      = TO_ADDR

    msg.attach(MIMEText("Please view this email in an HTML-capable client.", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    if attachment_tuple:
        fname, fdata, ftype = attachment_tuple
        part = MIMEBase(*ftype.split("/", 1) if "/" in ftype else ("application", "octet-stream"))
        part.set_payload(fdata)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{fname}"')
        msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())

# ── Minimal HTML templates (replicated inline) ───────────────────────────────
CANDIDATE_NAME = "Anand"

def base_html(title, body_content):
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,sans-serif;">
<table align="center" width="100%" style="max-width:620px;margin:0 auto;background:#f4f4f7;">
<tr><td align="center" style="padding:30px 15px;">
<table width="100%" style="background:#fff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;">
<tr><td align="center" style="padding:30px;background:#fff;">
<img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:250px;height:auto;">
</td></tr>
<tr><td style="padding:35px 40px 40px;color:#333;font-size:16px;line-height:1.6;">
{body_content}
<br><p style="margin:20px 0 4px;color:#555;">Regards,</p>
<p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
<p style="margin:4px 0 0;color:#555;font-size:14px;">Knowcraft Analytics Private Limited.</p>
</td></tr>
<tr><td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
&copy; 2026 Knowcraft Analytics Private Limited &bull; Confidential
</td></tr>
</table></td></tr></table>
</body></html>"""

EMAILS = [
    {
        "key": "welcome_wfo",
        "subject": "Welcome to Knowcraft Analytics!",
        "html": base_html("Welcome (WFO)", f"""
<h2 style="color:#1f2937;font-size:22px;">Welcome to Knowcraft Analytics!</h2>
<p>Hi <strong>{CANDIDATE_NAME}</strong>,</p>
<p>Welcome to Knowcraft Analytics! We are delighted to have you join our team.</p>
<table style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:20px;margin:16px 0;width:100%;">
<tr><td>
<p><strong>Reporting Date:</strong> [Date]</p>
<p><strong>Reporting Time:</strong> [Time]</p>
<p><strong>Office Address:</strong> Knowcraft Analytics, Ahmedabad</p>
<p><strong>Contact Person:</strong> HR Team &mdash; <a href="mailto:hr@knowcraft.in">hr@knowcraft.in</a></p>
</td></tr></table>
<p>We look forward to a successful journey together!</p>"""),
    },
    {
        "key": "welcome_wfh",
        "subject": "Welcome to Knowcraft Analytics!",
        "html": base_html("Welcome (WFH)", f"""
<h2 style="color:#1f2937;font-size:22px;">Welcome to Knowcraft Analytics!</h2>
<p>Hi <strong>{CANDIDATE_NAME}</strong>,</p>
<p>A very warm welcome to Knowcraft Analytics! We are excited to have you on board as you begin your remote journey with us.</p>
<p>Your IT setup details and system credentials will be shared with you soon. For any queries, reach out to <a href="mailto:hr@knowcraft.in">hr@knowcraft.in</a>.</p>"""),
    },
    {
        "key": "document_signoff",
        "subject": "Onboarding Document Sign-Off",
        "html": base_html("Onboarding Document Sign-Off", f"""
<h2 style="color:#1f2937;font-size:22px;">Onboarding Document Sign-Off</h2>
<p>Hello Crafter,</p>
<p>Welcome to Knowcraft Analytics!</p>
<p>As part of your onboarding, please review and complete the sign-off of the onboarding documents shared with you.</p>
<p>Kindly ensure all documents are reviewed and signed at the earliest to facilitate a seamless onboarding process.</p>
<p>Should you have any questions, feel free to reach out.</p>"""),
    },
    {
        "key": "hr_handbook",
        "subject": "HR Handbook",
        "attachment_key": "hr_handbook",
        "html": base_html("HR Handbook", f"""
<h2 style="color:#1f2937;font-size:22px;">HR Handbook</h2>
<p>Hello Crafter,</p>
<p>Welcome to Knowcraft Analytics!</p>
<p>Attached to this email is the <strong>HR Handbook</strong>. We encourage you to go through it carefully to familiarize yourself with our policies, processes, and benefits.</p>
<p>Should you have questions, reach out to <a href="mailto:hr@knowcraft.in">hr@knowcraft.in</a>.</p>"""),
    },
    {
        "key": "culture_values",
        "subject": "Exploring the Culture and Values of Knowcraft",
        "attachment_key": "culture_values",
        "html": base_html("Culture & Values", f"""
<h2 style="color:#1f2937;font-size:22px;">Exploring the Culture and Values of Knowcraft</h2>
<p>Hello Crafter,</p><p>Greetings!</p>
<p>Attached is a handbook on Knowcraft's Culture and Values. We encourage you to read through it and familiarize yourself with the principles that guide our decisions.</p>
<div style="margin:16px 0;text-align:center;">
<a href="{ATTACHMENT_URLS['culture_values']}" target="_blank"
   style="background:#2563eb;color:#fff;text-decoration:none;padding:12px 24px;border-radius:6px;font-weight:bold;display:inline-block;">
Download Culture &amp; Values Handbook (PDF)</a>
</div>
<p>While not a policy document, it serves as our collective moral compass.</p>"""),
    },
    {
        "key": "chatbot_manual",
        "subject": "HR Buddy - MS Teams Chatbot User Manual",
        "attachment_key": "chatbot_manual",
        "html": base_html("Chatbot Manual", f"""
<h2 style="color:#1f2937;font-size:22px;">HR Buddy &ndash; MS Teams Chatbot User Manual</h2>
<p>Hello Crafter,</p>
<p>Attached is the <strong>HR Buddy Chatbot User Manual</strong> to help you navigate our internal MS Teams bot for HR queries.</p>"""),
    },
    {
        "key": "kai_mascot",
        "subject": "Meet KAI - Your Crafter Happiness Mascot!",
        "html": base_html("KAI Mascot", f"""
<h2 style="color:#1f2937;font-size:22px;">Meet KAI &ndash; Your Crafter Happiness Mascot!</h2>
<p>Hello Crafter,</p>
<p>We are excited to introduce you to <strong>KAI</strong>, your Crafter Happiness Mascot at Knowcraft Analytics!</p>
<p>KAI is here to ensure your journey with us is fulfilling, engaging, and full of growth. Look out for periodic check-ins and pulse surveys from KAI throughout your onboarding.</p>"""),
    },
    {
        "key": "posh_policy",
        "subject": "POSH Policy & Guidelines",
        "attachment_key": "posh_policy",
        "html": base_html("POSH Policy", f"""
<h2 style="color:#1f2937;font-size:22px;">POSH Policy &amp; Guidelines</h2>
<p>Hello Crafter,</p>
<p>As part of your onboarding, please find attached our <strong>POSH (Prevention of Sexual Harassment) Policy</strong>.</p>
<p>We are committed to maintaining a safe, respectful, and inclusive workplace for all.</p>"""),
    },
]

# ── Main ──────────────────────────────────────────────────────────────────────
print(f"FROM: {FROM_ADDR}")
print(f"TO:   {TO_ADDR}")
print(f"SMTP: {SMTP_HOST}:{SMTP_PORT}")
print("=" * 60)

for i, email in enumerate(EMAILS, 1):
    print(f"{i}. {email['subject']}")
    att = None
    if "attachment_key" in email:
        att = fetch_attachment(ATTACHMENT_URLS[email["attachment_key"]])
    try:
        send_email(email["subject"], email["html"], att)
        print(f"   [OK] Sent successfully")
    except Exception as e:
        print(f"   [FAIL] {e}")

print("=" * 60)
print("Done.")

