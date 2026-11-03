from django.template.loader import render_to_string
# from weasyprint import HTML
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
# from pypdf import PdfReader, PdfWriter

# def html_to_pdf(template_name, context):
#     html_string = render_to_string(template_name, context)
#     pdf_bytes = HTML(string=html_string).write_pdf()
#     return pdf_bytes

# def html_to_pdf(html_string):
#     pdf_bytes = HTML(string=html_string).write_pdf()
#     return pdf_bytes

from xhtml2pdf import pisa

def html_to_pdf(html_content):
    """
    Convert FULL HTML + CSS to PDF using xhtml2pdf.
    """
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(
        html_content,
        dest=pdf_buffer
    )
    
    if pisa_status.err:
        raise Exception("PDF generation error using xhtml2pdf.")

    pdf_buffer.seek(0)
    return pdf_buffer.read()

# def fill_pdf_overlay(template_path, data):
#     # Create overlay in memory
#     overlay_buffer = BytesIO()
#     c = canvas.Canvas(overlay_buffer, pagesize=letter)

#     # Draw dynamic values (set coordinates as needed)
#     c.drawString(100, 700, data["employee_name"])
#     c.drawString(100, 680, data["position"])
#     c.drawString(100, 660, data["salary"])
#     c.drawString(100, 640, data["joining_date"])
#     c.save()

#     overlay_buffer.seek(0)

#     # Read PDFs
#     template_pdf = PdfReader(template_path)
#     overlay_pdf = PdfReader(overlay_buffer)

#     writer = PdfWriter()

#     # Merge the overlay onto the first page
#     base_page = template_pdf.pages[0]
#     base_page.merge_page(overlay_pdf.pages[0])
#     writer.add_page(base_page)

#     # Output final PDF as bytes
#     output_buffer = BytesIO()
#     writer.write(output_buffer)
#     output_buffer.seek(0)

#     return output_buffer.read()


def generate_offer_letter(candidate):
    """
    Generate a simple PDF for testing purposes.
    Returns a tuple: (filename, bytes_content, mimetype)
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.drawString(100, 750, f"Offer Letter for {candidate.candidate_name}")
    c.drawString(100, 730, f"Email: {candidate.candidate_email}")
    c.save()

    buffer.seek(0)
    pdf_bytes = buffer.read()

    filename = f"offer_letter_{candidate.id}.pdf"
    return (filename, pdf_bytes, "application/pdf")

def generate_survey_pdf(survey_response, structure):
    """
    Generate a professional PDF from a SurveyResponse with Knowcraft branding.
    Returns a tuple: (filename, bytes_content, mimetype)
    """
    import base64, requests as req_lib

    # ── Fetch & embed logo as base64 (xhtml2pdf cannot load external URLs) ───
    logo_b64 = ""
    logo_mime = "image/png"
    try:
        logo_resp = req_lib.get(
            "https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png",
            timeout=8
        )
        if logo_resp.status_code == 200:
            logo_b64 = base64.b64encode(logo_resp.content).decode("utf-8")
    except Exception:
        pass  # logo is optional — PDF still renders without it

    logo_tag = (
        f'<img src="data:{logo_mime};base64,{logo_b64}" '
        f'alt="Knowcraft Analytics" style="height:50px; display:block; margin:0 auto;">'
        if logo_b64 else
        '<span style="font-size:22px; font-weight:700; color:#1e3a5f; letter-spacing:1px;">Knowcraft Analytics</span>'
    )

    # ── Meta ─────────────────────────────────────────────────────────────────
    candidate   = survey_response.job_application
    survey_title = structure.get('title', 'Survey Report')
    submitted   = survey_response.submitted_at
    submitted_str = submitted.strftime('%d %B %Y, %I:%M %p') if submitted else 'N/A'

    # Role & department
    role = dept = ""
    try:
        role = candidate.job.mrf.designation.name if candidate.job and candidate.job.mrf else ""
        dept = candidate.job.mrf.department.name  if candidate.job and candidate.job.mrf else ""
    except Exception:
        pass

    # ── Answer badge helper ───────────────────────────────────────────────────
    SCALE_COLORS = {
        "strongly_agree":    ("#d1fae5", "#065f46"),   # green
        "agree":             ("#dbeafe", "#1e40af"),   # blue
        "neutral":           ("#fef9c3", "#713f12"),   # yellow
        "disagree":          ("#ffedd5", "#9a3412"),   # orange
        "strongly_disagree": ("#fee2e2", "#991b1b"),   # red
    }

    def answer_badge(raw):
        """Return a styled span for a scale answer, or plain text for free text."""
        if not raw:
            return '<span style="color:#94a3b8; font-style:italic;">No response</span>'
        key = raw.lower().replace(" ", "_") if isinstance(raw, str) else ""
        if key in SCALE_COLORS:
            bg, fg = SCALE_COLORS[key]
            label = raw.replace("_", " ").title()
            return (
                f'<span style="display:inline-block; padding:3px 12px; border-radius:20px; '
                f'background:{bg}; color:{fg}; font-weight:600; font-size:11px;">{label}</span>'
            )
        # Long free-text answer
        return f'<span style="color:#1e293b;">{raw}</span>'

    # ── Build responses map ───────────────────────────────────────────────────
    responses = survey_response.responses or {}
    sections  = structure.get('sections', [])

    # ── Sections HTML ─────────────────────────────────────────────────────────
    sections_html = ""
    processed_qids = set()
    for s_idx, section in enumerate(sections):
        sections_html += f"""
        <div style="margin-top:22px; page-break-inside:avoid;">
            <div style="background:#1e3a5f; color:#ffffff; padding:9px 16px;
                        font-size:12px; font-weight:700; letter-spacing:0.4px;
                        margin-bottom:8px;">
                {section.get('title', 'Section')}
            </div>
        """
        for q_idx, q in enumerate(section.get('questions', [])):
            qid     = str(q.get('id'))
            processed_qids.add(qid)
            qtext   = q.get('text', '')
            raw_ans = responses.get(qid)
            badge   = answer_badge(raw_ans)
            row_bg  = "#f8fafc" if q_idx % 2 == 0 else "#ffffff"

            sections_html += f"""
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8px; background:{row_bg}; border:1px solid #e2e8f0;">
                <tr>
                    <td style="width:6%; padding:12px 2px 12px 10px; color:#64748b; font-size:11px; font-weight:700; vertical-align:top; text-align:right;">
                        {qid}.
                    </td>
                    <td style="width:64%; padding:12px 10px 12px 10px; font-size:12px; color:#334155; vertical-align:top; line-height:16px;">
                        {qtext}
                    </td>
                    <td style="width:30%; padding:12px 12px 12px 0; text-align:right; vertical-align:top;">
                        {badge}
                    </td>
                </tr>
            </table>
            """
        sections_html += "</div>"

    unprocessed_qids = set(responses.keys()) - processed_qids
    if unprocessed_qids:
        def sort_key(k):
            try:
                return (0, int(k))
            except ValueError:
                return (1, str(k))
        
        sorted_unprocessed = sorted(list(unprocessed_qids), key=sort_key)
        
        sections_html += f"""
        <div style="margin-top:22px; page-break-inside:avoid;">
            <div style="background:#1e3a5f; color:#ffffff; padding:9px 16px;
                        font-size:12px; font-weight:700; letter-spacing:0.4px;
                        margin-bottom:8px;">
                Additional Responses
            </div>
        """
        for q_idx, qid in enumerate(sorted_unprocessed):
            qtext   = f"Question ID: {qid}"
            raw_ans = responses.get(qid)
            badge   = answer_badge(raw_ans)
            row_bg  = "#f8fafc" if q_idx % 2 == 0 else "#ffffff"

            sections_html += f"""
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8px; background:{row_bg}; border:1px solid #e2e8f0;">
                <tr>
                    <td style="width:6%; padding:12px 2px 12px 10px; color:#64748b; font-size:11px; font-weight:700; vertical-align:top; text-align:right;">
                        {qid}.
                    </td>
                    <td style="width:64%; padding:12px 10px 12px 10px; font-size:12px; color:#334155; vertical-align:top; line-height:16px;">
                        {qtext}
                    </td>
                    <td style="width:30%; padding:12px 12px 12px 0; text-align:right; vertical-align:top;">
                        {badge}
                    </td>
                </tr>
            </table>
            """
        sections_html += "</div>"

    # ── Summary rows (single-column label/value pairs, no overflow) ──────────
    joining_str = candidate.joining_date.strftime('%d %B %Y') if candidate.joining_date else '—'

    def info_row(label, value):
        return f"""
        <tr>
            <td style="padding:10px 10px 10px 15px; width:30%; color:#475569;
                       font-weight:600; font-size:11px; vertical-align:top;
                       border-bottom:0.5px solid #cbd5e1;">{label}</td>
            <td style="padding:10px 15px 10px 10px; color:#0f172a; font-size:12px;
                       vertical-align:top; border-bottom:0.5px solid #cbd5e1;">{value}</td>
        </tr>"""

    summary_rows = (
        info_row("Candidate Name", f"<strong>{candidate.candidate_name}</strong>") +
        info_row("Survey Type", survey_response.get_survey_type_display()) +
        info_row("Role", role or "—") +
        info_row("Department", dept or "—") +
        info_row("Date of Joining", joining_str) +
        info_row("Submitted On", submitted_str) +
        info_row("Respondent", survey_response.respondent_name or "—") +
        info_row("Respondent Email", survey_response.respondent_email or "—")
    )

    # ── Full HTML document ────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 12mm 15mm 20mm 15mm;
        @frame footer_frame {{
            -pdf-frame-content: footer_content;
            left: 15mm; right: 15mm; bottom: 5mm; height: 10mm;
        }}
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        font-size: 12px;
        color: #1e293b;
        background: #ffffff;
        margin: 0;
    }}
</style>
</head>
<body>

<!-- ── Fixed Footer ── -->
<div id="footer_content" style="text-align: center; font-size: 9px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 6px;">
    Knowcraft Analytics Private Limited  &nbsp;|&nbsp;  Confidential – HR Use Only  &nbsp;|&nbsp;  Generated on {submitted_str}
</div>

<!-- ── Header ── -->
<div style="text-align: center; margin-bottom: 18px;">
    <div style="margin-bottom: 8px;">
        {logo_tag}
    </div>
    <div style="font-size:17px; font-weight:700; color:#1e3a5f; margin-bottom: 8px; letter-spacing:0.3px;">
        {survey_title}
    </div>
    <div style="font-size:11px; color:#64748b; margin-bottom: 12px;">
        Human Resources &nbsp;&bull;&nbsp; Onboarding Feedback Report
        &nbsp;&nbsp;
        <span style="background:#fef2f2; color:#991b1b; font-size:10px;
                     font-weight:700; padding:2px 8px; border:1px solid #fecaca;">
            CONFIDENTIAL
        </span>
    </div>
    <div style="border-bottom: 3px solid #1e3a5f; width: 100%;"></div>
</div>

<!-- ── Summary Card ── -->
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#f0f7ff; border-left:1px solid #bfdbfe; border-right:1px solid #bfdbfe; border-top:4px solid #1e3a5f; margin-bottom:22px;">
    {summary_rows}
</table>

<!-- ── Survey Sections ── -->
{sections_html}

</body>
</html>"""

    pdf_bytes = html_to_pdf(html)
    safe_name = candidate.candidate_name.replace(' ', '_').replace('/', '_')
    filename  = f"{survey_response.survey_type}_{safe_name}.pdf"
    return (filename, pdf_bytes, "application/pdf")


# ─────────────────────────────────────────────────────────────────────────────
# Approval Note PDF
# ─────────────────────────────────────────────────────────────────────────────

def generate_approval_note_pdf(note):
    """
    Generate a full branded Approval Note PDF from an ApprovalNote instance.
    The PDF mirrors the email sent to the hiring manager – with Candidate
    Details, Interview Rounds (interviewers + scores) and Offer & Other
    Details tables, plus approval status and metadata.

    Returns: (filename, bytes, mimetype)
    """
    import base64, requests as req_lib

    # ── Logo ─────────────────────────────────────────────────────────────────
    logo_b64 = ""
    try:
        r = req_lib.get(
            "https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png",
            timeout=8
        )
        if r.status_code == 200:
            logo_b64 = base64.b64encode(r.content).decode("utf-8")
    except Exception:
        pass

    logo_tag = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        f'alt="Knowcraft Analytics" style="height:48px; display:block; margin:0 auto;">'
        if logo_b64 else
        '<span style="font-size:22px; font-weight:700; color:#1e3a5f;">Knowcraft Analytics</span>'
    )

    def clean_val(v, default="—"):
        if v is None:
            return default
        s = str(v).strip()
        if not s or s.lower() in {"none", "null", "undefined", "-", "—"}:
            return default
        return s

    # ── Data ─────────────────────────────────────────────────────────────────
    p = note.payload or {}
    cand = note.candidate

    candidate_name = clean_val(p.get("candidate_name") or (cand.candidate_name if cand else None), default="N/A")
    designation = clean_val(p.get("designation") or (cand.job.mrf.designation.name if cand and cand.job and cand.job.mrf and cand.job.mrf.designation else None))
    department = clean_val(p.get("department") or (cand.job.mrf.department.name if cand and cand.job and cand.job.mrf and cand.job.mrf.department else None))
    experience = clean_val(p.get("experience") or (cand.experience_years if cand else None))
    qualification = clean_val(p.get("qualification"))
    last_org = clean_val(p.get("last_organization"))

    hr_interviewer    = clean_val(p.get("hr_round_interviewer"))
    tech_interviewer  = clean_val(p.get("tech_round_interviewer"))
    case_interviewer  = clean_val(p.get("case_study_round_interviewer"))
    final_interviewer = clean_val(p.get("final_round_interviewer"))
    mgmt_interviewer  = clean_val(p.get("management_client_round_interviewer"))

    hr_score    = clean_val(p.get("hr_round_score"))
    tech_score  = clean_val(p.get("tech_round_score"))
    case_score  = clean_val(p.get("case_study_round_score"))
    final_score = clean_val(p.get("final_round_score"))
    mgmt_score  = clean_val(p.get("management_client_round_score"))

    # If payload didn't contain interviewer or score, fallback to candidate's feedbacks in DB
    if cand:
        for fb in cand.interview_feedbacks.all():
            r = fb.interview_round
            avg_score = fb.get_round_avg()
            score_str = f"{avg_score:.1f}/5" if (avg_score and avg_score > 0) else None
            if r == "hr_round":
                if hr_interviewer == "—": hr_interviewer = clean_val(fb.interviewer_name)
                if hr_score == "—" and score_str: hr_score = score_str
            elif r == "technical_round":
                if tech_interviewer == "—": tech_interviewer = clean_val(fb.interviewer_name)
                if tech_score == "—" and score_str: tech_score = score_str
            elif r == "case_study_round":
                if case_interviewer == "—": case_interviewer = clean_val(fb.interviewer_name)
                if case_score == "—" and score_str: case_score = score_str
            elif r == "final_round":
                if final_interviewer == "—": final_interviewer = clean_val(fb.interviewer_name)
                if final_score == "—" and score_str: final_score = score_str
            elif r == "management_client_round":
                if mgmt_interviewer == "—": mgmt_interviewer = clean_val(fb.interviewer_name)
                if mgmt_score == "—" and score_str: mgmt_score = score_str

    current_ctc  = clean_val(p.get("current_ctc"))
    expected_ctc = clean_val(p.get("expected_ctc"))
    offered_ctc  = clean_val(p.get("offered_ctc"))
    notice       = clean_val(p.get("notice_period"))
    location     = clean_val(p.get("office_location"))
    source       = clean_val(p.get("source"))
    mrf          = clean_val(p.get("mrf"))
    hiring_type  = clean_val(p.get("hiring_type"))
    remarks      = clean_val(p.get("remarks"), default="")

    approver_name  = note.manager.name if note.manager else "N/A"
    created_by     = note.created_by.name if note.created_by else "N/A"
    created_at_str = note.created_at.strftime("%d %B %Y, %I:%M %p") if note.created_at else "N/A"
    status_display = note.get_status_display() if note.status else (note.status or "N/A")

    STATUS_BADGE = {
        "approved":          ("#d1fae5", "#065f46"),
        "approval_pending":  ("#fef9c3", "#713f12"),
        "approval_rejected": ("#fee2e2", "#991b1b"),
        "joined":            ("#dbeafe", "#1e40af"),
    }
    badge_bg, badge_fg = STATUS_BADGE.get(note.status, ("#e0e7ff", "#3730a3"))

    def info_row(label, value, alt=False):
        bg = "#f8fafc" if alt else "#ffffff"
        return f"""
        <tr style="background:{bg};">
            <td style="padding:8px 12px; width:36%; font-weight:600; color:#374151;
                       font-size:11px; border:1px solid #e2e8f0;">{label}</td>
            <td style="padding:8px 12px; width:64%; font-size:11px; color:#111827;
                       border:1px solid #e2e8f0;">{value}</td>
        </tr>"""

    def section_header_div(title):
        return f"""
        <div style="background:#1e3a5f; color:#ffffff; padding:7px 12px;
                    font-size:12px; font-weight:700; letter-spacing:0.3px;
                    border:1px solid #1e3a5f; margin-top:14px;">
            {title}
        </div>"""

    remarks_row = (
        info_row("Remarks", remarks, alt=True) if remarks else ""
    )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 12mm 15mm 20mm 15mm;
        @frame footer_frame {{
            -pdf-frame-content: footer_content;
            left: 15mm; right: 15mm; bottom: 5mm; height: 10mm;
        }}
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        font-size: 11px;
        color: #1e293b;
        background: #ffffff;
        margin: 0;
    }}
    table {{ border-collapse: collapse; width: 100%; }}
</style>
</head>
<body>

<!-- Footer -->
<div id="footer_content" style="text-align:center; font-size:9px; color:#94a3b8;
     border-top:1px solid #e2e8f0; padding-top:6px;">
    Knowcraft Analytics Private Limited &nbsp;|&nbsp; Confidential – HR Use Only
    &nbsp;|&nbsp; Generated on {created_at_str}
</div>

<!-- Header -->
<div style="text-align:center; margin-bottom:16px;">
    <div style="margin-bottom:8px;">{logo_tag}</div>
    <div style="font-size:18px; font-weight:700; color:#1e3a5f; margin-bottom:4px;">
        Approval Note – Candidate Hiring
    </div>
    <div style="font-size:11px; color:#64748b; margin-bottom:10px;">
        Human Resources &nbsp;•&nbsp; Talent Acquisition
        &nbsp;&nbsp;
        <span style="background:#fef2f2; color:#991b1b; font-size:10px;
                     font-weight:700; padding:2px 8px; border:1px solid #fecaca;">
            CONFIDENTIAL
        </span>
    </div>
    <div style="border-bottom:2px solid #1e3a5f; width:100%;"></div>
</div>

<!-- Approval Status Banner -->
<div style="background:{badge_bg}; color:{badge_fg}; border:1px solid {badge_fg};
            border-radius:4px; padding:9px 14px; margin-bottom:16px;
            font-size:12px; font-weight:700; text-align:center;">
    Status: {status_display}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Approver: {approver_name}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Requested By: {created_by}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Date: {created_at_str}
</div>

<!-- Candidate Details -->
{section_header_div("Candidate Details")}
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px; border-collapse:collapse;">
    {info_row("Name of Candidate", f"<strong>{candidate_name}</strong>", alt=True)}
    {info_row("Designation", designation)}
    {info_row("Department", department, alt=True)}
    {info_row("Experience", experience)}
    {info_row("Qualification", qualification, alt=True)}
    {info_row("Last Organization", last_org)}
</table>

<!-- Interview Rounds -->
{section_header_div("Interview Rounds – Interviewers")}
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px; border-collapse:collapse;">
    {info_row("HR Round", hr_interviewer, alt=True)}
    {info_row("Technical Round", tech_interviewer)}
    {info_row("Case Study Round", case_interviewer, alt=True)}
    {info_row("Final Round", final_interviewer)}
    {info_row("Management / Client Round", mgmt_interviewer, alt=True)}
</table>

{section_header_div("Interview Scores")}
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px; border-collapse:collapse;">
    {info_row("HR Round Score", hr_score, alt=True)}
    {info_row("Technical Round Score", tech_score)}
    {info_row("Case Study Round Score", case_score, alt=True)}
    {info_row("Final Round Score", final_score)}
    {info_row("Management / Client Round Score", mgmt_score, alt=True)}
</table>

<!-- Offer & Other Details -->
{section_header_div("Offer &amp; Other Details")}
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px; border-collapse:collapse;">
    {info_row("Current / Last Drawn CTC", current_ctc, alt=True)}
    {info_row("Expected CTC", expected_ctc)}
    {info_row("CTC to be Offered", f"<strong>{offered_ctc}</strong>", alt=True)}
    {info_row("Notice Period", notice)}
    {info_row("Office Location", location, alt=True)}
    {info_row("Source", source)}
    {info_row("MRF", mrf, alt=True)}
    {info_row("New / Replacement", hiring_type)}
    {remarks_row}
</table>

<p style="font-size:10px; color:#64748b; margin-top:20px; text-align:center;">
    This document is auto-generated by the Knowcraft HRMS. For queries, contact HR.
</p>

</body>
</html>"""

    pdf_bytes = html_to_pdf(html)
    safe = candidate_name.replace(" ", "_").replace("/", "_")
    filename = f"Approval_Note_{safe}.pdf"
    return (filename, pdf_bytes, "application/pdf")


# ─────────────────────────────────────────────────────────────────────────────
# Interview Feedback PDF
# ─────────────────────────────────────────────────────────────────────────────

def generate_interview_feedback_pdf(fb):
    """
    Generate a detailed Interview Feedback PDF from an InterviewFeedback instance.
    Includes: candidate/round metadata, dynamically included ratings with colour-coded
    scores and remarks (omitting blank/unrated dimensions), candidate profile fields
    (only non-blank fields), behavioural/cultural notes, and the final hiring recommendation.

    Returns: (filename, bytes, mimetype)
    """
    import base64, requests as req_lib

    # ── Logo ─────────────────────────────────────────────────────────────────
    logo_b64 = ""
    try:
        r = req_lib.get(
            "https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png",
            timeout=8
        )
        if r.status_code == 200:
            logo_b64 = base64.b64encode(r.content).decode("utf-8")
    except Exception:
        pass

    logo_tag = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        f'alt="Knowcraft Analytics" style="height:48px; display:block; margin:0 auto;">'
        if logo_b64 else
        '<span style="font-size:22px; font-weight:700; color:#1e3a5f;">Knowcraft Analytics</span>'
    )

    # ── Meta ─────────────────────────────────────────────────────────────────
    candidate       = fb.job_application
    candidate_name  = candidate.candidate_name if candidate else "N/A"
    round_display   = fb.get_interview_round_display() if hasattr(fb, "get_interview_round_display") else (fb.interview_round or "Interview")
    interviewer     = fb.interviewer_name or "N/A"
    interview_date  = fb.interview_date.strftime("%d %B %Y") if fb.interview_date else "N/A"
    created_str     = fb.created_at.strftime("%d %B %Y, %I:%M %p") if fb.created_at else "N/A"

    # Hiring recommendation badge
    HIRE_BADGE = {
        "hire":        ("#d1fae5", "#065f46", "✓ Hire"),
        "strong_hire": ("#bbf7d0", "#14532d", "✓✓ Strong Hire"),
        "reject":      ("#fee2e2", "#991b1b", "✗ Reject"),
    }
    badge_bg, badge_fg, badge_label = HIRE_BADGE.get(
        fb.is_selected, ("#e0e7ff", "#3730a3", fb.is_selected or "Pending")
    )

    def is_valid_str(val):
        if val is None:
            return False
        s = str(val).strip()
        return bool(s and s.lower() not in {"-", "—", "none", "null", "undefined"})

    def is_valid_score(val):
        if val is None:
            return False
        try:
            return float(val) > 0
        except (ValueError, TypeError):
            return False

    def score_bar(score):
        """Return an inline coloured score indicator (0 to 5 scale)."""
        try:
            val = float(score)
        except (TypeError, ValueError):
            val = 0
        if val <= 0:
            return '<span style="color:#94a3b8; font-size:11px;">—</span>'
        pct = min(int(val / 5 * 100), 100)
        colour = "#16a34a" if val >= 4 else ("#ca8a04" if val >= 2.5 else "#dc2626")
        return (
            f'<span style="font-weight:700; color:{colour};">{val:.1f}/5</span>'
            f'&nbsp;<span style="display:inline-block; width:80px; height:8px; '
            f'background:#e2e8f0; border-radius:4px; vertical-align:middle;">'
            f'<span style="display:inline-block; width:{pct}%; height:8px; '
            f'background:{colour}; border-radius:4px;"></span></span>'
        )

    def rating_row(label, score, remark=None, alt=False):
        bg = "#f8fafc" if alt else "#ffffff"
        remark_str = str(remark).strip() if is_valid_str(remark) else ""
        remark_cell = (
            f'<td style="padding:8px 12px; font-size:11px; color:#475569; '
            f'border:1px solid #e2e8f0; font-style:italic; width:44%;">{remark_str}</td>'
            if remark_str else
            f'<td style="padding:8px 12px; border:1px solid #e2e8f0; '
            f'color:#cbd5e1; font-size:11px; width:44%;">—</td>'
        )
        return f"""
        <tr style="background:{bg};">
            <td style="padding:8px 12px; width:34%; font-size:11px;
                       font-weight:600; color:#374151; border:1px solid #e2e8f0;">{label}</td>
            <td style="padding:8px 12px; width:22%; border:1px solid #e2e8f0;">{score_bar(score)}</td>
            {remark_cell}
        </tr>"""

    def info_row(label, value, alt=False):
        bg = "#f8fafc" if alt else "#ffffff"
        return f"""
        <tr style="background:{bg};">
            <td style="padding:8px 12px; width:36%; font-weight:600; color:#374151;
                       font-size:11px; border:1px solid #e2e8f0;">{label}</td>
            <td style="padding:8px 12px; width:64%; font-size:11px; color:#111827;
                       border:1px solid #e2e8f0;">{value}</td>
        </tr>"""

    # ── Ratings: Check all dimensions and filter out unrated/blank ────────────
    CORE_DIMENSIONS = [
        ("Communication",        fb.communication_rating,        fb.communication_rating_remark),
        ("Technical Skill",      fb.technical_skill_rating,      fb.technical_skill_rating_remark),
        ("Attitude & Intent",    fb.attitude_intent_rating,      fb.attitude_intent_rating_remark),
        ("Team Handling",        fb.team_handling_rating,        fb.team_handling_rating_remark),
        ("Stability",            fb.stability_rating,            fb.stability_rating_remark),
        ("Problem Solving",      fb.problem_solving_rating,      fb.problem_solving_rating_remark),
        ("Analytical Thinking",  fb.analytical_thinking_rating,  fb.analytical_thinking_rating_remark),
        ("Cultural Fit",         fb.cultural_fit_rating,         fb.cultural_fit_rating_remark),
        ("Competency",           fb.competency_rating,           fb.competency_rating_remark),
        ("Interpersonal Skills", fb.interpersonal_skills_rating, fb.interpersonal_skills_rating_remark),
    ]

    LEADERSHIP_DIMENSIONS = [
        ("Leadership Skills", fb.leadership_skills_rating, fb.leadership_skills_rating_remark),
        ("Learning Agility",  fb.learning_agility_rating,  fb.learning_agility_rating_remark),
        ("Problem Solving / Critical Thinking / Decision Making",
         fb.problem_solving_critical_thinking_decision_making_rating,
         fb.problem_solving_critical_thinking_decision_making_rating_remark),
        ("Business Acumen / Industry Understanding",
         fb.business_acumen_industry_understanding_rating,
         fb.business_acumen_industry_understanding_rating_remark),
        ("Ownership & Accountability",
         fb.ownership_accountibility_rating,
         fb.ownership_accountibility_rating_remark),
    ]

    valid_core = [
        (label, score, remark) for label, score, remark in CORE_DIMENSIONS
        if is_valid_score(score) or is_valid_str(remark)
    ]
    valid_leadership = [
        (label, score, remark) for label, score, remark in LEADERSHIP_DIMENSIONS
        if is_valid_score(score) or is_valid_str(remark)
    ]

    core_ratings_table = ""
    if valid_core:
        rows = "".join(
            rating_row(label, score, remark, alt=(i % 2 == 1))
            for i, (label, score, remark) in enumerate(valid_core)
        )
        core_ratings_table = f"""
        <div style="background:#1e3a5f; color:#ffffff; padding:7px 12px;
                    font-size:12px; font-weight:700; border:1px solid #1e3a5f; margin-top:14px;">
            Core Ratings &amp; Remarks
        </div>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px; border-collapse:collapse;">
            <tr style="background:#e0e7ff;">
                <td style="padding:8px 12px; font-size:11px; font-weight:700; color:#374151;
                           border:1px solid #e2e8f0; width:34%;">Dimension</td>
                <td style="padding:8px 12px; font-size:11px; font-weight:700; color:#374151;
                           border:1px solid #e2e8f0; width:22%;">Score</td>
                <td style="padding:8px 12px; font-size:11px; font-weight:700; color:#374151;
                           border:1px solid #e2e8f0; width:44%;">Remarks</td>
            </tr>
            {rows}
        </table>"""

    leadership_ratings_table = ""
    if valid_leadership:
        rows = "".join(
            rating_row(label, score, remark, alt=(i % 2 == 1))
            for i, (label, score, remark) in enumerate(valid_leadership)
        )
        leadership_ratings_table = f"""
        <div style="background:#1e3a5f; color:#ffffff; padding:7px 12px;
                    font-size:12px; font-weight:700; border:1px solid #1e3a5f; margin-top:14px;">
            Leadership &amp; Strategic Ratings
        </div>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px; border-collapse:collapse;">
            <tr style="background:#e0e7ff;">
                <td style="padding:8px 12px; font-size:11px; font-weight:700; color:#374151;
                           border:1px solid #e2e8f0; width:34%;">Dimension</td>
                <td style="padding:8px 12px; font-size:11px; font-weight:700; color:#374151;
                           border:1px solid #e2e8f0; width:22%;">Score</td>
                <td style="padding:8px 12px; font-size:11px; font-weight:700; color:#374151;
                           border:1px solid #e2e8f0; width:44%;">Remarks</td>
            </tr>
            {rows}
        </table>"""

    # Round average score
    avg = fb.get_round_avg()
    if not avg or float(avg) == 0:
        all_eval_scores = [
            float(s) for _, s, _ in (valid_core + valid_leadership)
            if is_valid_score(s)
        ]
        if all_eval_scores:
            avg = round(sum(all_eval_scores) / len(all_eval_scores), 1)

    # ── Summary Card Rows (Dynamic) ───────────────────────────────────────────
    summary_card_rows = [
        f"""<tr>
            <td style="padding:8px 12px; width:30%; color:#475569; font-weight:600;
                       font-size:11px; vertical-align:top; border-bottom:0.5px solid #cbd5e1;">
                Candidate Name</td>
            <td style="padding:8px 12px; color:#0f172a; font-size:12px; font-weight:700;
                       border-bottom:0.5px solid #cbd5e1;">{candidate_name}</td>
        </tr>""",
        f"""<tr>
            <td style="padding:8px 12px; color:#475569; font-weight:600; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">Interview Round</td>
            <td style="padding:8px 12px; color:#0f172a; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">{round_display}</td>
        </tr>""",
        f"""<tr>
            <td style="padding:8px 12px; color:#475569; font-weight:600; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">Interviewer</td>
            <td style="padding:8px 12px; color:#0f172a; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">{interviewer}</td>
        </tr>""",
        f"""<tr>
            <td style="padding:8px 12px; color:#475569; font-weight:600; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">Interview Date</td>
            <td style="padding:8px 12px; color:#0f172a; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">{interview_date}</td>
        </tr>"""
    ]

    if is_valid_str(fb.department):
        summary_card_rows.append(f"""<tr>
            <td style="padding:8px 12px; color:#475569; font-weight:600; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">Department</td>
            <td style="padding:8px 12px; color:#0f172a; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">{str(fb.department).strip()}</td>
        </tr>""")

    if is_valid_str(fb.designation):
        summary_card_rows.append(f"""<tr>
            <td style="padding:8px 12px; color:#475569; font-weight:600; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">Designation</td>
            <td style="padding:8px 12px; color:#0f172a; font-size:11px;
                       border-bottom:0.5px solid #cbd5e1;">{str(fb.designation).strip()}</td>
        </tr>""")

    if avg and float(avg) > 0:
        summary_card_rows.append(f"""<tr>
            <td style="padding:8px 12px; color:#475569; font-weight:600; font-size:11px;">
                Round Average Score</td>
            <td style="padding:8px 12px; font-size:11px;">{score_bar(avg)}</td>
        </tr>""")

    summary_card_html = "".join(summary_card_rows)

    # ── Candidate Profile: Only include non-blank / non-null fields ───────────
    PROFILE_FIELDS = [
        ("Qualification",              fb.qualification),
        ("Current Organisation",       fb.current_organization),
        ("Organisation Location",      fb.current_organization_location),
        ("Current Designation",        fb.current_designation),
        ("Current Location",           fb.current_location),
        ("Hometown",                   fb.hometown),
        ("Preferred Location",         fb.preferred_location),
        ("Work Mode",                  fb.work_mode),
        ("Current CTC",                fb.current_ctc),
        ("Expected CTC",               fb.expected_ctc),
        ("Notice Period",              fb.notice_period),
        ("Bond",                       fb.bond),
        ("Reason for Job Change",      fb.job_change_reason),
        ("Role & Responsibility",      fb.role_responsibility),
    ]

    valid_profile = [
        (label, str(val).strip()) for label, val in PROFILE_FIELDS
        if is_valid_str(val)
    ]

    profile_table = ""
    if valid_profile:
        rows = "".join(
            info_row(label, val, alt=(i % 2 == 1))
            for i, (label, val) in enumerate(valid_profile)
        )
        profile_table = f"""
        <div style="background:#1e3a5f; color:#ffffff; padding:7px 12px;
                    font-size:12px; font-weight:700; border:1px solid #1e3a5f; margin-top:14px;">
            Candidate Profile &amp; Interview Details
        </div>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px; border-collapse:collapse;">
            {rows}
        </table>"""

    # ── Notes & Observations: Only include non-blank / non-null fields ────────
    def notes_block(label, value):
        if not is_valid_str(value):
            return ""
        return f"""
        <div style="margin-bottom:12px; page-break-inside:avoid;">
            <div style="background:#1e3a5f; color:#fff; padding:7px 12px;
                        font-size:11px; font-weight:700; margin-bottom:0;">{label}</div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0;
                        padding:10px 12px; font-size:11px; color:#1e293b;
                        line-height:1.5;">{value}</div>
        </div>"""

    NOTES_FIELDS = [
        ("Strengths",                                    fb.strengths),
        ("Areas of Improvement",                         fb.areas_of_improvement),
        ("Strength & Areas of Improvement",              fb.strength_areas_of_improvement),
        ("Goals",                                        fb.goals),
        ("Goals & Development Plan",                     fb.goals_development_plan),
        ("Behavioural & Cultural Fit",                   fb.behavioral_cultural_fit),
        ("Personal Background",                          fb.personal_background),
        ("Motivation for Change / Career Aspirations",   fb.motivation_for_change_career_aspirations),
        ("Achievement Orientation & Impact",             fb.achievement_orientation_impact),
        ("Stability / Reliability / Commitment",          fb.satbility_reliability_commitment),
        ("Comments & Overall Impression",                fb.comments),
        ("Behavioural Observations",                     fb.behavioral if is_valid_str(fb.behavioral) and str(fb.behavioral).strip() != "0" else None),
    ]

    notes_section = "".join(
        notes_block(label, val)
        for label, val in NOTES_FIELDS
        if is_valid_str(val) and str(val).strip() != "0"
    )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 12mm 15mm 20mm 15mm;
        @frame footer_frame {{
            -pdf-frame-content: footer_content;
            left: 15mm; right: 15mm; bottom: 5mm; height: 10mm;
        }}
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        font-size: 11px;
        color: #1e293b;
        background: #ffffff;
        margin: 0;
    }}
    table {{ border-collapse: collapse; width: 100%; }}
</style>
</head>
<body>

<!-- Footer -->
<div id="footer_content" style="text-align:center; font-size:9px; color:#94a3b8;
     border-top:1px solid #e2e8f0; padding-top:6px;">
    Knowcraft Analytics Private Limited &nbsp;|&nbsp; Confidential – HR Use Only
    &nbsp;|&nbsp; Generated on {created_str}
</div>

<!-- Header -->
<div style="text-align:center; margin-bottom:16px;">
    <div style="margin-bottom:8px;">{logo_tag}</div>
    <div style="font-size:18px; font-weight:700; color:#1e3a5f; margin-bottom:4px;">
        Interview Feedback Form
    </div>
    <div style="font-size:11px; color:#64748b; margin-bottom:10px;">
        Human Resources &nbsp;•&nbsp; Talent Acquisition
        &nbsp;&nbsp;
        <span style="background:#fef2f2; color:#991b1b; font-size:10px;
                     font-weight:700; padding:2px 8px; border:1px solid #fecaca;">
            CONFIDENTIAL
        </span>
    </div>
    <div style="border-bottom:2px solid #1e3a5f; width:100%;"></div>
</div>

<!-- Summary Card -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f7ff; border-left:1px solid #bfdbfe;
              border-right:1px solid #bfdbfe;
              border-top:4px solid #1e3a5f; margin-bottom:16px;">
    {summary_card_html}
</table>

<!-- Hiring Recommendation -->
<div style="text-align:center; margin-bottom:16px;">
    <span style="display:inline-block; background:{badge_bg}; color:{badge_fg};
                 border:2px solid {badge_fg}; border-radius:6px;
                 padding:8px 24px; font-size:13px; font-weight:700;">
        Hiring Recommendation: {badge_label}
    </span>
</div>

<!-- Ratings Sections (Only rendered if evaluated in this round) -->
{core_ratings_table}
{leadership_ratings_table}

<!-- Candidate Profile (Only rendered if fields are filled) -->
{profile_table}

<!-- Notes & Observations (Only rendered if filled) -->
{notes_section}

<p style="font-size:10px; color:#64748b; margin-top:20px; text-align:center;">
    This document is auto-generated by the Knowcraft HRMS. For queries, contact HR.
</p>

</body>
</html>"""

    pdf_bytes = html_to_pdf(html)
    safe = candidate_name.replace(" ", "_").replace("/", "_")
    filename = f"Interview_Feedback_{fb.interview_round or 'round'}_{safe}.pdf"
    return (filename, pdf_bytes, "application/pdf")
