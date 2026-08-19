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
