from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestEssRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Request = cls.env['ess.request']
        cls.request_type = cls.env['ess.request.type'].create({
            'name': 'Test Type', 'code': 'test_type', 'requester_kind': 'employee',
        })
        cls.employee = cls.env['hr.employee'].create({'name': 'Test Employee'})
        cls.partner = cls.env['res.partner'].create({'name': 'Test Client Co', 'company_type': 'company'})

    def _create_employee_request(self):
        return self.Request.create({
            'request_type_id': self.request_type.id,
            'requester_kind': 'employee',
            'employee_id': self.employee.id,
            'subject': 'Test request',
        })

    def test_sequence_name_generated(self):
        req = self._create_employee_request()
        self.assertTrue(req.name and req.name != 'New')
        self.assertIn('REQ/', req.name)

    def test_initial_status_history_logged(self):
        req = self._create_employee_request()
        self.assertEqual(len(req.status_history_ids), 1)
        self.assertEqual(req.status_history_ids.to_state, 'draft')

    def test_full_workflow(self):
        req = self._create_employee_request()
        req.action_submit()
        self.assertEqual(req.state, 'submitted')
        req.action_approve()
        self.assertEqual(req.state, 'approved')
        req.action_start_progress()
        self.assertEqual(req.state, 'in_progress')
        req.action_complete()
        self.assertEqual(req.state, 'completed')
        req.action_close()
        self.assertEqual(req.state, 'closed')
        self.assertTrue(req.closed_date)
        # 6 transitions: draft->submitted->approved->in_progress->completed->closed
        self.assertEqual(len(req.status_history_ids), 6)

    def test_reject_workflow(self):
        req = self._create_employee_request()
        req.action_submit()
        req.action_reject(reason='Not eligible')
        self.assertEqual(req.state, 'rejected')

    def test_cannot_approve_draft(self):
        req = self._create_employee_request()
        with self.assertRaises(UserError):
            req.action_approve()

    def test_cannot_double_close(self):
        req = self._create_employee_request()
        req.action_submit()
        req.action_approve()
        req.action_start_progress()
        req.action_complete()
        req.action_close()
        with self.assertRaises(UserError):
            req.action_close()

    def test_rating_only_after_closed(self):
        req = self._create_employee_request()
        with self.assertRaises(UserError):
            req.action_rate('5')
        req.action_submit()
        req.action_approve()
        req.action_start_progress()
        req.action_complete()
        req.action_close()
        req.action_rate('5')
        self.assertEqual(req.customer_rating, '5')

    def test_cancel_from_draft(self):
        req = self._create_employee_request()
        req.action_cancel()
        self.assertEqual(req.state, 'cancelled')

    def test_client_request_requires_partner(self):
        with self.assertRaises(Exception):
            self.Request.create({
                'request_type_id': self.request_type.id,
                'requester_kind': 'client',
                'subject': 'Missing partner',
            })

    def test_notification_created_on_submit(self):
        user = self.env['res.users'].create({
            'name': 'Notif Employee', 'login': 'notif_employee_test',
            'email': 'notif_employee_test@example.com',
        })
        employee = self.env['hr.employee'].create({'name': 'Notif Employee', 'user_id': user.id})
        req = self.Request.create({
            'request_type_id': self.request_type.id,
            'requester_kind': 'employee',
            'employee_id': employee.id,
            'subject': 'Notify me',
        })
        req.action_submit()
        notif = self.env['ess.portal.notification'].search([('request_id', '=', req.id)])
        self.assertTrue(notif)
        self.assertEqual(notif.user_id, user)

    def test_status_history_is_immutable(self):
        from odoo.exceptions import AccessError
        req = self._create_employee_request()
        history = req.status_history_ids[:1]
        admin = self.env.ref('base.user_admin')
        with self.assertRaises(AccessError):
            history.with_user(admin).write({'note': 'tampered'})
