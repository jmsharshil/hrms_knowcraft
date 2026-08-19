"""
Test script for survey PDF generation.
Run with: python test_survey_pdf.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_knowcraft.settings')
django.setup()

from onboarding.models import SurveyResponse
from jobs.models import JobApplication
from onboarding.utils.pdf_maker import generate_survey_pdf

# ── 1. Find a real candidate to attach the mock response to ──────────────────
app = JobApplication.objects.filter(joining_date__isnull=False).first()
if not app:
    print("[ERROR] No JobApplication with joining_date found. Cannot run test.")
    exit(1)

print(f"[INFO] Using candidate: {app.candidate_name} (id={app.id})")

# ── 2. Build a mock SurveyResponse with realistic answers ────────────────────
mock_response = SurveyResponse(
    job_application=app,
    survey_type="30_day_candidate",
    respondent_name=app.candidate_name,
    respondent_email=getattr(app, 'work_email', None) or app.candidate_email,
    responses={
        "1": "strongly_agree",
        "2": "agree",
        "3": "neutral",
        "4": "agree",
        "5": "strongly_agree",
        "6": "The onboarding process was smooth and well-organized. I felt welcomed from day one.",
        "7": "agree",
        "8": "agree",
        "9": "strongly_agree",
        "10": "agree",
        "11": "I would have appreciated more clarity on the tools I'd be using before joining.",
        "12": "agree",
        "13": "neutral",
        "14": "Yes, the buddy program was very helpful.",
        "15": "strongly_agree",
    }
)

# ── 3. Get the survey structure (from DB or hardcoded fallback) ───────────────
from onboarding.views import _get_survey_structure
structure = _get_survey_structure(app, "30_day_candidate")
print(f"[INFO] Survey title: {structure.get('title', 'N/A')}")
print(f"[INFO] Sections: {[s['title'] for s in structure.get('sections', [])]}")

# ── 4. Generate PDF ──────────────────────────────────────────────────────────
print("\n[INFO] Generating PDF...")
try:
    filename, pdf_bytes, mime = generate_survey_pdf(mock_response, structure)
    print(f"[OK]  Generated: {filename}")
    print(f"[OK]  Size: {len(pdf_bytes):,} bytes | MIME: {mime}")

    # Save to current directory
    out_path = os.path.join(os.path.dirname(__file__), filename)
    with open(out_path, 'wb') as f:
        f.write(pdf_bytes)

    print(f"\n[DONE] PDF saved to: {out_path}")
    print("       Open this file to verify the layout and content.")

except Exception as e:
    import traceback
    print(f"\n[ERROR] PDF generation failed: {e}")
    traceback.print_exc()
