from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestVisitorSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env['res.company'].create({'name': 'Test Company B'})

        cls.location_a = cls.env['visitor.location'].create({
            'name': 'Location A', 'company_id': cls.company_a.id,
        })
        cls.location_b = cls.env['visitor.location'].create({
            'name': 'Location B', 'company_id': cls.company_b.id,
        })

        cls.group_host = cls.env.ref('smart_visitor_management.group_visitor_host')
        cls.group_receptionist = cls.env.ref('smart_visitor_management.group_visitor_receptionist')
        cls.group_security = cls.env.ref('smart_visitor_management.group_visitor_security')
        cls.group_manager = cls.env.ref('smart_visitor_management.group_visitor_manager')

        def make_user(login, group, companies):
            return cls.env['res.users'].create({
                'name': login,
                'login': login,
                'email': f'{login}@example.com',
                'groups_id': [(6, 0, [group.id, cls.env.ref('base.group_user').id])],
                'company_ids': [(6, 0, [c.id for c in companies])],
                'company_id': companies[0].id,
            })

        cls.user_host_1 = make_user('visitor_host_1', cls.group_host, [cls.company_a])
        cls.user_host_2 = make_user('visitor_host_2', cls.group_host, [cls.company_a])
        cls.user_receptionist = make_user('visitor_reception', cls.group_receptionist, [cls.company_a])
        cls.user_security = make_user('visitor_security', cls.group_security, [cls.company_a])
        cls.user_manager = make_user('visitor_manager', cls.group_manager, [cls.company_a, cls.company_b])

        cls.host_1 = cls.env['visitor.host'].create({
            'name': 'Host One', 'user_id': cls.user_host_1.id, 'company_id': cls.company_a.id,
        })
        cls.host_2 = cls.env['visitor.host'].create({
            'name': 'Host Two', 'user_id': cls.user_host_2.id, 'company_id': cls.company_a.id,
        })
        cls.guest = cls.env['visitor.guest'].create({
            'name': 'Sec Guest', 'identity_type': 'passport', 'identity_number': 'SEC001',
        })

    def _make_visit(self, host, company, location):
        now = fields.Datetime.now()
        return self.env['visitor.visit'].create({
            'guest_id': self.guest.id,
            'host_id': host.id,
            'company_id': company.id,
            'location_id': location.id,
            'visit_purpose': 'Security test',
            'visit_start': now,
            'visit_end': now + timedelta(hours=1),
        })

    def test_host_cannot_approve_own_visit(self):
        visit = self._make_visit(self.host_1, self.company_a, self.location_a)
        visit.with_user(self.user_host_1).action_submit()
        with self.assertRaises(AccessError):
            visit.with_user(self.user_host_1).action_approve()

    def test_receptionist_cannot_approve(self):
        visit = self._make_visit(self.host_1, self.company_a, self.location_a)
        visit.action_submit()
        with self.assertRaises(AccessError):
            visit.with_user(self.user_receptionist).action_approve()

    def test_manager_can_approve(self):
        visit = self._make_visit(self.host_1, self.company_a, self.location_a)
        visit.action_submit()
        visit.with_user(self.user_manager).action_approve()
        self.assertIn(visit.state, ('approved', 'scheduled'))

    def test_host_sees_only_own_visits(self):
        visit_of_host_1 = self._make_visit(self.host_1, self.company_a, self.location_a)
        visit_of_host_2 = self._make_visit(self.host_2, self.company_a, self.location_a)

        visits_visible_to_host_1 = self.env['visitor.visit'].with_user(self.user_host_1).search([
            ('id', 'in', (visit_of_host_1 | visit_of_host_2).ids)
        ])
        self.assertIn(visit_of_host_1.id, visits_visible_to_host_1.ids)
        self.assertNotIn(visit_of_host_2.id, visits_visible_to_host_1.ids,
                          'A host must not be able to see another host\'s visits (IDOR).')

    def test_multi_company_isolation(self):
        visit_a = self._make_visit(self.host_1, self.company_a, self.location_a)
        visit_b = self.env['visitor.visit'].create({
            'guest_id': self.guest.id,
            'host_id': self.host_1.id,
            'company_id': self.company_b.id,
            'location_id': self.location_b.id,
            'visit_purpose': 'Company B visit',
            'visit_start': fields.Datetime.now(),
            'visit_end': fields.Datetime.now() + timedelta(hours=1),
        })

        # user_manager only has company A allowed by default (company_b is
        # an *allowed* company but not the active one); restrict context
        # to company A only to simulate a user who never switched company.
        visible = self.env['visitor.visit'].with_user(self.user_manager).with_context(
            allowed_company_ids=[self.company_a.id]
        ).search([('id', 'in', (visit_a | visit_b).ids)])
        self.assertIn(visit_a.id, visible.ids)
        self.assertNotIn(visit_b.id, visible.ids)

    def test_security_officer_has_no_direct_write_access(self):
        visit = self._make_visit(self.host_1, self.company_a, self.location_a)
        visit.action_submit()
        visit.action_approve()
        with self.assertRaises(AccessError):
            visit.with_user(self.user_security).write({'visit_purpose': 'Hacked'})

    def test_security_officer_can_perform_manual_checkin(self):
        visit = self._make_visit(self.host_1, self.company_a, self.location_a)
        visit.action_submit()
        visit.action_approve()
        # The security officer has no 'write' ACL on visitor.visit, yet the
        # check-in action must still work because the mutation happens
        # inside a narrowly-scoped sudo() call, not via direct user write.
        visit.with_user(self.user_security).action_manual_checkin()
        self.assertEqual(visit.state, 'checked_in')

    def test_host_cannot_manually_checkin(self):
        visit = self._make_visit(self.host_1, self.company_a, self.location_a)
        visit.action_submit()
        visit.action_approve()
        with self.assertRaises(AccessError):
            visit.with_user(self.user_host_1).action_manual_checkin()
