from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestEssRequestSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request_type = cls.env['ess.request.type'].create({
            'name': 'Security Test Type', 'code': 'sec_test_type', 'requester_kind': 'both',
        })
        cls.group_client = cls.env.ref('employee_client_self_service_portal.group_ess_client')
        cls.group_manager = cls.env.ref('employee_client_self_service_portal.group_ess_request_manager')

        cls.user_employee_1 = cls.env['res.users'].create({
            'name': 'Sec Employee 1', 'login': 'sec_employee_1',
            'email': 'sec_employee_1@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.employee_1 = cls.env['hr.employee'].create({
            'name': 'Sec Employee 1', 'user_id': cls.user_employee_1.id,
        })
        cls.user_employee_2 = cls.env['res.users'].create({
            'name': 'Sec Employee 2', 'login': 'sec_employee_2',
            'email': 'sec_employee_2@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.employee_2 = cls.env['hr.employee'].create({
            'name': 'Sec Employee 2', 'user_id': cls.user_employee_2.id,
        })

        cls.partner_client_a = cls.env['res.partner'].create({'name': 'Client A', 'company_type': 'company'})
        cls.user_client_a = cls.env['res.users'].create({
            'name': 'Client A User', 'login': 'sec_client_a',
            'email': 'sec_client_a@example.com',
            'partner_id': cls.partner_client_a.id,
            'groups_id': [(6, 0, [cls.group_client.id])],
        })
        cls.partner_client_b = cls.env['res.partner'].create({'name': 'Client B', 'company_type': 'company'})
        cls.user_client_b = cls.env['res.users'].create({
            'name': 'Client B User', 'login': 'sec_client_b',
            'email': 'sec_client_b@example.com',
            'partner_id': cls.partner_client_b.id,
            'groups_id': [(6, 0, [cls.group_client.id])],
        })

        cls.user_manager = cls.env['res.users'].create({
            'name': 'Sec Manager', 'login': 'sec_manager',
            'email': 'sec_manager@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.group_manager.id])],
        })

    def test_employee_cannot_approve_own_request(self):
        req = self.env['ess.request'].create({
            'request_type_id': self.request_type.id, 'requester_kind': 'employee',
            'employee_id': self.employee_1.id, 'subject': 'Approve me',
        })
        req.with_user(self.user_employee_1).action_submit()
        with self.assertRaises(AccessError):
            req.with_user(self.user_employee_1).action_approve()

    def test_manager_can_approve(self):
        req = self.env['ess.request'].create({
            'request_type_id': self.request_type.id, 'requester_kind': 'employee',
            'employee_id': self.employee_1.id, 'subject': 'Approve me',
        })
        req.action_submit()
        req.with_user(self.user_manager).action_approve()
        self.assertEqual(req.state, 'approved')

    def test_employee_cannot_see_another_employees_request(self):
        req_1 = self.env['ess.request'].create({
            'request_type_id': self.request_type.id, 'requester_kind': 'employee',
            'employee_id': self.employee_1.id, 'subject': 'Employee 1 request',
        })
        req_2 = self.env['ess.request'].create({
            'request_type_id': self.request_type.id, 'requester_kind': 'employee',
            'employee_id': self.employee_2.id, 'subject': 'Employee 2 request',
        })
        visible = self.env['ess.request'].with_user(self.user_employee_1).search([
            ('id', 'in', (req_1 | req_2).ids)
        ])
        self.assertIn(req_1.id, visible.ids)
        self.assertNotIn(req_2.id, visible.ids)

    def test_client_cannot_see_another_clients_request(self):
        req_a = self.env['ess.request'].create({
            'request_type_id': self.request_type.id, 'requester_kind': 'client',
            'partner_id': self.partner_client_a.id, 'subject': 'Client A request',
        })
        req_b = self.env['ess.request'].create({
            'request_type_id': self.request_type.id, 'requester_kind': 'client',
            'partner_id': self.partner_client_b.id, 'subject': 'Client B request',
        })
        visible = self.env['ess.request'].with_user(self.user_client_a).search([
            ('id', 'in', (req_a | req_b).ids)
        ])
        self.assertIn(req_a.id, visible.ids)
        self.assertNotIn(req_b.id, visible.ids)

    def test_client_cannot_create_request_for_another_client(self):
        with self.assertRaises(AccessError):
            self.env['ess.request'].with_user(self.user_client_a).create({
                'request_type_id': self.request_type.id, 'requester_kind': 'client',
                'partner_id': self.partner_client_b.id, 'subject': 'Trying to impersonate Client B',
            })

    def test_manager_sees_all_company_requests(self):
        req_1 = self.env['ess.request'].create({
            'request_type_id': self.request_type.id, 'requester_kind': 'employee',
            'employee_id': self.employee_1.id, 'subject': 'Employee 1 request',
        })
        req_2 = self.env['ess.request'].create({
            'request_type_id': self.request_type.id, 'requester_kind': 'client',
            'partner_id': self.partner_client_a.id, 'subject': 'Client A request',
        })
        visible = self.env['ess.request'].with_user(self.user_manager).search([
            ('id', 'in', (req_1 | req_2).ids)
        ])
        self.assertEqual(len(visible), 2)
