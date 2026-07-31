from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestVisitorVisit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Visit = cls.env['visitor.visit']
        cls.location = cls.env['visitor.location'].create({'name': 'Test HQ', 'code': 'THQ'})
        cls.gate = cls.env['visitor.gate'].create({
            'name': 'Test Gate', 'location_id': cls.location.id,
        })
        cls.host = cls.env['visitor.host'].create({'name': 'Test Host'})
        cls.guest = cls.env['visitor.guest'].create({
            'name': 'Test Guest', 'identity_type': 'passport', 'identity_number': 'PTEST001',
        })

    def _create_visit(self, **overrides):
        now = fields.Datetime.now()
        vals = {
            'guest_id': self.guest.id,
            'host_id': self.host.id,
            'location_id': self.location.id,
            'gate_id': self.gate.id,
            'visit_purpose': 'Test purpose',
            'visit_start': now,
            'visit_end': now + timedelta(hours=2),
        }
        vals.update(overrides)
        return self.Visit.create(vals)

    def test_sequence_name_generated(self):
        visit = self._create_visit()
        self.assertTrue(visit.name and visit.name != 'New')
        self.assertIn('VIS/', visit.name)

    def test_full_workflow_checkin_checkout(self):
        visit = self._create_visit()
        self.assertEqual(visit.state, 'draft')

        visit.action_submit()
        self.assertEqual(visit.state, 'pending_approval')

        visit.action_approve()
        self.assertIn(visit.state, ('approved', 'scheduled'))
        self.assertTrue(visit.qr_token)

        token = visit.qr_token
        result = self.Visit._process_checkin(token, gate_id=self.gate.id)
        self.assertTrue(result['ok'])
        self.assertEqual(visit.state, 'checked_in')
        self.assertTrue(visit.check_in_datetime)

        result = self.Visit._process_checkout(token, gate_id=self.gate.id)
        self.assertTrue(result['ok'])
        self.assertEqual(visit.state, 'checked_out')
        self.assertFalse(visit.qr_token)

    def test_qr_reuse_prevention_after_checkin(self):
        visit = self._create_visit()
        visit.action_submit()
        visit.action_approve()
        token = visit.qr_token

        first = self.Visit._process_checkin(token, gate_id=self.gate.id)
        self.assertTrue(first['ok'])

        second = self.Visit._process_checkin(token, gate_id=self.gate.id)
        self.assertFalse(second['ok'], 'A checked-in visit must not be checkable-in again with the same token.')

    def test_qr_reuse_prevention_after_checkout(self):
        visit = self._create_visit()
        visit.action_submit()
        visit.action_approve()
        token = visit.qr_token
        self.Visit._process_checkin(token, gate_id=self.gate.id)
        self.Visit._process_checkout(token, gate_id=self.gate.id)

        replay = self.Visit._process_checkin(token, gate_id=self.gate.id)
        self.assertFalse(replay['ok'], 'A consumed token must not be usable again.')

    def test_qr_expiry_outside_window(self):
        past_start = fields.Datetime.now() - timedelta(hours=5)
        visit = self._create_visit(
            visit_start=past_start, visit_end=past_start + timedelta(hours=1),
            entry_grace_minutes=0,
        )
        visit.action_submit()
        visit.action_approve()
        result = self.Visit._process_checkin(visit.qr_token, gate_id=self.gate.id)
        self.assertFalse(result['ok'])

    def test_invalid_token_rejected(self):
        result = self.Visit._process_checkin('does-not-exist', gate_id=self.gate.id)
        self.assertFalse(result['ok'])
        result = self.Visit._process_checkout('does-not-exist', gate_id=self.gate.id)
        self.assertFalse(result['ok'])

    def test_blacklisted_guest_blocks_approval(self):
        self.env['visitor.blacklist'].create({
            'name': self.guest.name,
            'identity_type': self.guest.identity_type,
            'identity_number': self.guest.identity_number,
            'reason': 'Test blacklist',
        })
        visit = self._create_visit()
        visit.action_submit()
        visit.action_approve()
        self.assertEqual(visit.state, 'blacklisted')
        self.assertFalse(visit.qr_token)

    def test_cancel_revokes_token(self):
        visit = self._create_visit()
        visit.action_submit()
        visit.action_approve()
        self.assertTrue(visit.qr_token)
        visit.action_cancel()
        self.assertEqual(visit.state, 'cancelled')
        self.assertFalse(visit.qr_token)
        result = self.Visit._process_checkin(
            'irrelevant', gate_id=self.gate.id)
        self.assertFalse(result['ok'])

    def test_cannot_approve_twice(self):
        visit = self._create_visit()
        visit.action_submit()
        visit.action_approve()
        with self.assertRaises(UserError):
            visit.action_approve()

    def test_checkpoint_log_is_immutable(self):
        visit = self._create_visit()
        visit.action_submit()
        visit.action_approve()
        self.Visit._process_checkin(visit.qr_token, gate_id=self.gate.id)
        log = visit.checkpoint_log_ids[:1]
        self.assertTrue(log)
        # Use a real (non-superuser) admin account: env.su only bypasses
        # the immutability guard for literal sudo()/superuser code, which
        # is the intended escape hatch - a regular user, even a powerful
        # one, must never be able to edit the audit trail.
        admin = self.env.ref('base.user_admin')
        from odoo.exceptions import AccessError
        with self.assertRaises(AccessError):
            log.with_user(admin).write({'note': 'tampered'})
        with self.assertRaises(AccessError):
            log.with_user(admin).unlink()
