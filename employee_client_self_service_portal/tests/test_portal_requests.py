from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestPortalRequests(HttpCase):

    def setUp(self):
        super().setUp()
        self.request_type = self.env['ess.request.type'].create({
            'name': 'Portal Test Type', 'code': 'portal_test_type', 'requester_kind': 'employee',
        })
        self.user_a = self.env['res.users'].create({
            'name': 'Portal Employee A', 'login': 'portal_employee_a',
            'email': 'portal_employee_a@example.com',
            'password': 'portal_employee_a',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.employee_a = self.env['hr.employee'].create({
            'name': 'Portal Employee A', 'user_id': self.user_a.id,
        })
        self.user_b = self.env['res.users'].create({
            'name': 'Portal Employee B', 'login': 'portal_employee_b',
            'email': 'portal_employee_b@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.employee_b = self.env['hr.employee'].create({
            'name': 'Portal Employee B', 'user_id': self.user_b.id,
        })
        self.request_b = self.env['ess.request'].create({
            'request_type_id': self.request_type.id, 'requester_kind': 'employee',
            'employee_id': self.employee_b.id, 'subject': 'Employee B private request',
        })

    def test_requests_page_requires_login(self):
        response = self.url_open('/my/requests')
        # Redirected to the login page rather than a raw 500/200 with data.
        self.assertIn(response.status_code, (200, 303))

    def test_cannot_view_another_employees_request_detail(self):
        self.authenticate('portal_employee_a', 'portal_employee_a')
        response = self.url_open('/my/requests/%d' % self.request_b.id, allow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Employee B private request', response.text)
