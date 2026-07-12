from odoo import fields, models


class EmployeePortalTask(models.Model):
    _name = 'employee.portal.task'
    _description = 'Employee Portal Task Assignment'
    _order = 'deadline asc, id desc'

    employee_id = fields.Many2one('hr.employee', string='Assigned To', required=True)
    project_id = fields.Many2one(related='employee_id.project_id', store=True, string='Project')
    assigned_by_id = fields.Many2one('res.users', string='Assigned By')
    name = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    deadline = fields.Datetime(string='Deadline')
    state = fields.Selection([
        ('new', 'New'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], string='Status', default='new', required=True)
    status_note = fields.Text(string='Latest Update')
    last_update_date = fields.Datetime(string='Last Updated')

    def _cron_send_reminders(self):
        template = self.env.ref('employee_client_self_service_portal.mail_template_assignment_reminder', raise_if_not_found=False)
        if not template:
            return
        pending = self.search([('state', '!=', 'done')])
        employees = pending.employee_id
        for employee in employees:
            if not employee.user_id or not employee.work_email:
                continue
            tasks = pending.filtered(lambda t: t.employee_id == employee)
            template.with_context(pending_tasks=tasks).send_mail(
                employee.id, force_send=True, email_values={'email_to': employee.work_email},
            )
