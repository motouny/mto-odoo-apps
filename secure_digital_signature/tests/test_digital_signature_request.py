import base64
import io

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


def _make_pdf_bytes(text='Test document'):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 700, text)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


@tagged('post_install', '-at_install')
class TestDigitalSignatureRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Request = cls.env['digital.signature.request']
        cls.pdf_bytes = _make_pdf_bytes()

    def _create_request(self, signing_mode='sequential', signer_count=2):
        request = self.Request.create({
            'subject': 'Test Agreement',
            'signing_mode': signing_mode,
        })
        request.write({
            'original_file': base64.b64encode(self.pdf_bytes),
            'original_filename': 'test.pdf',
        })
        signers = self.env['digital.signature.signer']
        for i in range(signer_count):
            signer = self.env['digital.signature.signer'].create({
                'request_id': request.id,
                'sequence': (i + 1) * 10,
                'signer_type': 'external',
                'name': f'Signer {i + 1}',
                'email': f'signer{i + 1}@example.com',
            })
            self.env['digital.signature.field'].create({
                'request_id': request.id,
                'signer_id': signer.id,
                'field_type': 'name',
                'page_number': 1,
                'pos_x': 10, 'pos_y': 80, 'width': 20, 'height': 5,
            })
            signers |= signer
        return request, signers

    def test_original_hash_computed_on_upload(self):
        request, signers = self._create_request()
        self.assertTrue(request.original_hash)
        self.assertEqual(len(request.original_hash), 64)

    def test_cannot_mark_ready_without_signers(self):
        request = self.Request.create({'subject': 'Empty'})
        request.write({'original_file': base64.b64encode(self.pdf_bytes), 'original_filename': 'x.pdf'})
        with self.assertRaises(UserError):
            request.action_mark_ready()

    def test_sequential_workflow_full_completion(self):
        request, signers = self._create_request(signing_mode='sequential', signer_count=2)
        request.action_mark_ready()
        self.assertEqual(request.state, 'ready')
        request.action_send()
        self.assertEqual(request.state, 'sent')

        signer_1, signer_2 = signers[0], signers[1]
        self.assertEqual(signer_1.status, 'sent')
        self.assertEqual(signer_2.status, 'pending')
        self.assertTrue(signer_1.token)
        self.assertFalse(signer_2.token)

        signer_1.field_ids.write({'value': 'Signer One'})
        request._signer_sign(signer_1, ip_address='1.1.1.1', user_agent='test')
        self.assertEqual(signer_1.status, 'signed')
        self.assertEqual(signer_2.status, 'sent')
        self.assertTrue(signer_2.token)

        signer_2.field_ids.write({'value': 'Signer Two'})
        request._signer_sign(signer_2, ip_address='2.2.2.2', user_agent='test')
        self.assertEqual(signer_2.status, 'signed')
        self.assertEqual(request.state, 'completed')
        self.assertTrue(request.final_hash)
        self.assertTrue(request.final_document())
        self.assertTrue(request.certificate_document())

    def test_parallel_workflow(self):
        request, signers = self._create_request(signing_mode='parallel', signer_count=2)
        request.action_mark_ready()
        request.action_send()
        for signer in signers:
            self.assertEqual(signer.status, 'sent')
            self.assertTrue(signer.token)

        signers[0].field_ids.write({'value': 'A'})
        request._signer_sign(signers[0], ip_address='1.1.1.1', user_agent='test')
        self.assertEqual(request.state, 'partially_signed')

        signers[1].field_ids.write({'value': 'B'})
        request._signer_sign(signers[1], ip_address='2.2.2.2', user_agent='test')
        self.assertEqual(request.state, 'completed')

    def test_cannot_sign_without_required_fields(self):
        request, signers = self._create_request(signer_count=1)
        request.action_mark_ready()
        request.action_send()
        with self.assertRaises(UserError):
            request._signer_sign(signers[0], ip_address='1.1.1.1', user_agent='test')

    def test_rejection_revokes_all_tokens(self):
        request, signers = self._create_request(signing_mode='parallel', signer_count=2)
        request.action_mark_ready()
        request.action_send()
        request._signer_reject(signers[0], 'Not agreed', ip_address='1.1.1.1', user_agent='test')
        self.assertEqual(request.state, 'rejected')
        self.assertTrue(signers[0].token_revoked)
        self.assertTrue(signers[1].token_revoked)

    def test_signed_token_cannot_be_reused(self):
        request, signers = self._create_request(signer_count=1)
        request.action_mark_ready()
        request.action_send()
        signers[0].field_ids.write({'value': 'X'})
        request._signer_sign(signers[0], ip_address='1.1.1.1', user_agent='test')
        self.assertTrue(signers[0].token_revoked)
        with self.assertRaises(UserError):
            request._signer_sign(signers[0], ip_address='1.1.1.1', user_agent='test')

    def test_field_definition_locked_after_send(self):
        request, signers = self._create_request(signer_count=1)
        request.action_mark_ready()
        request.action_send()
        field = signers[0].field_ids[0]
        with self.assertRaises(UserError):
            field.write({'pos_x': 99})

    def test_original_document_cannot_be_replaced_after_draft(self):
        request, signers = self._create_request(signer_count=1)
        request.action_mark_ready()
        with self.assertRaises(UserError):
            request.write({'original_file': base64.b64encode(_make_pdf_bytes('other'))})

    def test_cancel_revokes_pending_tokens(self):
        request, signers = self._create_request(signer_count=1)
        request.action_mark_ready()
        request.action_send()
        request.action_cancel()
        self.assertEqual(request.state, 'cancelled')
        self.assertTrue(signers[0].token_revoked)

    def test_expire_cron(self):
        from datetime import timedelta
        from odoo import fields as odoo_fields
        request, signers = self._create_request(signer_count=1)
        request.action_mark_ready()
        request.expiration_date = odoo_fields.Datetime.now() - timedelta(days=1)
        request.action_send()
        self.Request._cron_expire_requests()
        self.assertEqual(request.state, 'expired')
        self.assertTrue(signers[0].token_revoked)
