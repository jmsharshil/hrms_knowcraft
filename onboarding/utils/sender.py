from django.core.mail import send_mail,EmailMultiAlternatives
from django.conf import settings
import requests
import time
import threading
import os
import queue
import logging
logger = logging.getLogger(__name__)

def send_email(to, subject, cc=[], text="", template=None, attachments=None, use_default_cc=True, is_private=False, event="", email_type="other", candidate=None):
    if is_private:
        logger.info(f"Skipping email to {to} for private record: {subject}")
        _log_email(to, cc, subject, text, template, event, email_type, candidate, status="skipped")
        return

    cc_list = list(cc)
    if use_default_cc:
        cc_list.append("talent@knowcraft.in")

    try:
        msg = EmailMultiAlternatives(subject, text, "talent@knowcraft.in", to=[to], cc=cc_list)
        if template:
            msg.attach_alternative(template, "text/html")
        if attachments:
            for attachment in attachments:
                try:
                    if isinstance(attachment, str):
                        # attachment is a file path
                        filename = attachment.split("/")[-1]
                        with open(attachment, "rb") as f:
                            msg.attach(filename, f.read(), "application/pdf")
                    else:
                        # attachment is a tuple
                        # (filename, content_bytes, mimetype)
                        msg.attach(*attachment)
                except Exception as e:
                    print("Error Attaching Documents:", e)
            pass
        msg.send()
        _log_email(to, cc_list, subject, text, template, event, email_type, candidate, status="sent")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        _log_email(to, cc_list, subject, text, template, event, email_type, candidate, status="failed", error=str(e))


def _log_email(to, cc, subject, text, template, event, email_type, candidate, status="sent", error=None):
    """Persist an email audit record (fire-and-forget, never blocks the caller)."""
    try:
        from onboarding.models import EmailLog
        EmailLog.objects.create(
            recipient_email=to,
            cc_emails=cc or [],
            subject=subject,
            body_text=text or "",
            body_html=template or "",
            event=event or "unknown",
            email_type=email_type or "other",
            candidate=candidate,
            status=status,
            error_message=error or "",
        )
    except Exception as exc:
        logger.warning(f"Failed to log email record: {exc}")


API_BASE = "https://www.wasenderapi.com"
API_KEY = settings.__getattr__("WASENDER_API_KEY")
RETRY_QUEUE = queue.Queue()
STOP_RETRY_THREAD = False

def _headers():
    if not API_KEY:
        raise RuntimeError("WASENDER_API_KEY is not set")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

def send_text(to: str, text: str, is_private=False):
    """Try common payload variants so we don't get stuck on a minor mismatch."""
    if is_private:
        logger.info(f"Skipping text to {to} for private record")
        return

    if not to:
        logger.error("Missing recipient number in send_text()")
        return
    
    # 1) 'to' + 'text'  (most common)
    try:
        payload = {"to": to, "text": text}
        # return _safe_post_async(payload)
        return SEND_QUEUE.enqueue(payload)

    except Exception as e1:
        logger.warning("send_text variant1 failed: %s", e1)

    # 2) 'number' + 'text'
    try:
        payload= {"number": to, "text": text}
        # return _safe_post_async(payload)
        return SEND_QUEUE.enqueue(payload)
    except Exception as e2:
        logger.warning("send_text variant2 failed: %s", e2)

    # 3) 'to' + 'message'
    payload={"to": to, "message": text}
    return SEND_QUEUE.enqueue(payload)
    # return _safe_post_async(payload)

def send_image(to: str, image_url: str, caption: str = "", is_private=False):
    if is_private:
        logger.info(f"Skipping image to {to} for private record")
        return

    if not to:
        logger.error("Missing recipient number in send_image()")
        return
    
    # 1) 'imageUrl' + (optional 'text')
    payload = {"to": to, "imageUrl": image_url}
    if caption:
        payload["text"] = caption
    try:
        # return _safe_post_async(payload)
        return SEND_QUEUE.enqueue(payload)
    except Exception as e1:
        logger.warning("send_image variant1 failed: %s", e1)

    # 2) fallback 'image' + 'caption'
    payload = {"to": to, "image": image_url}
    if caption:
        payload["caption"] = caption
    # return _safe_post_async(payload)
    return SEND_QUEUE.enqueue(payload)

def send_document(to: str, file_url: str, filename: str, text: str = "", is_private=False):
    if is_private:
        logger.info(f"Skipping document to {to} for private record")
        return

    if not to:
        logger.error("Missing recipient number in send_document()")
        return
    
    payload = {"to": to, "documentUrl": file_url, "fileName":filename}
    if text:
        payload["text"] = text
    
    return SEND_QUEUE.enqueue(payload)

def send_location(phone: str, latitude: float, longitude: float, text: str, address: str, name: str, is_private=False):
    """
    Sends a WhatsApp location message via WaSender API.

    Args:
        phone (str): Recipient's phone number in international format (e.g., '918401611072')
        latitude (float): Latitude of location
        longitude (float): Longitude of location
        address (str): Full address or description
        text (str): The text content of the message. Required if no media/contact/location is sent.
        is_private (bool): If True, communication is suppressed.
    """
    if is_private:
        logger.info(f"Skipping location to {phone} for private record")
        return

    if not phone:
        logger.error("Missing recipient number in send_location()")
        return
    
    payload = {
        "to": phone,
        "text": text,
        "location":{
        "latitude": latitude,
        "longitude": longitude,
        "name": name,
        "address": address
        }
    }
    try:
        # return _safe_post_async(payload)
        return SEND_QUEUE.enqueue(payload)
    except Exception as e1:
        logger.warning("send location failed: %s", e1)

def send_contact(phone: str, contact_name: str, contact_number: str, is_private=False):
    """
    Sends a WhatsApp contact card (vCard) via WaSender API.

    Args:
        phone (str): Recipient's phone number in international format (e.g., '918401611072')
        contact_name (str): Contact's full name
        contact_number (str): Contact's phone number (in international format)
        is_private (bool): If True, communication is suppressed.
    """
    if is_private:
        logger.info(f"Skipping contact to {phone} for private record")
        return

    if not phone:
        logger.error("Missing recipient number in send_contact()")
        return
    
    payload = {
        "to": phone,
        "contact":{
            "name":contact_name,
            "phone":contact_number
        }
    }
    try:
        # return _safe_post_async(payload)
        return SEND_QUEUE.enqueue(payload)
    except Exception as e1:
        logger.warning("send contact failed: %s", e1)

class WasenderQueue:
    def __init__(self, api_base: str, headers_func, max_retries=5, pause_after_success=0.4):
        self.api_base = api_base.rstrip("/") + "/api/send-message"
        self._headers = headers_func
        self.session = requests.Session()
        self.queue = queue.Queue()
        self.max_retries = max_retries
        self.pause_after_success = pause_after_success
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        logger.info("WasenderQueue started, sending to %s", self.api_base)

    def enqueue(self, payload: dict):
        """Enqueue payload (non-blocking)."""
        # attach a timestamp or id if you want tracing
        payload["_enqueued_at"] = time.time()
        self.queue.put(payload)
        return True

    def _worker(self):
        """Continuously process queue items, one-by-one."""
        while True:
            payload = self.queue.get()
            try:
                self._process_payload(payload)
            except Exception as e:
                logger.exception("Unexpected worker error: %s", e)
            finally:
                self.queue.task_done()

    def _process_payload(self, payload: dict):
        """Try to send a single payload with internal retries/backoff."""
        attempt = 0
        delay = 1.0
        max_attempts = payload.get("_max_retries", self.max_retries)

        while attempt < max_attempts:
            attempt += 1
            try:
                logger.debug("Sending (attempt %d/%d) to %s: %s", attempt, max_attempts, payload.get("to"), payload)
                r = self.session.post(self.api_base, json=payload, headers=self._headers(), timeout=15)
                status = r.status_code
                if status < 300:
                    # success
                    logger.info("✅ Message sent to %s (attempt %d).", payload.get("to"), attempt)
                    # small pause to help with ordering and API processing
                    if self.pause_after_success:
                        time.sleep(self.pause_after_success)
                    return
                # handle rate limiting explicitly
                if status == 429:
                    logger.warning("⚠️ Rate limited sending to %s (attempt %d/%d). Retrying in %ds",
                                   payload.get("to"), attempt, max_attempts, int(delay))
                    time.sleep(delay)
                    delay = min(delay, 30)
                    continue
                # for other 5xx errors also retry
                if 500 <= status < 600:
                    logger.warning("Server error %s when sending to %s. Retrying in %ds. resp=%s",
                                   status, payload.get("to"), int(delay), r.text[:200])
                    time.sleep(delay)
                    delay = min(delay, 30)
                    continue

                # for 4xx (client error) we normally don't retry, but log and bail
                logger.error("Failed to send to %s: status=%s, resp=%s", payload.get("to"), status, r.text[:400])
                return
            except requests.exceptions.RequestException as e:
                logger.warning("Network error sending to %s (attempt %d/%d): %s. Retrying in %ds",
                               payload.get("to"), attempt, max_attempts, e, int(delay))
                time.sleep(delay)
                delay = min(delay, 30)

        logger.error("❌ Giving up after %d attempts for %s", max_attempts, payload.get("to"))
        # you can add code here to persist failed payloads or notify admins

# instantiate a global queue object (use same _headers function you already have)
SEND_QUEUE = WasenderQueue(API_BASE, _headers, max_retries=20, pause_after_success=0.4)
