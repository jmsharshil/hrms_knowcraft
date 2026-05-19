# bgv/services.py

import base64
import logging
import requests

from requests.auth import HTTPBasicAuth

from django.conf import settings

from .models import CandidateBGV


logger = logging.getLogger(__name__)

BASE_URL = "https://api-staging.ongrid.in"


def is_fresher(candidate):
    """
    Determine whether a candidate is a fresher (< 1 year experience).
    Returns True if fresher, False if experienced.
    """
    exp = candidate.experience_years
    if exp is None:
        return True  # treat unknown experience as fresher
    return float(exp) < 1


def _collect_documents(candidate):
    """
    Collect available documents from the JobApplicationDocument model
    linked to the candidate (JobApplication) and prepare them for
    the OnGrid API in Base64 format.

    Returns a list of dicts matching OnGrid's document schema:
      {
        "documentType": "...",
        "fileDataType": "Base64",
        "fileContent": "<base64>",
        "fileName": "filename.ext"
      }
    """
    try:
        docs = candidate.documents  # OneToOneField reverse relation
    except Exception:
        logger.info("No JobApplicationDocument found for application %s", candidate.id)
        return []

    # Map model fields → OnGrid documentType
    DOCUMENT_MAP = {
        # Personal / Identity
        "aadhaar":          "CustomDocument",
        "pan":              "CustomDocument",
        "passport":         "CustomDocument",
        "photograph":       "ProfileImage",
        "address_proof":    "CustomDocument",

        # Education
        "tenth_certificate":             "EducationalCertificates",
        "twelfth_certificate":           "EducationalCertificates",
        "graduation_certificate":        "EducationalCertificates",
        "post_graduation_certificate":   "EducationalCertificates",
        "additional_certificate_1":      "EducationalCertificates",
        "additional_certificate_2":      "EducationalCertificates",
        "additional_certificate_3":      "EducationalCertificates",

        # Experience / Employment
        "experience_letter_1":   "ExperienceLetter",
        "experience_letter_2":   "ExperienceLetter",
        "offer_letter_1":        "AppointmentLetter",
        "offer_letter_2":        "AppointmentLetter",
        "relieving_letter":      "ExperienceLetter",
        "increment_letter":      "SalarySlip",

        # Salary
        "salary_slip_1":    "SalarySlip",
        "salary_slip_2":    "SalarySlip",
        "salary_slip_3":    "SalarySlip",
        "bank_statement":   "Other",
    }

    collected = []

    for field_name, doc_type in DOCUMENT_MAP.items():
        file_field = getattr(docs, field_name, None)
        if not file_field or not file_field.name:
            continue

        try:
            file_field.open("rb")
            content = file_field.read()
            file_field.close()

            b64_content = base64.b64encode(content).decode("utf-8")

            # Extract filename from storage path
            filename = file_field.name.split("/")[-1] if "/" in file_field.name else file_field.name

            collected.append({
                "documentType": doc_type,
                "fileDataType": "Base64",
                "fileContent": b64_content,
                "fileName": filename,
            })

            logger.info("Collected document: %s (%s)", field_name, filename)

        except Exception as exc:
            logger.warning(
                "Failed to read document field '%s' for application %s: %s",
                field_name, candidate.id, exc
            )

    return collected


def initiate_bgv(candidate):
    """
    Initiate a Background Verification for a JobApplication instance.
    - Collects candidate documents from JobApplicationDocument
    - Sends them to OnGrid along with candidate details
    - Creates/updates a CandidateBGV record based on the API response
    """

    url = (
        f"{BASE_URL}/app/v1/community/"
        f"{settings.ONGRID_COMMUNITY_ID}/individuals/initiate"
    )

    # Collect documents from the application
    documents = _collect_documents(candidate)

    payload = {
        "name": candidate.candidate_name or "",
        "email": candidate.candidate_email or "",
        "phone": str(candidate.candidate_phone or ""),
        "employeeId": str(candidate.id),
        "professionId": settings.ONGRID_PROFESSION_ID,
        "hasConsent": True,
        "consentText": settings.ONGRID_CONSENT_TEXT.strip(),
        "verifications": [
            {"code": "CCRV"},   # Criminal Court Record Verification
        ],
    }

    # Add documents if any were collected
    if documents:
        payload["documents"] = documents

    data = {}
    api_success = False

    try:
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(
                settings.ONGRID_CLIENT_ID,
                settings.ONGRID_SECRET,
            ),
            headers={"Content-Type": "application/json"},
            timeout=60,  # longer timeout for document uploads
        )

        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text[:500]}

        if response.status_code in (200, 201):
            api_success = True
            logger.info(
                "OnGrid BGV initiated for %s (app=%s) with %d documents",
                candidate.candidate_name, candidate.id, len(documents),
            )
        else:
            logger.error(
                "OnGrid initiate failed – HTTP %s: %s",
                response.status_code,
                data,
            )

    except requests.RequestException as exc:
        logger.exception("OnGrid API request failed: %s", exc)
        data = {"error": str(exc)}

    # ── persist ──────────────────────────────────────────────
    bgv, created = CandidateBGV.objects.update_or_create(
        candidate=candidate,
        defaults={
            "callback_payload": data,
            "ongrid_individual_id": data.get("id", "") if api_success else "",
            "status": "initiated" if api_success else "failed",
            "remarks": "" if api_success else f"API error: {data}",
        },
    )

    return bgv