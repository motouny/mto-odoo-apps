import base64
import io

from odoo.tests import tagged
from odoo.tests.common import HttpCase


def _make_pdf_bytes():
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 700, 'Portal test document')
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


@tagged('post_install', '-at_install')
class TestPortalSigning(HttpCase):

    def setUp(self):
        super().setUp()
        self.request = self.env['digital.signature.request'].create({
            'subject': 'Portal Test Agreement',
        })
        self.request.write({
            'original_file': base64.b64encode(_make_pdf_bytes()),
            'original_filename': 'x.pdf',
        })
        self.signer = self.env['digital.signature.signer'].create({
            'request_id': self.request.id, 'signer_type': 'external',
            'name': 'Portal Signer', 'email': 'portal.signer@example.com',
        })
        self.env['digital.signature.field'].create({
            'request_id': self.request.id, 'signer_id': self.signer.id,
            'field_type': 'name', 'page_number': 1,
            'pos_x': 10, 'pos_y': 80, 'width': 20, 'height': 5,
        })
        self.request.action_mark_ready()
        self.request.action_send()

    def test_sign_page_accessible_with_valid_token(self):
        response = self.url_open('/sign/%s' % self.signer.token)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Portal Test Agreement', response.text)

    def test_sign_page_404_on_invalid_token(self):
        response = self.url_open('/sign/does-not-exist')
        self.assertEqual(response.status_code, 404)

    def test_token_not_guessable_from_record_id(self):
        self.assertNotEqual(self.signer.token, str(self.signer.id))
        response = self.url_open('/sign/%s' % self.signer.id)
        self.assertEqual(response.status_code, 404)

    def test_verification_page_shows_not_found_for_bad_token(self):
        response = self.url_open('/sign/verify/does-not-exist')
        self.assertEqual(response.status_code, 200)
        self.assertIn('No document was found', response.text)

    def test_verification_page_shows_valid_for_completed_request(self):
        self.signer.field_ids.write({'value': 'Portal Signer'})
        self.request._signer_sign(self.signer, ip_address='1.1.1.1', user_agent='test')
        response = self.url_open('/sign/verify/%s' % self.request.verification_token)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Valid', response.text)
