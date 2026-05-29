# bgv/services.py

import base64
import logging
import requests
import uuid
from requests.auth import HTTPBasicAuth
from datetime import datetime
from django.conf import settings

from .models import CandidateBGV
from .utils import extract_pan_smart,extract_aadhaar_smart,extract_candidate_kyc_details


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
# Human-readable names for each verification code
VERIFICATION_NAMES = {
    "PANV":   "PAN Verification",
    "AV":     "Aadhaar Verification",
    "CCRV":   "Court & Criminal Record Verification",
    "PAV":    "Permanent Address Verification",
    "LAV":    "Current/Local Address Verification",
    "EDUV":   "Education Verification",
    "GDC":    "Global Database Check",
    "EMPV":   "Employment Verification",
    "DLV":    "Driving Licence Verification",
    "BAV":    "Bank Account Verification",
    "CVV":    "CV Verification",
    "PAPV":   "Passport Verification",
    "PANV":   "PAN Verification",
    "PADV":   "PAN Address Verification",
    "VIDV":   "Voter ID Verification",
    "IPAV":   "IP Address Verification",
    "LAPV":   "Latest Address Verification",
    "LADV":   "Latest Address Document Verification",
    "PCC":    "Police Clearance Certificate",
    "PPV":    "Passport Police Verification",
    "PRC":    "Professional Reference Check",
    "DRG":    "Drug Test",
    "FMC":    "Financial & Medical Check",
    "SMC":    "Social Media Check",
    "EHC":    "Executive Health Check",
    "PVLF":   "PF Verification",
    "NSORC":  "National Sex Offender Registry Check",
    "OFACC":  "OFAC Check",
    "IAF":    "Identity & Address Fraud Check",
    "XAV":    "Extended Address Verification",
    "EFIRC":  "EPFO/ESIC Fraud & Identity Record Check",
    "ICAV":   "Income Certificate & Address Verification",
    "EREF":   "Employee Reference Check",
    "BGSV":   "Background Score Verification",
    "CC":     "Credit Check",
}


def get_verification_names(codes):
    """
    Given a list of verification codes, return a list of dicts with
    both code and human-readable name.
    e.g. [{"code": "PANV", "name": "PAN Verification"}, ...]
    """
    return [
        {"code": c, "name": VERIFICATION_NAMES.get(c, c)}
        for c in codes
    ]


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

def _build_verifications(candidate, extra_data=None):
    extra = extra_data or {}
    verifications = []

    for code in get_verification_codes(candidate):

        # ---------------- PANV ----------------
        if code == "PANV":
            pan_file = getattr(candidate.documents, "pan", None)
            pan_data = extract_pan_smart(pan_file)

            if not pan_data or not pan_data.get("pan_number"):
                continue

            verifications.append({
                "code": code,
                "key": str(uuid.uuid4()),
                "data": {
                    "documentUID": pan_data["pan_number"]
                }
            })

        # ---------------- EDUV ----------------
        elif code == "EDUV":
            if not extra.get("institute_name"):
                continue

            level = extra.get("level", extra.get("education_level", "GRADUATE")).upper()
            if level not in ["NO_EDUCATION","LESS_THEN_FIFTH_STD","FIFTH_STD","EIGHT_STD","TENTH_STD","TWELFTH_STD","DIPLOMA","GRADUATE","MASTERS","PHD","POST_DOC","POST_GRADUATE_DIPLOMA"]:
                logger.error(f"Invalid education level: {level}")
                continue

            education_document = {
                "nameAsPerDocument": candidate.candidate_name,
                "level": level,
                "nameOfInstitute": extra.get("institute_name", ""),
                "documents": _get_education_documents(candidate),
            }

            if extra.get("name_of_board_university"):
                education_document["nameOfBoardUniversity"] = extra.get("name_of_board_university")

            yop = extra.get("year_of_passing")
            if yop:
                education_document["yearOfPassing"] = str(yop)[:4]

            if extra.get("issue_date"):
                education_document["issueDate"] = normalize_date(extra.get("issue_date"))
            if extra.get("registration_number"):
                education_document["registrationNumber"] = extra.get("registration_number")
            if extra.get("degree"):
                education_document["degree"] = extra.get("degree")
            if extra.get("field_of_study"):
                education_document["fieldOfStudy"] = extra.get("field_of_study")
            if extra.get("duration_in_months"):
                try:
                    education_document["durationInMonths"] = int(extra.get("duration_in_months"))
                except ValueError:
                    pass
            if extra.get("grade"):
                education_document["grade"] = extra.get("grade")

            verifications.append({
                "code": code,
                "key": str(uuid.uuid4()),
                "data": {
                    "educationDocument": education_document
                }
            })

        # ---------------- PAV ----------------
        elif code == "PAV":
            perm = extra.get("permanentAddress") or {}

            if not perm.get("line1"):
                continue

            verifications.append({
                "code": code,
                "key": str(uuid.uuid4()),
                "data": {
                    "permanentAddress": perm
                }
            })

        # ---------------- LAV ----------------
        elif code == "LAV":
            current_address = (
                extra.get("currentAddress")
                or candidate.location
            )

            if not current_address:
                continue

            verifications.append({
                "code": code,
                "key": str(uuid.uuid4()),
                "data": {
                    "currentAddress": current_address
                }
            })

        elif code == "EMPV":
            emp_record = {
                "nameAsPerEmployerRecords": candidate.candidate_name,
                "employeeId": str(candidate.id),
                "employerName": extra.get("employer_name", ""),
                "lastDesignation": extra.get("designation", ""),
                "documents": _get_employment_documents(candidate),
            }
            if extra.get("joining_date"):
                emp_record["joiningDate"] = normalize_date(extra.get("joining_date"))

            if extra.get("last_working_date"):
                emp_record["lastWorkingDate"] = normalize_date(extra.get("last_working_date"))

            if extra.get("issue_date"):
                education_document["issueDate"] = normalize_date(extra.get("issue_date"))
            verifications.append({
                "code": code,
                "key": str(uuid.uuid4()),
                "data": {
                    "employmentRecord": emp_record
                }
            })

        # ---------------- SIMPLE CHECKS ----------------
        else:
            verifications.append({
                "code": code,
                "key": str(uuid.uuid4()),
            })

    return verifications

def _build_document(file_field, document_type):

    if not file_field:
        return None

    return {
        "documentType": document_type,
        "fileDataType": "Url",
        "fileName": file_field.name.split("/")[-1],
        "fileContent": file_field.url.split("?")[0] if "?" in file_field.url else file_field.url,
    }

def _get_education_documents(candidate):

    docs = []

    certs = [
        candidate.documents.tenth_certificate,
        candidate.documents.twelfth_certificate,
        candidate.documents.graduation_certificate,
        candidate.documents.post_graduation_certificate,
    ]

    for cert in certs:
        if cert:
            docs.append(
                _build_document(cert, "EducationalCertificates")
            )

    return docs

def _get_employment_documents(candidate):

    docs = []

    mappings = [
        (candidate.documents.experience_letter_1, "ExperienceLetter"),
        (candidate.documents.experience_letter_2, "ExperienceLetter"),
        (candidate.documents.salary_slip_1, "SalarySlip"),
        (candidate.documents.salary_slip_2, "SalarySlip"),
    ]

    for file_obj, doc_type in mappings:
        if file_obj:
            docs.append(
                _build_document(file_obj, doc_type)
            )

    return docs

# def _collect_documents(candidate):
#     """
#     Collect documents as URL-based payload (NOT base64).
#     """

#     try:
#         docs = candidate.documents
#     except Exception:
#         logger.info("No documents found for %s", candidate.id)
#         return []

#     # Map model fields → OnGrid documentType
#     DOCUMENT_MAP = {
#         "aadhaar": "CustomDocument",
#         "pan": "PANCard",
#         "passport": "Passport",
#         "photograph": "ProfileImage",
#         "address_proof": "AddressProof",
#         "tenth_certificate": "EducationalCertificates",
#         "twelfth_certificate": "EducationalCertificates",
#         "graduation_certificate": "EducationalCertificates",
#         "post_graduation_certificate": "EducationalCertificates",
#         "experience_letter_1": "ExperienceLetter",
#         "experience_letter_2": "ExperienceLetter",
#         "salary_slip_1": "SalarySlip",
#         "salary_slip_2": "SalarySlip",
#         "bank_statement": "FinancialDocument",
#     }

#     collected = []

#     for field_name, doc_type in DOCUMENT_MAP.items():
#         file_field = getattr(docs, field_name, None)
#         print(file_field,"file",field_name,"field_name",docs.id,"docs.id")
#         if not file_field or not file_field.name:
#             continue

#         try:
#             collected.append({
#                 "documentType": doc_type,
#                 "fileDataType": "URL",
#                 "servingUrl": file_field.url,
#                 "fileName": file_field.name.split("/")[-1],
#             })

#             print("Collected document: %s (%s)", field_name, file_field.name)

#         except Exception as exc:
#             logger.exception("Document error %s: %s", field_name, exc)

#     return collected

def normalize_date(date_value):
    """
    Convert multiple date formats into YYYY-MM-DD.
    Returns None if invalid.
    """

    if not date_value:
        return None

    if isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d")

    date_value = str(date_value).strip()

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None
    
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
        "employeeId": str(candidate.id),
        "hasConsent": True,
        "consentText": settings.ONGRID_CONSENT_TEXT.strip(),
        "deduplicationKeys": [str(candidate.id)],
        "joiningDate": str(candidate.joining_date),
        # "uid": str(candidate.id)  # safer idempotency
    }

    raw_phone = str(candidate.candidate_phone or "")

    # Strip country code if present and set separately
    if raw_phone.startswith("+91"):
        payload["phone"] = raw_phone[3:]          # "8401611072"
        # payload["phoneCountryCode"] = "+91"
    elif raw_phone.startswith("91") and len(raw_phone) == 12:
        payload["phone"] = raw_phone[2:]          # "8401611072"
        # payload["phoneCountryCode"] = "+91"
    else:
        payload["phone"] = raw_phone
        # payload["phoneCountryCode"] = "+91"
      
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
    # kyc = extract_candidate_kyc_details(candidate)
    # print(kyc,"kyc")

    # if kyc.get("father_name"):
    #     payload["fathersName"] = kyc["father_name"]

    # GENDER_MAP = {
    #     "male":   "M",
    #     "female": "F",
    #     "transgender": "T",
    #     "other": "O",
    # }

    # if kyc.get("gender"):
    #     payload["gender"] = GENDER_MAP.get(kyc["gender"].lower(), "U")

    # if kyc.get("dob"):
    #     raw_dob = kyc["dob"]
    #     try:
    #         from datetime import datetime
    #         # Handle dd/MM/yyyy → yyyy-MM-dd
    #         payload["dob"] = datetime.strptime(raw_dob, "%d/%m/%Y").strftime("%Y-%m-%d")
    #     except ValueError:
    #         payload["dob"] = raw_dob

    current_address = extra.get("currentAddress") or candidate.location
    if current_address:
        payload["currentAddress"] = current_address

    permanent_address = extra.get("permanentAddress")
    if extra.get("city"):
        payload["city"] = extra["city"]
    elif not extra_data.get("city") and permanent_address and permanent_address.get("city"):
        extra_data["city"] = permanent_address.get("city")
    elif candidate.location:
        payload["city"] = candidate.location

    if permanent_address:
        payload["permanentAddress"] = permanent_address

    if extra.get("gender"):
        payload["gender"] = extra["gender"]
    
    raw_dob = extra.get("dob") or getattr(candidate, "dob", None)
    if raw_dob:
        payload["dob"] = normalize_date(raw_dob)

    if extra.get("fathersName"):
        payload["fathersName"] = extra["fathersName"]

    if extra.get('adhar_id'):
        payload['uid'] = extra['adhar_id']

    # ✅ FIXED VERIFICATIONS
    payload["verifications"] = _build_verifications(candidate,extra_data)

    return payload

def initiate_bgv(candidate, extra_data=None):
    """
    Initiate a Background Verification for a JobApplication instance.
    Uses the combined "Onboard and Initiate" endpoint.

    - Collects candidate details and documents
    - Sends them to OnGrid along with candidate details
    - Creates/updates a CandidateBGV record based on the API response
    - On re-initiation (OnGrid 409 / already-exists), recovers the
      existing individualId instead of marking the record as failed.

    extra_data (dict): Optional additional fields for the API payload
      (fathersName, gender, dob, city, permanentAddress, currentAddress, verifications)
    """

    url = (
        f"{BASE_URL}/v1/community/"
        f"{settings.ONGRID_COMMUNITY_ID}/individuals/initiate"
    )

    payload = _build_payload(candidate, extra_data)

    print(payload, "payload")

    data, status_code, api_success = _ongrid_request("POST", url, payload)
    print(data, "data")
    print(status_code, "status_code")
    print(api_success, "api_success")

    if api_success:
        logger.info(
            "OnGrid BGV initiated for %s (app=%s)",
            candidate.candidate_name, candidate.id
        )

    # ── Detect re-initiation (already-existing individual) ────────
    # OnGrid returns non-2xx with the existing individualId in the body.
    # Common shapes:
    #   { "individualId": 123456, "message": "..." }
    #   { "individual": { "id": 123456 }, ... }
    individual_id = None

    if api_success:
        individual = data.get("individual", {})
        if individual:
            individual_id = individual.get("id")
        if not individual_id:
            individual_id = data.get("individualId") or data.get("id")
    else:
        # Try to recover existing individualId from error body
        recovered_id = (
            data.get("individualId")
            or data.get("id")
            or (data.get("individual") or {}).get("id")
        )
        if recovered_id:
            individual_id = recovered_id
            logger.warning(
                "OnGrid returned HTTP %s for %s – recovered existing individualId=%s",
                status_code, candidate.candidate_name, individual_id,
            )

    # ── Determine BGV status ──────────────────────────────────────
    if api_success:
        bgv_status = "in_progress"
        remarks = ""
    elif individual_id:
        # Individual already existed; treat as in_progress
        bgv_status = "in_progress"
        remarks = f"Re-initiation: recovered existing OnGrid individualId={individual_id}"
    else:
        bgv_status = "failed"
        remarks = f"API error (HTTP {status_code}): {data}"

    # ── Persist ───────────────────────────────────────────────────
    bgv, created = CandidateBGV.objects.update_or_create(
        candidate=candidate,
        defaults={
            "callback_payload": data,
            "raw_initiation_payload": payload,
            "ongrid_individual_id": individual_id if individual_id else None,
            "status": bgv_status,
            "remarks": remarks,
            "is_fresher": is_fresher(candidate),
        },
    )
    print(bgv)

    # ── Attach enriched verification names for the response ───────
    codes = get_verification_codes(candidate)
    bgv._verification_names = get_verification_names(codes)

    return bgv


def send_notification_for_bgv(candidate):
    """
    Send BGV initiation link directly to the candidate to fill their details
    and initiate the BGV process.
    """
    from onboarding.utils.sender import send_email, send_text
    
    FRONTEND_URL = getattr(settings, "FRONTEND_URL", "")
    # Link for candidate to fill BGV details
    form_link = f"{FRONTEND_URL}/bgv-form/{candidate.id}" 

    email_subject = "Background Verification - Action Required"
    
    # Plain text version
    email_text = (
        f"Dear {candidate.candidate_name},\n\n"
        f"Congratulations on your offer! Please fill out the required details to initiate your Background Verification (BGV) process.\n\n"
        f"You can access the form here: {form_link}\n\n"
        f"Please complete this at your earliest convenience to ensure a smooth onboarding process.\n\n"
        f"Thank you,\nHR Team\nKnowcraft Analytics Private Limited."
    )
    
    # HTML template version
    html_template = f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <!-- Separator -->
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Background Verification Required</h2>
                                
                                <p style="margin:0 0 16px 0;">Dear <strong>{candidate.candidate_name}</strong>,</p>
                                
                                <p style="margin:0 0 20px 0;">
                                    Congratulations on your offer! We're excited to have you join our team.
                                </p>
                                
                                <p style="margin:0 0 20px 0;">
                                    As part of the onboarding process, we need to complete your <strong>Background Verification (BGV)</strong>. 
                                    Please fill out the required details by clicking the button below:
                                </p>
                                
                                <!-- Action Button -->
                                <p style="margin:32px 0 30px 0;text-align:center;">
                                    <a href="{form_link}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:8px;font-weight:600;font-size:16px;display:inline-block;">
                                        Complete BGV Form
                                    </a>
                                </p>
                                
                                <p style="margin:0 0 20px 0;">
                                    Please complete this at your earliest convenience to ensure a smooth onboarding process.
                                </p>
                                
                                <p style="margin:20px 0 6px 0;color:#555555;">Thank you,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">HR Team</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # sms_text = (
    #     f"Dear {candidate.candidate_name}, please fill out the required details to initiate your "
    #     f"Background Verification (BGV) process.\n Link: {form_link}"
    # )

    # Send directly to candidate
    try:
        if candidate.candidate_email:
            send_email(
                to=candidate.candidate_email, 
                subject=email_subject, 
                text=email_text,
                template=html_template
            )
            logger.info("BGV initiation link sent to candidate %s (%s)", candidate.candidate_name, candidate.candidate_email)
        
        if candidate.candidate_phone:
            send_text(to=str(candidate.candidate_phone), text=email_text)
            logger.info("BGV initiation SMS sent to candidate %s (%s)", candidate.candidate_name, candidate.candidate_phone)
    except Exception as e:
        logger.error("Failed to send BGV notification to candidate %s: %s", candidate.candidate_name, e)

    # ── persist ──────────────────────────────────────────────
    bgv, created = CandidateBGV.objects.update_or_create(
        candidate=candidate,
        defaults={
            "status": "pending_data",
            "remarks": "BGV initiation link sent to candidate",
            "is_fresher": is_fresher(candidate),
        },
    )
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
    # documents = _collect_documents(candidate)
    # if documents:
    #     payload["documents"] = documents

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
            bgv.raw_initiation_payload = payload
            bgv.remarks = f"Verifications initiated: {', '.join(codes)}"
            bgv.save(update_fields=["status", "callback_payload", "raw_initiation_payload", "remarks"])
        except CandidateBGV.DoesNotExist:
            logger.warning(
                "No BGV record found for individual %s after triggering verifications",
                individual_id,
            )

    return data, api_success


def get_individual_status(individual_id, bgv_instance=None):
    """
    Fetch the current status/details of an individual from OnGrid.
    Useful for polling verification progress.

    If bgv_instance (CandidateBGV) is provided, the response is persisted
    into the record (ongrid_status, report_url, status).
    """
    url = (
        f"{BASE_URL}/v1/individual/{individual_id}/verificationstatus"
    )

    data, status_code, success = _ongrid_request("GET", url)

    if success and bgv_instance is not None:
        _persist_ongrid_status(bgv_instance, data)

    return data if success else None


def _persist_ongrid_status(bgv, status_data):
    """
    Save the OnGrid status payload into the CandidateBGV record.
    Also updates report_url from consolidatedReportUrl if present,
    and maps overallStatus to a local status value.
    Saves only if a status field has changed.
    """
    OVERALL_STATUS_MAP = {
        "InProgress":   "in_progress",
        "Completed":    "completed",
        "Clear":        "clear",
        "Failed":       "failed",
        "Closed":       "closed",
        "Cancelled":    "cancelled",
        "Verified":     "verified",
        "Discrepancy":  "discrepancy",
    }
    
    VERIFICATION_STATUS_FIELDS = {
        "AV": "av_status",
        "BAV": "bav_status",
        "CC": "cc_status",
        "CCRV": "ccrv_status",
        "CVV": "cvv_status",
        "DLV": "dlv_status",
        "DRG": "drg_status",
        "EDUV": "eduv_status",
        "EFIRC": "efirc_status",
        "EHC": "ehc_status",
        "EMPV": "empv_status",
        "ERef": "eref_status",
        "FMC": "fmc_status",
        "GDC": "gdc_status",
        "IAF": "iaf_status",
        "ICAV": "icav_status",
        "IPAV": "ipav_status",
        "LADV": "ladv_status",
        "LAPV": "lapv_status",
        "LAV": "lav_status",
        "NSORC": "nsorc_status",
        "OFACC": "ofacc_status",
        "PADV": "padv_status",
        "PANV": "panv_status",
        "PAPV": "papv_status",
        "PAV": "pav_status",
        "PCC": "pcc_status",
        "PPV": "ppv_status",
        "PRC": "prc_status",
        "PVLF": "pvlf_status",
        "SMC": "smc_status",
        "VIDV": "vidv_status",
        "XAV": "xav_status",
    }

    update_fields = set()
    changed = False

    # Check overall status
    overall = status_data.get("overallStatus")
    if overall:
        mapped = OVERALL_STATUS_MAP.get(overall)
        if mapped and bgv.status != mapped:
            bgv.status = mapped
            update_fields.add("status")
            changed = True

    # Check individual verification statuses
    for api_code, model_field in VERIFICATION_STATUS_FIELDS.items():
        status_key = f"overall{api_code}Status"
        new_val = status_data.get(status_key)
        if new_val is not None:
            old_val = getattr(bgv, model_field)
            if old_val != new_val:
                setattr(bgv, model_field, new_val)
                update_fields.add(model_field)
                changed = True

    # Check report URL
    report_url = status_data.get("consolidatedReportUrl")
    if report_url and bgv.report_url != report_url:
        bgv.report_url = report_url
        update_fields.add("report_url")
        changed = True
        
    # We always update the ongrid_status JSON if we are saving, to keep the cache fresh.
    # But we ONLY trigger a save if one of the structured fields changed.
    if changed:
        bgv.ongrid_status = status_data
        update_fields.add("ongrid_status")
        bgv.save(update_fields=list(update_fields))
        logger.info(
            "Persisted OnGrid status for individual %s → overall=%s, update_fields=%s",
            bgv.ongrid_individual_id, overall, list(update_fields)
        )
    else:
        logger.info(
            "OnGrid status unchanged for individual %s, skipping save.",
            bgv.ongrid_individual_id
        )


def get_verification_report(individual_id):
    """
    Fetch the verification report/results for an individual.
    """
    url = (
        f"{BASE_URL}/v1/individual/{individual_id}/report"
    )

    data, status_code, success = _ongrid_request("GET", url)
    return data if success else None