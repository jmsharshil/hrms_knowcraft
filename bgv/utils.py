import base64
import re
import logging

from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

PAN_REGEX = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"


def is_valid_pan(pan: str) -> bool:
    """Validate PAN format."""
    return bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan or ""))


def _file_to_base64(file_field):
    """Convert Django file field to base64."""
    file_field.open("rb")
    content = file_field.read()
    file_field.close()
    return base64.b64encode(content).decode("utf-8")


def extract_pan_from_openai(file_field):
    """
    Uses OpenAI Vision model to extract PAN details from image/PDF.
    Returns dict with structured data.
    """

    if not file_field:
        return None
    print(file_field,"file_field--------------------")
    try:
        b64 = _file_to_base64(file_field)
        print(b64,"b64--------------------")
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an OCR engine specialized in Indian PAN cards. "
                        "Extract ONLY the following fields:\n"
                        "1. PAN Number\n"
                        "2. Full Name\n"
                        "3. Father's Name\n"
                        "4. Date of Birth\n\n"
                        "Return output in this format:\n"
                        "PAN: XXXXX1234X\n"
                        "NAME: ....\n"
                        "FATHER: ....\n"
                        "DOB: DD/MM/YYYY\n"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract PAN card details accurately.",
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

        text = response.choices[0].message.content or ""

        print(text,"text--------------------")

        # ---- Extract PAN using regex ----
        pan_match = re.search(PAN_REGEX, text)
        pan_number = pan_match.group(0) if pan_match else None

        # ---- Parse structured fields ----
        def extract_field(label):
            pattern = rf"{label}:\s*(.*)"
            match = re.search(pattern, text)
            return match.group(1).strip() if match else None

        result = {
            "pan_number": pan_number,
            "name": extract_field("NAME"),
            "father_name": extract_field("FATHER"),
            "dob": extract_field("DOB"),
            "raw_text": text,
        }

        # validation
        if pan_number and not is_valid_pan(pan_number):
            result["pan_number"] = None

        return result

    except Exception as exc:
        logger.exception("PAN extraction failed: %s", exc)
        return {
            "error": str(exc)
        }

from pdf2image import convert_from_bytes
import io


def pdf_to_image_base64(file_field):
    """Convert first page of PDF to image base64."""
    file_field.open("rb")
    pdf_bytes = file_field.read()
    file_field.close()

    images = convert_from_bytes(pdf_bytes)

    if not images:
        return None

    buffer = io.BytesIO()
    images[0].save(buffer, format="JPEG")

    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def extract_pan_smart(file_field):
    """
    Handles both images and PDFs.
    """

    if not file_field:
        return None

    name = file_field.name.lower()

    # PDF handling
    if name.endswith(".pdf"):
        b64 = pdf_to_image_base64(file_field)
        if not b64:
            return None

        return _run_openai_vision(b64)

    # Image handling
    b64 = _file_to_base64(file_field)
    return _run_openai_vision(b64)


def _run_openai_vision(b64):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Extract PAN details from image.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract PAN details."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            },
        ],
        temperature=0,
    )

    return {"raw_text": response.choices[0].message.content}