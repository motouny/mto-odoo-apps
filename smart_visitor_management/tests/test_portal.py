from datetime import timedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestVisitorPortal(HttpCase):

    def setUp(self):
        super().setUp()
        now = fields.Datetime.now()
        self.location = self.env['visitor.location'].create({'name': 'Portal Test HQ'})
        self.host = self.env['visitor.host'].create({'name': 'Portal Host'})
        self.guest = self.env['visitor.guest'].create({
            'name': 'Portal Guest', 'identity_type': 'passport', 'identity_number': 'PORTAL001',
        })
        self.visit = self.env['visitor.visit'].create({
            'guest_id': self.guest.id,
            'host_id': self.host.id,
            'location_id': self.location.id,
            'visit_purpose': 'Portal test',
            'visit_start': now,
            'visit_end': now + timedelta(hours=2),
        })

    def test_invitation_page_accessible_with_valid_token(self):
        response = self.url_open('/visitor/invitation/%s' % self.visit.invitation_token)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Visitor Invitation', response.text)

    def test_invitation_page_404_on_invalid_token(self):
        response = self.url_open('/visitor/invitation/does-not-exist-token')
        self.assertEqual(response.status_code, 404)

    def test_invitation_token_not_guessable_from_record_id(self):
        # The token must not be derivable from (or equal to) the record id.
        self.assertNotEqual(self.visit.invitation_token, str(self.visit.id))
        response = self.url_open('/visitor/invitation/%s' % self.visit.id)
        self.assertEqual(response.status_code, 404)

    def test_invitation_submit_updates_guest_and_submits_visit(self):
        csrf_token = self._get_csrf_token()
        self.url_open(
            '/visitor/invitation/%s/submit' % self.visit.invitation_token,
            data={
                'name': 'Updated Guest Name',
                'identity_type': 'passport',
                'identity_number': 'PORTAL001-UPDATED',
                'mobile': '+1 555 0000',
                'csrf_token': csrf_token,
            },
        )
        self.visit.invalidate_recordset()
        self.assertTrue(self.visit.invitation_completed)
        self.assertEqual(self.visit.state, 'pending_approval')
        self.assertEqual(self.visit.guest_id.identity_number, 'PORTAL001-UPDATED')

    def _get_csrf_token(self):
        # Fetch a valid CSRF token bound to the current test session by
        # rendering the public page and reading it out of the DOM.
        page = self.url_open('/visitor/invitation/%s' % self.visit.invitation_token)
        html = page.text
        marker = 'name="csrf_token" value="'
        start = html.index(marker) + len(marker)
        end = html.index('"', start)
        return html[start:end]
