# onboarding/utils/opensign_service.py
import base64
import json
import logging
import requests

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpRequest
from django.core.cache import cache
from django.utils import timezone

from .pdf_maker import generate_offer_letter
from onboarding.models import Candidate

logger = logging.getLogger(__name__)

OPENSIGN_API_BASE = getattr(settings, "OPENSIGN_API_BASE_URL", None)
OPENSIGN_API_TOKEN = getattr(settings, "OPENSIGN_API_TOKEN", None)
OPENSIGN_CREATEDOCUMENT_ENDPOINT = getattr(
    settings, "OPENSIGN_CREATEDOCUMENT_ENDPOINT", "/createdocument"
)
# Full URL used for posting
# Example: OPENSIGN_API_BASE = "https://opensign.example.com/api/v1"
# Full URL used -> "https://opensign.example.com/api/v1/createdocument"


def _get_opensign_url():
    if not OPENSIGN_API_BASE:
        raise RuntimeError("OPENSIGN_API_BASE_URL not configured in settings")
    return OPENSIGN_API_BASE


def send_to_opensign_and_get_link(candidate: Candidate) -> tuple[str, str]:
    """
    Sends offer letter PDF to OpenSign (selfsign API)
    and returns (signing_url, form_id).
    """

    filename, pdf_bytes, _mimetype = generate_offer_letter(candidate)
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    # Correct OpenSign SelfSign endpoint
    url = "https://sandbox.opensignlabs.com/api/v1.1/selfsign"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-token": settings.OPENSIGN_API_TOKEN,   # MUST be x-api-token
    }

    # OpenSign selfsign accepts ONLY 1 signer block, not a list
    payload = {
        "file": pdf_base64,
        "title": f"Offer Letter – {candidate.name}",
        "note": "Please sign your offer letter",
        "description": "Digital offer letter signing",
        "timeToCompleteDays": 7,

        "signer": {
            "role": "candidate",
            "email": candidate.email,
            "name": candidate.name,
            "phone": "",      # optional
            "company": "",    # optional
            "job_title": "",  # optional
            "widgets": [
                {
                    "type": "signature",
                    "page": 1,
                    "x": 244,
                    "y": 71,
                    "w": 150,
                    "h": 50
                }
            ]
        },

        "folderId": "",
        "send_email": True,
        "email_subject": "{{sender_name}} has requested you to sign the offer letter",
        "email_body": "<p>Please sign your offer letter:</p><p><a href='{{signing_url}}'>Sign here</a></p>",

        "enableTour": False,
        "redirect_url": "",
        "sender_name": "HR Team",
        "sender_email": "no-reply@yourcompany.com",
        "merge_certificate": False
    }

    # Make request
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    signing_url = data.get("signing_url") or data.get("signurl")
    objectId = data.get("id") or data.get("objectId")

    if not signing_url or not objectId:
        raise RuntimeError(f"Bad OpenSign response: {data}")

    # store mapping for webhook
    cache.set(f"opensign_form_{objectId}", str(candidate.id), timeout=24 * 3600)

    return signing_url, objectId


# -----------------------
# Webhook endpoint
# -----------------------
@csrf_exempt
def opensign_webhook(request: HttpRequest):
    """
    Webhook that OpenSign calls when document status changes.
    It will look up candidate from cache (form_id -> candidate_id) and trigger the automation_engine.
    NOTE: We import automation_engine locally to avoid circular imports.
    """
    try:
        body = json.loads(request.body)
        print("in webhook body",body)
    except Exception:
        logger.exception("Invalid JSON on OpenSign webhook")
        return JsonResponse({"error": "invalid json"}, status=400)

    objectId = body.get("objectId") or body.get("id") or body.get("document_id")
    status = body.get("event")  # e.g., "completed"
    signed_url = body.get("signed_url") or body.get("file_url") or body.get("signed_file")

    if not objectId:
        logger.error("OpenSign webhook missing objectId: payload=%s", body)
        return JsonResponse({"error": "missing objectId"}, status=400)

    cache_key = f"opensign_form_{objectId}"
    candidate_id = cache.get(cache_key)
    if not candidate_id:
        logger.warning("OpenSign webhook: no mapping for form_id=%s", objectId)
        # Optionally: attempt to search candidates by other means, or log for manual reconciliation
        return JsonResponse({"error": "not found"}, status=404)

    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        logger.exception("Candidate not found for id from cache: %s (form_id=%s)", candidate_id, objectId)
        return JsonResponse({"error": "candidate not found"}, status=404)

    # IMPORTANT: capture old stage BEFORE calling automation_engine
    old_stage = candidate.stage

    # When signing completed, we want to move candidate to next stage (offer_accepted)
    try:
        # Local import to avoid circular import at module import time
        from onboarding.utils.engine import automation_engine
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Could not import automation_engine inside webhook: %s", exc)
        return JsonResponse({"error": "server error"}, status=500)

    if status == "completed":
        logger.info("OpenSign: completed for form_id=%s candidate=%s", objectId, candidate.email)
        # Do NOT set candidate.stage directly — let automation_engine validate & set it.
        ok, reason = automation_engine(candidate, old_stage, "offer_accepted")
        if not ok:
            logger.error("automation_engine rejected transition: %s -> %s (reason=%s)", old_stage, "offer_accepted", reason)
            return JsonResponse({"error": "invalid transition", "reason": reason}, status=400)

        # Optionally store signed URL into cache or attach to some audit log (not model)
        if signed_url:
            cache.set(f"opensign_signed_url_{objectId}", signed_url, timeout=7 * 24 * 3600)

        # Remove the temporary mapping if you like
        cache.delete(cache_key)

    else:
        # you may want to handle other statuses e.g., "signed_by_first", "cancelled", etc.
        logger.info("OpenSign webhook for form_id=%s status=%s", objectId, status)

    return JsonResponse({"ok": True})
