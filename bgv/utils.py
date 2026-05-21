import base64
import re
import logging

from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

PAN_REGEX = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
AADHAAR_REGEX = r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"

def normalize_aadhaar(aadhaar):
    return re.sub(r"\D", "", aadhaar or "")

def is_valid_pan(pan: str) -> bool:
    """Validate PAN format."""
    return bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan or ""))

def is_valid_aadhaar(aadhaar: str) -> bool:
    aadhaar = normalize_aadhaar(aadhaar)
    return bool(re.fullmatch(r"\d{12}", aadhaar))

def _file_to_base64(file_field):
    """Convert Django file field to base64."""
    file_field.open("rb")
    content = file_field.read()
    file_field.close()
    return base64.b64encode(content).decode("utf-8")


# def extract_pan_from_openai(file_field):
#     """
#     Uses OpenAI Vision model to extract PAN details from image/PDF.
#     Returns dict with structured data.
#     """

#     if not file_field:
#         return None
#     print(file_field,"file_field--------------------")
#     try:
#         b64 = _file_to_base64(file_field)
#         print(b64,"b64--------------------")
#         response = client.chat.completions.create(
#             model="gpt-4.1-mini",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are an OCR engine specialized in Indian PAN cards. "
#                         "Extract ONLY the following fields:\n"
#                         "1. PAN Number\n"
#                         "2. Full Name\n"
#                         "3. Father's Name\n"
#                         "4. Date of Birth\n\n"
#                         "Return output in this format:\n"
#                         "PAN: XXXXX1234X\n"
#                         "NAME: ....\n"
#                         "FATHER: ....\n"
#                         "DOB: DD/MM/YYYY\n"
#                     ),
#                 },
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": "Extract PAN card details accurately.",
#                         },
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/jpeg;base64,{b64}"
#                             },
#                         },
#                     ],
#                 },
#             ],
#             temperature=0,
#         )

#         text = response.choices[0].message.content or ""

#         print(text,"text--------------------")

#         # ---- Extract PAN using regex ----
#         pan_match = re.search(PAN_REGEX, text)
#         pan_number = pan_match.group(0) if pan_match else None

#         # ---- Parse structured fields ----
#         def extract_field(label):
#             pattern = rf"{label}:\s*(.*)"
#             match = re.search(pattern, text)
#             return match.group(1).strip() if match else None

#         result = {
#             "pan_number": pan_number,
#             "name": extract_field("NAME"),
#             "father_name": extract_field("FATHER"),
#             "dob": extract_field("DOB"),
#             "raw_text": text,
#         }

#         # validation
#         if pan_number and not is_valid_pan(pan_number):
#             result["pan_number"] = None

#         return result

#     except Exception as exc:
#         logger.exception("PAN extraction failed: %s", exc)
#         return {
#             "error": str(exc)
#         }

# def extract_adhar_from_openai(file_field):
#     """
#     Uses OpenAI Vision model to extract Adhar details from image/PDF.
#     Returns dict with structured data.
#     """

#     if not file_field:
#         return None
#     try:
#         b64 = _file_to_base64(file_field)
#         response = client.chat.completions.create(
#             model="gpt-4.1-mini",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are an OCR engine specialized in Indian Aadhaar cards.\n"
#                         "Extract ONLY these fields exactly:\n"
#                         "1. Aadhaar Number\n"
#                         "2. Full Name\n"
#                         "3. Date of Birth\n"
#                         "4. Gender\n\n"
#                         "Rules:\n"
#                         "- Aadhaar number must contain exactly 12 digits\n"
#                         "- Preserve DOB format exactly as shown\n"
#                         "- Gender should be Male/Female/Other\n"
#                         "- Do not hallucinate values\n"
#                         "- Return ONLY this format:\n\n"
#                         "AADHAAR: <number>\n"
#                         "NAME: <name>\n"
#                         "DOB: <dob>\n"
#                         "GENDER: <gender>"
#                     ),
#                 },
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": "Extract Adhar card details accurately.",
#                         },
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/jpeg;base64,{b64}"
#                             },
#                         },
#                     ],
#                 },
#             ],
#             temperature=0,
#         )

#         text = response.choices[0].message.content or ""

#         # ---- Extract Adhar using regex ----
#         adhar_match = re.search(AADHAAR_REGEX, text)
#         aadhaar_number = None

#         if adhar_match:
#             aadhaar_number = normalize_aadhaar(
#                 adhar_match.group(0)
#             )

#         # ---- Parse structured fields ----
#         def extract_field(label):
#             pattern = rf"{label}:\s*(.*)"
#             match = re.search(pattern, text)
#             return match.group(1).strip() if match else None

#         result = {
#             "adhar_number": aadhaar_number,
#             "name": extract_field("NAME"),
#             "dob": extract_field("DOB"),
#             "gender": extract_field("GENDER"),
#             "raw_text": text,
#         }

#         # validation
#         if aadhaar_number and not is_valid_aadhaar(aadhaar_number):
#             result["adhar_number"] = None

#         return result

#     except Exception as exc:
#         logger.exception("Adhar extraction failed: %s", exc)
#         return {
#             "error": str(exc)
#         }

import io
from pdf2image import convert_from_bytes


def _prepare_file_for_vision(file_field):
    """
    Converts image/PDF into image base64 for OpenAI Vision.
    Returns base64 image string.
    """

    if not file_field:
        return None

    name = file_field.name.lower()

    # PDF handling
    if name.endswith(".pdf"):

        file_field.open("rb")
        pdf_bytes = file_field.read()
        file_field.close()

        images = convert_from_bytes(pdf_bytes)

        if not images:
            return None

        buffer = io.BytesIO()

        images[0].save(buffer, format="JPEG")

        return base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

    # Image handling
    return _file_to_base64(file_field)

def _run_openai_vision(prompt, b64):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract document details accurately.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}"
                        },
                    },
                ],
            },
        ],
        temperature=0,
    )

    return response.choices[0].message.content or ""

def extract_pan_smart(file_field):

    if not file_field:
        return None

    try:
        b64 = _prepare_file_for_vision(file_field)

        if not b64:
            return None

        prompt = (
            "You are an OCR engine specialized in Indian PAN cards.\n"
            "Extract ONLY the following fields:\n"
            "1. PAN Number\n"
            "2. Full Name\n"
            "3. Father's Name\n"
            "4. Date of Birth\n\n"
            "Return ONLY:\n"
            "PAN: XXXXX1234X\n"
            "NAME: ....\n"
            "FATHER: ....\n"
            "DOB: DD/MM/YYYY\n"
        )

        text = _run_openai_vision(prompt, b64)

        pan_match = re.search(PAN_REGEX, text)

        pan_number = pan_match.group(0) if pan_match else None

        def extract_field(label):
            pattern = rf"{label}:\s*(.+)"
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else None

        result = {
            "pan_number": pan_number,
            "name": extract_field("NAME"),
            "father_name": extract_field("FATHER"),
            "dob": extract_field("DOB"),
            "raw_text": text,
        }

        if pan_number and not is_valid_pan(pan_number):
            result["pan_number"] = None

        return result

    except Exception as exc:
        logger.exception("PAN extraction failed: %s", exc)

        return {
            "error": str(exc)
        }

def extract_aadhaar_smart(file_field):

    if not file_field:
        return None

    try:
        b64 = _prepare_file_for_vision(file_field)

        if not b64:
            return None

        prompt = (
            "You are an OCR engine specialized in Indian Aadhaar cards.\n"
            "Extract ONLY these fields:\n"
            "1. Aadhaar Number\n"
            "2. Full Name\n"
            "3. Date of Birth\n"
            "4. Gender\n\n"
            "Return ONLY:\n"
            "AADHAAR: <number>\n"
            "NAME: <name>\n"
            "DOB: <dob>\n"
            "GENDER: <gender>"
        )

        text = _run_openai_vision(prompt, b64)

        aadhaar_match = re.search(AADHAAR_REGEX, text)

        aadhaar_number = None

        if aadhaar_match:
            aadhaar_number = normalize_aadhaar(
                aadhaar_match.group(0)
            )

        def extract_field(label):
            pattern = rf"{label}:\s*(.+)"
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else None

        result = {
            "aadhaar_number": aadhaar_number,
            "name": extract_field("NAME"),
            "dob": extract_field("DOB"),
            "gender": extract_field("GENDER"),
            "raw_text": text,
        }

        if aadhaar_number and not is_valid_aadhaar(aadhaar_number):
            result["aadhaar_number"] = None

        return result

    except Exception as exc:
        logger.exception("Aadhaar extraction failed: %s", exc)

        return {
            "error": str(exc)
        }

def extract_candidate_kyc_details(candidate):

    details = {}

    documents = getattr(candidate, "documents", None)

    if not documents:
        return details

    # PAN
    pan_file = getattr(documents, "pan", None)

    if pan_file:
        pan_data = extract_pan_smart(pan_file)

        if pan_data:
            details.update({
                "pan_number": pan_data.get("pan_number"),
                "father_name": pan_data.get("father_name"),
            })

            # Prefer PAN DOB if available
            if pan_data.get("dob"):
                details["dob"] = pan_data.get("dob")

    # Aadhaar
    aadhaar_file = getattr(documents, "aadhaar", None)

    if aadhaar_file:
        aadhaar_data = extract_aadhaar_smart(aadhaar_file)

        if aadhaar_data:
            details.update({
                "aadhaar_number": aadhaar_data.get("aadhaar_number"),
                "gender": aadhaar_data.get("gender"),
                "address": aadhaar_data.get("address"),
            })

            # fallback DOB
            if not details.get("dob"):
                details["dob"] = aadhaar_data.get("dob")

    return details