# bgv/services.py

import base64
import logging
import requests
import uuid
from requests.auth import HTTPBasicAuth

from django.conf import settings

from .models import CandidateBGV
from .utils import extract_pan_from_openai


logger = logging.getLogger(__name__)    

BASE_URL = "https://api-staging.ongrid.in/app"

# ── OnGrid Profession Master (actual list from OnGrid) ────────────
ONGRID_PROFESSIONS = {
    1:   "Security Guard",
    2:   "Maid Cleaning",
    3:   "Maid Cooking",
    4:   "Office Boy",
    5:   "Delivery Personnel",
    6:   "Hotel Staff Cleaning",
    7:   "Carpenter",
    8:   "Plumber",
    9:   "Electrician",
    10:  "Driver - Car/Jeep",
    11:  "Painter",
    12:  "Mason",
    13:  "Gardener",
    14:  "Pest Control Professional",
    15:  "Cleaning Personnel - Home",
    16:  "Accountant",
    17:  "Admin Executive",
    18:  "Admin Supervisor",
    19:  "Bartender",
    20:  "Beautician",
    21:  "Call Center / BPO Executive",
    22:  "Call Center / BPO Supervisor",
    23:  "Cashier",
    24:  "Cleaning Personnel - Offices/Stores",
    25:  "Cleaning Supervisor",
    26:  "Chef - Hotel/Restaurant",
    27:  "Chef - Home",
    28:  "CNC Machine Operator",
    29:  "Construction Site Worker",
    30:  "Construction Site Supervisor",
    31:  "Data Collection Agent",
    32:  "Data Collection Supervisor",
    33:  "Data Entry Operator",
    35:  "Driver - Truck/Bus",
    36:  "Electronics Mechanic",
    37:  "Field Executive",
    38:  "Field Supervisor",
    39:  "Fitter",
    40:  "Hair Dresser",
    41:  "Housekeeping Executive",
    42:  "Housekeeping Supervisor",
    43:  "Hotel Executive",
    44:  "Hotel Supervisor",
    45:  "Insurance Agent",
    46:  "Lathe Machine Operator",
    47:  "Loader",
    48:  "Machinist",
    49:  "Marketing Executive",
    50:  "Marketing Supervisor",
    51:  "MIS executive",
    52:  "Motor Mechanic",
    53:  "Mutual Fund Agent",
    54:  "Nurse",
    55:  "Office Assisstant/Executive",
    56:  "Office Supervisor",
    57:  "Operations Executive",
    58:  "Operations Supervisor",
    59:  "Packer",
    60:  "Pantry Personnel - Office",
    61:  "Receptionist / Front-desk executive",
    62:  "Sales personnel",
    63:  "Security Supervisor",
    64:  "Sheet Metal Mechanic",
    65:  "Steward",
    66:  "Retail Executive",
    67:  "Waiter - Hotel/Restaurant",
    68:  "Welder",
    69:  "Other",
    71:  "Surveyor",
    72:  "Computer Operator",
    73:  "Software Engineer",
    74:  "Meet And Greet Officer",
    75:  "Room Attendant",
    76:  "Housekeeping Attendant (Manual Cleaning)",
    77:  "Food & Beverage Service Steward",
    78:  "Admin Manager",
    79:  "Audit Professional",
    80:  "Auto/Car Mechanic",
    81:  "Auto/Car Service Professional",
    82:  "Beauty Professional",
    83:  "Business Development Personnel",
    84:  "CAD professional",
    85:  "Entreprenuer",
    86:  "Facility Executive",
    87:  "Facility Supervisor",
    88:  "Facility Manager",
    89:  "IT/ITES Executive",
    90:  "IT/ITES Manager",
    91:  "Lift/Elevator Operator",
    92:  "Operations Manager",
    93:  "Project Manager",
    94:  "Security Personnel",
    95:  "Self-employed",
    96:  "Wellness and Beauty Professional",
    97:  "Designer",
    98:  "Data Analyst",
    99:  "Engineer",
    100: "Consultant",
    101: "Hospital/Clinic Attendant",
    102: "Hospital/Clinic Technician",
    103: "Ward boy - Hospital/Clinic",
    104: "Helper",
    105: "Rider - 2-wheeler",
}


def _resolve_profession_id(designation_name):
    """
    Match the candidate's designation against the OnGrid profession master.
    Returns (professionId, otherProfession) tuple.

    - If an exact or keyword match is found, returns (matched_id, None).
    - If no match, returns (69, designation_name) for 'Other'.
    """
    if not designation_name:
        return 69, "Not Specified"

    designation_lower = designation_name.lower().strip()

    # 1. Try exact match first
    for pid, pname in ONGRID_PROFESSIONS.items():
        if pid == 69:
            continue
        if pname.lower() == designation_lower:
            return pid, None

    # 2. Try keyword / substring match
    for pid, pname in ONGRID_PROFESSIONS.items():
        if pid == 69:
            continue
        pname_lower = pname.lower()
        # Check if profession name is contained in designation or vice versa
        if pname_lower in designation_lower or designation_lower in pname_lower:
            return pid, None

    # 3. Try matching individual words from the profession name
    for pid, pname in ONGRID_PROFESSIONS.items():
        if pid == 69:
            continue
        pname_words = set(pname.lower().split())
        designation_words = set(designation_lower.split())
        # If any significant word matches (exclude short words)
        significant_matches = pname_words & designation_words - {"of", "the", "and", "a", "an"}
        if significant_matches:
            return pid, None

    # 4. Fallback to Other
    return 69, designation_name

# ── Verification codes to request ────────────────────────────────
def get_verification_codes(candidate):
    """
    Returns the list of verification codes based on the candidate's experience.
    """
    codes = ["PANV", "CCRV", "PAV", "LAV", "EDUV", "GDC"]
    if not is_fresher(candidate):
        codes.append("EMPV")
    return codes


def is_fresher(candidate):
    """
    Determine whether a candidate is a fresher (< 1 year experience).
    Returns True if fresher, False if experienced.
    """
    exp = candidate.experience_years
    if exp is None:
        return True  # treat unknown experience as fresher
    return float(exp) < 1


def _get_auth():
    """Return HTTPBasicAuth using OnGrid credentials from settings."""
    return HTTPBasicAuth(
        settings.ONGRID_CLIENT_ID,
        settings.ONGRID_SECRET,
    )


def _ongrid_request(method, url, json_payload=None, timeout=60):
    """
    Common helper for making authenticated requests to the OnGrid API.
    Returns (response_data_dict, http_status_code, success_bool).
    """
    try:
        response = requests.request(
            method,
            url,
            json=json_payload,
            auth=_get_auth(),
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )

        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text[:500]}

        success = response.status_code in (200, 201)

        if not success:
            logger.error(
                "OnGrid API %s %s failed – HTTP %s: %s",
                method, url, response.status_code, data,
            )

        return data, response.status_code, success

    except requests.RequestException as exc:
        logger.exception("OnGrid API request failed: %s", exc)
        return {"error": str(exc)}, 0, False

def _build_verifications(candidate):
    codes = get_verification_codes(candidate)
    verifications = []

    pan_number = None
    try:
        pan_file = getattr(candidate.documents, "pan", None)
        print(pan_file,"pan_file--------------------")
        if pan_file:
            pan_data = extract_pan_from_openai(pan_file)
            print(pan_data,"pan_data--------------------")
            if pan_data:
                pan_number = pan_data.get("pan_number")
                print(pan_number,"pan_number--------------------")
    except Exception:
        logger.exception("PAN extraction failed")

    for code in codes:
        item = {
            "code": code,
            "key": str(uuid.uuid4()),  # ✅ REQUIRED UNIQUE KEY
            "data": {}
        }

        if code == "PANV" and pan_number:
            print(pan_number,"pan_number--------------------in panv")
            item["data"] = {
                "panNumber": pan_number
            }

        verifications.append(item)

    return verifications

def _collect_documents(candidate):
    """
    Collect documents as URL-based payload (NOT base64).
    """

    try:
        docs = candidate.documents
    except Exception:
        logger.info("No documents found for %s", candidate.id)
        return []

    # Map model fields → OnGrid documentType
    DOCUMENT_MAP = {
        "aadhaar": "CustomDocument",
        "pan": "PANCard",
        "passport": "Passport",
        "photograph": "ProfileImage",
        "address_proof": "AddressProof",
        "tenth_certificate": "EducationalCertificates",
        "twelfth_certificate": "EducationalCertificates",
        "graduation_certificate": "EducationalCertificates",
        "post_graduation_certificate": "EducationalCertificates",
        "experience_letter_1": "ExperienceLetter",
        "experience_letter_2": "ExperienceLetter",
        "salary_slip_1": "SalarySlip",
        "salary_slip_2": "SalarySlip",
        "bank_statement": "FinancialDocument",
    }

    collected = []

    for field_name, doc_type in DOCUMENT_MAP.items():
        file_field = getattr(docs, field_name, None)
        print(file_field,"file",field_name,"field_name",docs.id,"docs.id")
        if not file_field or not file_field.name:
            continue

        try:
            collected.append({
                "documentType": doc_type,
                "fileDataType": "URL",
                "servingUrl": file_field.url,
                "fileName": file_field.name.split("/")[-1],
            })

            print("Collected document: %s (%s)", field_name, file_field.name)

        except Exception as exc:
            logger.exception("Document error %s: %s", field_name, exc)

    return collected


def _build_payload(candidate, extra_data=None):
    """
    Build the OnGrid onboard/initiate payload from a JobApplication instance.

    extra_data (dict) can contain additional fields:
      - fathersName, gender, dob, city
      - permanentAddress (dict with line1, line2, city, state, pincode, country, fullAddress)
      - currentAddress (string)
      - verifications (list of verification code dicts)
    """
    extra = extra_data or {}

    payload = {
        "name": candidate.candidate_name or "",
        "email": candidate.candidate_email or "",
        "phone": str(candidate.candidate_phone or ""),
        "employeeId": str(candidate.id),
        "hasConsent": True,
        "consentText": settings.ONGRID_CONSENT_TEXT.strip(),
        "deduplicationKeys": [str(candidate.id)],
        # "deduplicationKeys": [
        #     {
        #         "keyName": "candidateId",
        #         "keyValue": str(candidate.id)
        #     }
        # ],
        # "uid": str(candidate.id)  # safer idempotency
    }

    # profession
    profession = ""
    if getattr(candidate, "job", None):
        if getattr(candidate.job, "designation", None):
            profession = candidate.job.designation.name
        elif getattr(candidate.job, "job_title", None):
            profession = candidate.job.job_title

    # Resolve profession from OnGrid master list
    prof_id, other_prof = _resolve_profession_id(profession)
    payload["professionId"] = str(prof_id)

    if other_prof:
        payload["otherProfession"] = other_prof

    # optional fields
    if extra.get("fathersName"):
        payload["fathersName"] = extra["fathersName"]

    if extra.get("gender"):
        payload["gender"] = extra["gender"]

    if extra.get("dob"):
        payload["dob"] = extra["dob"]

    if extra.get("city"):
        payload["city"] = extra["city"]
    elif candidate.location:
        payload["city"] = candidate.location

    if extra.get("permanentAddress"):
        payload["permanentAddress"] = extra["permanentAddress"]

    if extra.get("currentAddress"):
        payload["currentAddress"] = extra["currentAddress"]

    # ✅ FIXED VERIFICATIONS
    payload["verifications"] = _build_verifications(candidate)

    # ✅ FIXED DOCUMENTS (URL ONLY)
    documents = _collect_documents(candidate)
    if documents:
        payload["documents"] = documents

    return payload, len(documents)

def initiate_bgv(candidate, extra_data=None):
    """
    Initiate a Background Verification for a JobApplication instance.
    Uses the combined "Onboard and Initiate" endpoint.

    - Collects candidate details and documents
    - Sends them to OnGrid along with candidate details
    - Creates/updates a CandidateBGV record based on the API response

    extra_data (dict): Optional additional fields for the API payload
      (fathersName, gender, dob, city, permanentAddress, currentAddress, verifications)
    """

    url = (
        f"{BASE_URL}/v1/community/"
        f"{settings.ONGRID_COMMUNITY_ID}/individuals/initiate"
    )

    payload, doc_count = _build_payload(candidate, extra_data)

    print(payload,"payload")

    data, status_code, api_success = _ongrid_request("POST", url, payload)

    if api_success:
        logger.info(
            "OnGrid BGV initiated for %s (app=%s) with %d documents",
            candidate.candidate_name, candidate.id, doc_count,
        )

    # ── persist ──────────────────────────────────────────────
    bgv, created = CandidateBGV.objects.update_or_create(
        candidate=candidate,
        defaults={
            "callback_payload": data,
            "ongrid_individual_id": data.get("id", "") if api_success else "",
            "status": "initiated" if api_success else "failed",
            "remarks": "" if api_success else f"API error (HTTP {status_code}): {data}",
            "is_fresher": is_fresher(candidate),
        },
    )
    print(bgv)

    return bgv


def onboard_individual(candidate, extra_data=None):
    """
    Step 1 of the two-step flow:
    Onboard an individual into the OnGrid community WITHOUT initiating verifications.
    Returns the individual record (or None on failure).

    Use this when you want to register the candidate first and initiate
    verifications later (e.g., after collecting additional data).
    """

    url = (
        f"{BASE_URL}/v1/community/"
        f"{settings.ONGRID_COMMUNITY_ID}/individuals"
    )

    extra = extra_data or {}

    payload = {
        "name": candidate.candidate_name or "",
        "email": candidate.candidate_email or "",
        "phone": str(candidate.candidate_phone or ""),
        "employeeId": str(candidate.id),
        "hasConsent": True,
        "consentText": settings.ONGRID_CONSENT_TEXT.strip(),
    }

    profession = ""
    if getattr(candidate, "job", None):
        if getattr(candidate.job, "designation", None):
            profession = candidate.job.designation.name
        elif getattr(candidate.job, "job_title", None):
            profession = candidate.job.job_title

    # Resolve profession from OnGrid master list
    prof_id, other_prof = _resolve_profession_id(profession)
    payload["professionId"] = prof_id
    if other_prof:
        payload["otherProfession"] = other_prof

    if extra.get("fathersName"):
        payload["fathersName"] = extra["fathersName"]
    if extra.get("gender"):
        payload["gender"] = extra["gender"]
    if extra.get("dob"):
        payload["dob"] = extra["dob"]
    if extra.get("city"):
        payload["city"] = extra["city"]
    elif candidate.location:
        payload["city"] = candidate.location
    if extra.get("permanentAddress"):
        payload["permanentAddress"] = extra["permanentAddress"]
    if extra.get("currentAddress"):
        payload["currentAddress"] = extra["currentAddress"]

    # Collect and attach documents
    documents = _collect_documents(candidate)
    if documents:
        payload["documents"] = documents

    data, status_code, api_success = _ongrid_request("POST", url, payload)

    if api_success:
        individual_id = data.get("id", "")
        logger.info(
            "OnGrid individual onboarded: %s (individualId=%s)",
            candidate.candidate_name, individual_id,
        )

        bgv, _ = CandidateBGV.objects.update_or_create(
            candidate=candidate,
            defaults={
                "callback_payload": data,
                "ongrid_individual_id": individual_id,
                "status": "pending_schedule",  # onboarded but verifications not started
                "is_fresher": is_fresher(candidate),
                "remarks": "Individual onboarded, verifications not yet initiated.",
            },
        )
        return bgv

    logger.error(
        "Failed to onboard individual %s: HTTP %s – %s",
        candidate.candidate_name, status_code, data,
    )
    return None


def trigger_verifications(individual_id, verification_codes=None):
    """
    Step 2 of the two-step flow:
    Trigger verifications for an already-onboarded individual.

    individual_id: The OnGrid individualId returned from onboard_individual().
    verification_codes: List of code strings, e.g. ["CCRV", "PANV"].
                        Dynamically fetched if not provided.
    """
    if verification_codes is None:
        try:
            bgv = CandidateBGV.objects.get(ongrid_individual_id=individual_id)
            codes = get_verification_codes(bgv.candidate)
        except CandidateBGV.DoesNotExist:
            codes = ["PANV", "AADHAAR", "CCRV", "PAV", "LAV", "EDUV", "GDC"]
    else:
        codes = verification_codes

    url = (
        f"{BASE_URL}/v1/community/"
        f"{settings.ONGRID_COMMUNITY_ID}/individuals/{individual_id}"
        f"/verifications/initiate"
    )

    payload = {
        "verifications": [{"code": c} for c in codes],
    }

    data, status_code, api_success = _ongrid_request("POST", url, payload)

    if api_success:
        logger.info(
            "Verifications %s initiated for individual %s",
            codes, individual_id,
        )

        # Update the BGV record status
        try:
            bgv = CandidateBGV.objects.get(ongrid_individual_id=individual_id)
            bgv.status = "initiated"
            bgv.callback_payload = data
            bgv.remarks = f"Verifications initiated: {', '.join(codes)}"
            bgv.save(update_fields=["status", "callback_payload", "remarks"])
        except CandidateBGV.DoesNotExist:
            logger.warning(
                "No BGV record found for individual %s after triggering verifications",
                individual_id,
            )

    return data, api_success


def get_individual_status(individual_id):
    """
    Fetch the current status/details of an individual from OnGrid.
    Useful for polling verification progress.
    """
    url = (
        f"{BASE_URL}/v1/community/"
        f"{settings.ONGRID_COMMUNITY_ID}/individuals/{individual_id}"
    )

    data, status_code, success = _ongrid_request("GET", url)
    return data if success else None


def get_verification_report(individual_id):
    """
    Fetch the verification report/results for an individual.
    """
    url = (
        f"{BASE_URL}/v1/community/"
        f"{settings.ONGRID_COMMUNITY_ID}/individuals/{individual_id}"
        f"/verifications"
    )

    data, status_code, success = _ongrid_request("GET", url)
    return data if success else None