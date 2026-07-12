from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.employee_client_self_service_portal.controllers.portal import EmployeeSelfPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class EmployeeSelfPortalPayroll(EmployeeSelfPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        employee = request.env.user.employee_id
        if employee and 'payslip_count' in counters:
            values['payslip_count'] = request.env['hr.payslip'].search_count([
                ('employee_id', '=', employee.id), ('state', 'in', ['done', 'paid']),
            ])
        return values

    @http.route(['/my/payslips', '/my/payslips/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_payslips(self, page=1, **kw):
        employee = self._get_portal_employee()
        HrPayslip = request.env['hr.payslip']
        domain = [('employee_id', '=', employee.id), ('state', 'in', ['done', 'paid'])]

        pager_values = portal_pager(
            url='/my/payslips',
            total=HrPayslip.search_count(domain),
            page=page,
            step=self._items_per_page,
        )
        payslips = HrPayslip.search(domain, order='date_from desc', limit=self._items_per_page, offset=pager_values['offset'])

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'payslips',
            'payslips': payslips,
            'pager': pager_values,
            'default_url': '/my/payslips',
        })
        return request.render('employee_client_self_service_portal_payroll.portal_my_payslips', values)

    @http.route(['/my/payslips/<int:payslip_id>/download'], type='http', auth='user', website=True)
    def portal_my_payslip_download(self, payslip_id, **kw):
        try:
            payslip_sudo = self._document_check_access('hr.payslip', payslip_id)
        except (AccessError, MissingError):
            return request.redirect('/my/payslips')
        return self._show_report(
            model=payslip_sudo,
            report_type='pdf',
            report_ref='hr_payroll.action_report_payslip',
            download=True,
        )
