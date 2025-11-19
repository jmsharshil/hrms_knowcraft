from django.template.loader import render_to_string
# from weasyprint import HTML
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

# def html_to_pdf(template_name, context):
#     html_string = render_to_string(template_name, context)
#     pdf_bytes = HTML(string=html_string).write_pdf()
#     return pdf_bytes

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

    c.drawString(100, 750, f"Offer Letter for {candidate.name}")
    c.drawString(100, 730, f"Email: {candidate.email}")
    c.save()

    buffer.seek(0)
    pdf_bytes = buffer.read()

    filename = f"offer_letter_{candidate.id}.pdf"
    return (filename, pdf_bytes, "application/pdf")