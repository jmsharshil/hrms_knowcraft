# disclaimers.py
"""
Corporate automated message disclaimers and footers for HRMS notifications.
Provides standardized, professional disclaimers for emails (HTML and plain text)
and WhatsApp/SMS text communications.
"""

EMAIL_DISCLAIMER_HTML = """
<!-- Automated Notification Footer -->
<table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:20px auto 10px auto;">
    <tr>
        <td align="center" style="padding:10px 20px;font-family:Arial,Helvetica,sans-serif;text-align:center;">
            <p style="margin:0 0 4px 0;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;">
                Automated Notification
            </p>
            <p style="margin:0;font-size:12px;line-height:1.5;color:#64748b;">
                This is an automated system-generated communication. Please do not reply directly to this email as this mailbox is unattended and incoming messages are not monitored.<br>
                For inquiries or assistance, please contact the Talent Acquisition Team at <a href="mailto:talent@knowcraft.in" style="color:#2563eb;text-decoration:none;font-weight:500;">talent@knowcraft.in</a>.
            </p>
        </td>
    </tr>
</table>
"""

EMAIL_DISCLAIMER_TEXT = (
    "\n\n---\n"
    "Please note: This is an automated system-generated communication. Please do not reply directly to this email as this mailbox is unattended and incoming messages are not monitored. "
    "For inquiries or assistance, please contact the Talent Acquisition Team at talent@knowcraft.in."
)

SMS_DISCLAIMER_TEXT = (
    "\n\n---\n"
    "*Please Note:* This is an automated system-generated message. Inbound replies to this number are not monitored. "
    "If you have any questions or require assistance, please contact talent@knowcraft.in."
)


def append_email_html_disclaimer(html: str) -> str:
    """
    Append a sophisticated automated notification footer to an HTML email template.
    Ensures idempotency - will not duplicate if already present.
    """
    if not html or not isinstance(html, str):
        return html
    if "Automated Notification" in html or "do not reply directly to this email" in html.lower():
        return html

    idx = html.rfind("</body>")
    if idx != -1:
        return html[:idx] + EMAIL_DISCLAIMER_HTML + html[idx:]

    idx_html = html.rfind("</html>")
    if idx_html != -1:
        return html[:idx_html] + EMAIL_DISCLAIMER_HTML + html[idx_html:]

    return html + EMAIL_DISCLAIMER_HTML


def append_email_text_disclaimer(text: str) -> str:
    """
    Append a corporate automated message disclaimer to plain-text email content.
    Ensures idempotency.
    """
    if text is None:
        text = ""
    if "do not reply directly to this email" in text.lower():
        return text

    stripped = text.rstrip()
    if not stripped:
        return "Please refer to the accompanying HTML content for details." + EMAIL_DISCLAIMER_TEXT
    return stripped + EMAIL_DISCLAIMER_TEXT


def append_sms_disclaimer(text: str) -> str:
    """
    Append a sophisticated corporate automated message disclaimer to WhatsApp / SMS text messages.
    Ensures idempotency.
    """
    if not text or not isinstance(text, str):
        return text
    if (
        "inbound replies to this number are not monitored" in text.lower()
        or "do not reply directly to this message" in text.lower()
        or "replies are unmonitored" in text.lower()
    ):
        return text

    return text.rstrip() + SMS_DISCLAIMER_TEXT
