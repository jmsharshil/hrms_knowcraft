from django.core.mail import send_mail,EmailMultiAlternatives
from django.conf import settings
import requests
import time
import threading
import os
import queue
import logging
from .disclaimers import append_email_html_disclaimer, append_email_text_disclaimer, append_sms_disclaimer
logger = logging.getLogger(__name__)

def send_email(to, subject, cc=[], text="", template=None, attachments=None, use_default_cc=True, is_private=False, event="", email_type="other", candidate=None):
    # Ensure corporate automated message disclaimers are present on all emails
    if template:
        template = append_email_html_disclaimer(template)
    text = append_email_text_disclaimer(text)

    if is_private:
        logger.info(f"Skipping email to {to} for private record: {subject}")
        _log_email(to, cc, subject, text, template, event, email_type, candidate, status="skipped")
        return

    cc_list = list(cc)
    if use_default_cc:
        cc_list.append("talent@knowcraft.in")

    # ── Multi-Worker Deduplication Guard ─────────────────────────────
    # If the exact same email (same recipient and subject, and candidate if specified)
    # was already sent within the last 300 seconds (5 minutes),
    # suppress duplicate sends from concurrent workers or overlapping tasks.
    # try:
    #     from onboarding.models import EmailLog
    #     from django.utils import timezone
    #     from datetime import timedelta
    #     from django.db.models import Q

    #     recent_window = timezone.now() - timedelta(seconds=300)
    #     recent_query = EmailLog.objects.filter(
    #         recipient_email=to,
    #         subject=subject,
    #         sent_at__gte=recent_window,
    #     ).filter(
    #         Q(status="sent") | Q(error_message="Intercepted for debug approval")
    #     )
    #     if candidate and hasattr(candidate, 'id'):
    #         recent_query = recent_query.filter(candidate=candidate)

    #     if recent_query.exists():
    #         logger.warning(
    #             f"[DEDUPLICATION] Preventing duplicate email to '{to}' with subject '{subject}' "
    #             f"(already processed within the last 300s). Skipping duplicate."
    #         )
    #         _log_email(
    #             to, cc_list, subject, text, template, event, email_type, candidate,
    #             status="skipped",
    #             error="Duplicate email suppressed by multi-worker guard (already sent within 300s)"
    #         )
    #         return
    # except Exception as dedup_err:
    #     logger.warning(f"[DEDUPLICATION] Error checking recent email logs: {dedup_err}")

    is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
    if is_debug:
        logger.info(f"[DEBUG MODE] Intercepting email to {to}: {subject}. Marking as skipped (pending approval).")
        _log_email(to, cc_list, subject, text, template, event, email_type, candidate, status="skipped", error="Intercepted for debug approval")
        return

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


def _log_whatsapp(to, text="", message_type="text", event="whatsapp", candidate=None, file_url=None, filename=None, status="sent", error=None):
    """Persist a WhatsApp audit record (fire-and-forget, never blocks the caller)."""
    try:
        from onboarding.models import WhatsAppLog, JobApplication
        from django.db.models import Q

        if candidate is None and to:
            try:
                clean_phone = str(to).strip().replace(" ", "").replace("-", "")
                if len(clean_phone) >= 10:
                    candidate = JobApplication.objects.filter(
                        Q(candidate_phone__icontains=clean_phone[-10:])
                    ).order_by("-created_at").first()
            except Exception:
                candidate = None

        return WhatsAppLog.objects.create(
            recipient_phone=str(to or ""),
            message_text=text or "",
            message_type=message_type or "text",
            file_url=file_url,
            filename=filename,
            event=event or "whatsapp",
            candidate=candidate,
            status=status,
            error_message=error or "",
        )
    except Exception as exc:
        logger.warning(f"Failed to log whatsapp record: {exc}")
        return None


def send_text(to: str, text: str, is_private=False, candidate=None, event="whatsapp_text", **kwargs):
    """Send WhatsApp text message. Suppressed when ONBOARDING_DEBUG_MINUTES is True."""
    if is_private:
        logger.info(f"Skipping text to {to} for private record")
        _log_whatsapp(to, text, message_type="text", event=event, candidate=candidate, status="skipped", error="Skipped for private record")
        return

    if not to:
        logger.error("Missing recipient number in send_text()")
        return
    
    # Append corporate automated communication disclaimer
    if text:
        text = append_sms_disclaimer(text)

    is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
    if is_debug:
        logger.info(f"[DEBUG MODE] Intercepting text/whatsapp to {to}. Marking as skipped (pending approval).")
        _log_whatsapp(to, text, message_type="text", event=event, candidate=candidate, status="skipped", error="Intercepted for debug approval")
        return

    payload = {"to": to, "text": text}
    try:
        log_obj = _log_whatsapp(to, text, message_type="text", event=event, candidate=candidate, status="sent")
        if log_obj:
            payload["_log_id"] = str(log_obj.id)
        return SEND_QUEUE.enqueue(payload)
    except Exception as e1:
        logger.warning("send_text failed: %s", e1)
        _log_whatsapp(to, text, message_type="text", event=event, candidate=candidate, status="failed", error=str(e1))


def send_image(to: str, image_url: str, caption: str = "", is_private=False, candidate=None, event="whatsapp_image", **kwargs):
    """Send WhatsApp image. Suppressed when ONBOARDING_DEBUG_MINUTES is True."""
    if is_private:
        logger.info(f"Skipping image to {to} for private record")
        _log_whatsapp(to, caption, message_type="image", event=event, candidate=candidate, file_url=image_url, status="skipped", error="Skipped for private record")
        return

    if not to:
        logger.error("Missing recipient number in send_image()")
        return

    is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
    if is_debug:
        logger.info(f"[DEBUG MODE] Intercepting whatsapp image to {to}. Marking as skipped (pending approval).")
        _log_whatsapp(to, caption, message_type="image", event=event, candidate=candidate, file_url=image_url, status="skipped", error="Intercepted for debug approval")
        return

    payload = {"to": to, "imageUrl": image_url}
    if caption:
        payload["text"] = caption
    try:
        log_obj = _log_whatsapp(to, caption, message_type="image", event=event, candidate=candidate, file_url=image_url, status="sent")
        if log_obj:
            payload["_log_id"] = str(log_obj.id)
        return SEND_QUEUE.enqueue(payload)
    except Exception as e1:
        logger.warning("send_image failed: %s", e1)
        _log_whatsapp(to, caption, message_type="image", event=event, candidate=candidate, file_url=image_url, status="failed", error=str(e1))


def send_document(to: str, file_url: str, filename: str, text: str = "", is_private=False, candidate=None, event="whatsapp_document", **kwargs):
    """Send WhatsApp document. Suppressed when ONBOARDING_DEBUG_MINUTES is True."""
    if is_private:
        logger.info(f"Skipping document to {to} for private record")
        _log_whatsapp(to, text, message_type="document", event=event, candidate=candidate, file_url=file_url, filename=filename, status="skipped", error="Skipped for private record")
        return

    if not to:
        logger.error("Missing recipient number in send_document()")
        return

    is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
    if is_debug:
        logger.info(f"[DEBUG MODE] Intercepting whatsapp document to {to}. Marking as skipped (pending approval).")
        _log_whatsapp(to, text, message_type="document", event=event, candidate=candidate, file_url=file_url, filename=filename, status="skipped", error="Intercepted for debug approval")
        return

    payload = {"to": to, "documentUrl": file_url, "fileName": filename}
    if text:
        payload["text"] = text
    try:
        log_obj = _log_whatsapp(to, text, message_type="document", event=event, candidate=candidate, file_url=file_url, filename=filename, status="sent")
        if log_obj:
            payload["_log_id"] = str(log_obj.id)
        return SEND_QUEUE.enqueue(payload)
    except Exception as e1:
        logger.warning("send_document failed: %s", e1)
        _log_whatsapp(to, text, message_type="document", event=event, candidate=candidate, file_url=file_url, filename=filename, status="failed", error=str(e1))


def send_location(phone: str, latitude: float, longitude: float, text: str, address: str, name: str, is_private=False, candidate=None, event="whatsapp_location", **kwargs):
    """
    Sends a WhatsApp location message via WaSender API. Suppressed when ONBOARDING_DEBUG_MINUTES is True.
    """
    if is_private:
        logger.info(f"Skipping location to {phone} for private record")
        _log_whatsapp(phone, text or f"Location: {name}, {address}", message_type="location", event=event, candidate=candidate, status="skipped", error="Skipped for private record")
        return

    if not phone:
        logger.error("Missing recipient number in send_location()")
        return

    is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
    if is_debug:
        logger.info(f"[DEBUG MODE] Intercepting whatsapp location to {phone}. Marking as skipped (pending approval).")
        _log_whatsapp(phone, text or f"Location: {name}, {address}", message_type="location", event=event, candidate=candidate, status="skipped", error="Intercepted for debug approval")
        return

    payload = {
        "to": phone,
        "text": text,
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "name": name,
            "address": address
        }
    }
    try:
        log_obj = _log_whatsapp(phone, text or f"Location: {name}, {address}", message_type="location", event=event, candidate=candidate, status="sent")
        if log_obj:
            payload["_log_id"] = str(log_obj.id)
        return SEND_QUEUE.enqueue(payload)
    except Exception as e1:
        logger.warning("send location failed: %s", e1)
        _log_whatsapp(phone, text or f"Location: {name}, {address}", message_type="location", event=event, candidate=candidate, status="failed", error=str(e1))


def send_contact(phone: str, contact_name: str, contact_number: str, is_private=False, candidate=None, event="whatsapp_contact", **kwargs):
    """
    Sends a WhatsApp contact card (vCard) via WaSender API. Suppressed when ONBOARDING_DEBUG_MINUTES is True.
    """
    if is_private:
        logger.info(f"Skipping contact to {phone} for private record")
        _log_whatsapp(phone, f"Contact: {contact_name} ({contact_number})", message_type="contact", event=event, candidate=candidate, status="skipped", error="Skipped for private record")
        return

    if not phone:
        logger.error("Missing recipient number in send_contact()")
        return

    is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
    if is_debug:
        logger.info(f"[DEBUG MODE] Intercepting whatsapp contact to {phone}. Marking as skipped (pending approval).")
        _log_whatsapp(phone, f"Contact: {contact_name} ({contact_number})", message_type="contact", event=event, candidate=candidate, status="skipped", error="Intercepted for debug approval")
        return

    payload = {
        "to": phone,
        "contact": {
            "name": contact_name,
            "phone": contact_number
        }
    }
    try:
        log_obj = _log_whatsapp(phone, f"Contact: {contact_name} ({contact_number})", message_type="contact", event=event, candidate=candidate, status="sent")
        if log_obj:
            payload["_log_id"] = str(log_obj.id)
        return SEND_QUEUE.enqueue(payload)
    except Exception as e1:
        logger.warning("send contact failed: %s", e1)
        _log_whatsapp(phone, f"Contact: {contact_name} ({contact_number})", message_type="contact", event=event, candidate=candidate, status="failed", error=str(e1))

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
        if payload.get("_log_id"):
            try:
                from onboarding.models import WhatsAppLog
                WhatsAppLog.objects.filter(id=payload["_log_id"]).update(
                    status="failed",
                    error_message=f"Giving up after {max_attempts} attempts"
                )
            except Exception:
                pass

# instantiate a global queue object (use same _headers function you already have)
SEND_QUEUE = WasenderQueue(API_BASE, _headers, max_retries=20, pause_after_success=0.4)
