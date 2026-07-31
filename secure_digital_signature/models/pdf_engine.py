"""PDF signing engine.

Uses PyPDF2 and reportlab only - both are already core Odoo Python
dependencies (see odoo/requirements.txt), so this module does not add any
new external dependency to the app.
"""
import hashlib
import io

from PyPDF2 import PdfReader, PdfWriter
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def get_page_sizes(pdf_bytes):
    """Return a list of (width_pt, height_pt) for every page."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    sizes = []
    for page in reader.pages:
        box = page.mediabox
        sizes.append((float(box.width), float(box.height)))
    return sizes


def get_page_count(pdf_bytes):
    return len(PdfReader(io.BytesIO(pdf_bytes)).pages)


def _draw_field(c, field, width_pt, height_pt):
    """Draw a single field onto a reportlab canvas. Coordinates are stored
    as percentages (0-100) from the top-left of the page; reportlab's
    origin is bottom-left, so the Y axis is flipped here."""
    x = field['pos_x'] / 100.0 * width_pt
    w = field['width'] / 100.0 * width_pt
    h = field['height'] / 100.0 * height_pt
    y_top = field['pos_y'] / 100.0 * height_pt
    y = height_pt - y_top - h

    field_type = field['field_type']
    if field_type in ('signature', 'initials', 'stamp') and field.get('signature_image'):
        try:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(io.BytesIO(field['signature_image']))
            c.drawImage(img, x, y, width=w, height=h,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            c.setFont('Helvetica-Oblique', 8)
            c.drawString(x, y + h / 2, '[signature]')
    elif field_type == 'checkbox':
        c.rect(x, y, min(w, h), min(w, h))
        if field.get('value') == 'True':
            c.setFont('Helvetica-Bold', min(w, h))
            c.drawString(x + 1, y + 1, 'X')
    else:
        c.setFont('Helvetica', max(6, min(12, h * 0.6)))
        c.drawString(x, y + h * 0.25, str(field.get('value') or ''))
    c.setFont('Helvetica', 5)
    c.setFillGray(0.6)
    c.drawString(x, y - 6, field.get('signer_label', ''))
    c.setFillGray(0)


def build_overlay_pdf(width_pt, height_pt, fields):
    """Build a single-page, transparent-background PDF with the given
    fields drawn at their stored positions."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width_pt, height_pt))
    for field in fields:
        _draw_field(c, field, width_pt, height_pt)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


def apply_fields_to_pdf(original_bytes, fields_by_page):
    """fields_by_page: {page_number(1-indexed): [field_dict, ...]}
    Returns the final PDF bytes with every field burned into its page."""
    reader = PdfReader(io.BytesIO(original_bytes))
    writer = PdfWriter()

    for index, page in enumerate(reader.pages):
        page_number = index + 1
        fields = fields_by_page.get(page_number)
        if fields:
            width_pt = float(page.mediabox.width)
            height_pt = float(page.mediabox.height)
            overlay_bytes = build_overlay_pdf(width_pt, height_pt, fields)
            overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()


def build_certificate_pdf(request_name, subject, signers, original_hash, final_hash, verify_url):
    """A small, self-contained completion certificate page."""
    buf = io.BytesIO()
    width_pt, height_pt = letter
    c = canvas.Canvas(buf, pagesize=letter)

    c.setFont('Helvetica-Bold', 16)
    c.drawString(20 * mm, height_pt - 25 * mm, 'Signature Completion Certificate')

    c.setFont('Helvetica', 10)
    y = height_pt - 40 * mm
    c.drawString(20 * mm, y, f'Request: {request_name}')
    y -= 6 * mm
    c.drawString(20 * mm, y, f'Subject: {subject}')
    y -= 10 * mm

    c.setFont('Helvetica-Bold', 11)
    c.drawString(20 * mm, y, 'Signers')
    y -= 6 * mm
    c.setFont('Helvetica', 9)
    for signer in signers:
        line = (f"- {signer['name']} <{signer['email']}> "
                f"signed {signer['signed_date'] or '-'} "
                f"from IP {signer['signed_ip'] or '-'}")
        c.drawString(22 * mm, y, line[:110])
        y -= 5 * mm

    y -= 8 * mm
    c.setFont('Helvetica-Bold', 11)
    c.drawString(20 * mm, y, 'Document Integrity')
    y -= 6 * mm
    c.setFont('Helvetica', 8)
    c.drawString(20 * mm, y, f'Original SHA-256: {original_hash}')
    y -= 5 * mm
    c.drawString(20 * mm, y, f'Final SHA-256: {final_hash}')

    if verify_url:
        qr = QrCodeWidget(verify_url)
        bounds = qr.getBounds()
        qr_size = 35 * mm
        w = bounds[2] - bounds[0]
        h = bounds[3] - bounds[1]
        drawing = Drawing(qr_size, qr_size, transform=[qr_size / w, 0, 0, qr_size / h, 0, 0])
        drawing.add(qr)
        renderPDF.draw(drawing, c, 20 * mm, 20 * mm)
        c.setFont('Helvetica', 7)
        c.drawString(20 * mm, 16 * mm, 'Scan to verify this document online')

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
