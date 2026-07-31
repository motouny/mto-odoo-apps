import base64
import io

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


def _make_pdf_bytes():
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 700, 'Security test document')
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


@tagged('post_install', '-at_install')
class TestDigitalSignatureSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pdf_bytes = _make_pdf_bytes()
        cls.group_user = cls.env.ref('secure_digital_signature.group_signature_user')
        cls.group_manager = cls.env.ref('secure_digital_signature.group_signature_manager')

        cls.user_a = cls.env['res.users'].create({
            'name': 'Signature User A', 'login': 'sig_user_a', 'email': 'sig_user_a@example.com',
            'groups_id': [(6, 0, [cls.group_user.id])],
        })
        cls.user_b = cls.env['res.users'].create({
            'name': 'Signature User B', 'login': 'sig_user_b', 'email': 'sig_user_b@example.com',
            'groups_id': [(6, 0, [cls.group_user.id])],
        })
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Signature Manager', 'login': 'sig_manager', 'email': 'sig_manager@example.com',
            'groups_id': [(6, 0, [cls.group_manager.id])],
        })

    def _create_request_as(self, user):
        request = self.env['digital.signature.request'].with_user(user).create({
            'subject': 'Owned by %s' % user.name,
        })
        request.with_user(user).write({
            'original_file': base64.b64encode(self.pdf_bytes),
            'original_filename': 'x.pdf',
        })
        return request

    def test_user_sees_only_own_requests(self):
        request_a = self._create_request_as(self.user_a)
        request_b = self._create_request_as(self.user_b)

        visible = self.env['digital.signature.request'].with_user(self.user_a).search([
            ('id', 'in', (request_a | request_b).ids)
        ])
        self.assertIn(request_a.id, visible.ids)
        self.assertNotIn(request_b.id, visible.ids)

    def test_manager_sees_all_requests(self):
        request_a = self._create_request_as(self.user_a)
        request_b = self._create_request_as(self.user_b)

        visible = self.env['digital.signature.request'].with_user(self.user_manager).search([
            ('id', 'in', (request_a | request_b).ids)
        ])
        self.assertEqual(len(visible), 2)

    def test_user_b_cannot_write_user_as_request(self):
        request_a = self._create_request_as(self.user_a)
        with self.assertRaises(AccessError):
            request_a.with_user(self.user_b).write({'subject': 'Hacked'})

    def test_user_cannot_see_others_signers(self):
        request_a = self._create_request_as(self.user_a)
        signer_a = self.env['digital.signature.signer'].with_user(self.user_a).create({
            'request_id': request_a.id, 'signer_type': 'external',
            'name': 'External Signer', 'email': 'ext@example.com',
        })
        visible = self.env['digital.signature.signer'].with_user(self.user_b).search([
            ('id', '=', signer_a.id)
        ])
        self.assertFalse(visible)

    def test_audit_events_are_immutable_even_for_admin(self):
        request_a = self._create_request_as(self.user_a)
        event = request_a.event_ids[:1]
        self.assertTrue(event)
        admin = self.env.ref('base.user_admin')
        with self.assertRaises(AccessError):
            event.with_user(admin).write({'note': 'tampered'})
        with self.assertRaises(AccessError):
            event.with_user(admin).unlink()
