from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

PROFILE_EDITABLE_FIELDS = [
    'private_street', 'private_street2', 'private_city', 'private_state_id',
    'private_zip', 'private_country_id', 'private_phone', 'private_email',
    'emergency_contact', 'emergency_phone', 'study_field', 'study_school',
    'certificate',
]
PROFILE_MANY2ONE_FIELDS = ('private_state_id', 'private_country_id')


class EmployeeSelfPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        employee = request.env.user.employee_id
        if employee:
            if 'leave_balance_count' in counters:
                values['leave_balance_count'] = self._get_leave_balance(employee)
            if 'attendance_count' in counters:
                values['attendance_count'] = request.env['hr.attendance'].search_count([
                    ('employee_id', '=', employee.id),
                ])
            if 'task_count' in counters:
                values['task_count'] = request.env['project.task'].search_count([
                    ('user_ids', 'in', [request.env.user.id]),
                ])
            if 'assignment_count' in counters:
                values['assignment_count'] = request.env['employee.portal.task'].sudo().search_count([
                    ('employee_id', '=', employee.id), ('state', '!=', 'done'),
                ])
        if 'team_approval_count' in counters:
            values['team_approval_count'] = request.env['hr.leave'].search_count([
                ('employee_id.project_id.portal_manager_id', '=', request.env.user.id),
                ('state', 'in', ['confirm', 'validate1']),
                ('validation_type', 'in', ['manager', 'both']),
            ])
        return values

    def _get_portal_employee(self):
        employee = request.env.user.employee_id
        if not employee:
            raise AccessError(_("No employee record is linked to your account."))
        return employee

    def _get_allocation_data(self, employee):
        leave_types = request.env['hr.leave.type'].sudo().search([
            '|', ('company_id', '=', False), ('company_id', '=', employee.company_id.id),
        ])
        allocation_data = leave_types.get_allocation_data(employee.sudo())[employee.sudo()]
        return [data for data in allocation_data if data[1].get('max_leaves', False)]

    def _get_leave_balance(self, employee):
        return sum(data[1].get('virtual_remaining_leaves', 0) for data in self._get_allocation_data(employee))

    def _get_managed_projects(self):
        return request.env['project.project'].sudo().search([
            ('portal_manager_id', '=', request.env.user.id),
        ])

    def _get_managed_employees(self):
        return request.env['hr.employee'].sudo().search([
            ('project_id', 'in', self._get_managed_projects().ids),
        ])

    def _get_leave_stage(self, leave):
        """Build the approval stepper for a leave request straight from its
        own state machine (hr.leave.state selection + validation_type), so
        the steps shown always match what Odoo itself would show."""
        state_labels = dict(leave._fields['state'].selection)
        steps = ['confirm', 'validate1', 'validate'] if leave.validation_type == 'both' else ['confirm', 'validate']
        ended = leave.state in ('refuse', 'cancel')
        active_index = 0 if ended else (steps.index(leave.state) if leave.state in steps else 0)
        return {
            'step_info': [{'label': state_labels[s], 'done': i <= active_index} for i, s in enumerate(steps)],
            'ended': ended,
            'end_label': state_labels[leave.state] if ended else False,
            'approved': leave.state == 'validate',
        }

    # ---------------------------------------------------------------------
    # Dashboard
    # ---------------------------------------------------------------------

    @http.route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kw):
        employee = request.env.user.employee_id
        if employee or self._get_managed_projects():
            return request.redirect('/my/dashboard')
        return super().home(**kw)

    @http.route(['/my/dashboard'], type='http', auth='user', website=True)
    def portal_my_dashboard(self, **kw):
        employee = request.env.user.employee_id
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'dashboard',
            'dash_employee': False,
            'dash_projects_status': [],
        })

        if employee:
            leaves = request.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
            ], order='create_date desc', limit=5)
            values['dash_employee'] = {
                'employee': employee.sudo(),
                'allocation_data': self._get_allocation_data(employee),
                'leave_balance': self._get_leave_balance(employee),
                'leaves': [(leave, self._get_leave_stage(leave)) for leave in leaves],
                'assignment_count': request.env['employee.portal.task'].sudo().search_count([
                    ('employee_id', '=', employee.id), ('state', '!=', 'done'),
                ]),
            }

        projects = self._get_managed_projects()
        for project in projects:
            team_employees = request.env['hr.employee'].sudo().search([('project_id', '=', project.id)])
            values['dash_projects_status'].append({
                'project': project,
                'lines': self._team_status(team_employees),
                'approval_count': request.env['hr.leave'].sudo().search_count([
                    ('employee_id', 'in', team_employees.ids), ('state', 'in', ['confirm', 'validate1']),
                    ('validation_type', 'in', ['manager', 'both']),
                ]),
                'task_count': request.env['employee.portal.task'].sudo().search_count([
                    ('employee_id', 'in', team_employees.ids), ('state', '!=', 'done'),
                ]),
            })

        return request.render('employee_client_self_service_portal.portal_my_dashboard', values)

    # ---------------------------------------------------------------------
    # Profile
    # ---------------------------------------------------------------------

    @http.route(['/my/profile'], type='http', auth='user', website=True)
    def portal_my_profile(self, **kw):
        employee = self._get_portal_employee()
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'profile',
            'employee': employee.sudo(),
            'countries': request.env['res.country'].sudo().search([]),
            'states': request.env['res.country.state'].sudo().search([]),
        })
        return request.render('employee_client_self_service_portal.portal_my_profile', values)

    @http.route(['/my/profile/update'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_profile_update(self, **post):
        employee = self._get_portal_employee()
        values = {key: post[key] for key in PROFILE_EDITABLE_FIELDS if key in post}
        for m2o_field in PROFILE_MANY2ONE_FIELDS:
            if m2o_field in values:
                values[m2o_field] = int(values[m2o_field]) if values[m2o_field] else False
        employee.sudo().write(values)
        return request.redirect('/my/profile')

    # ---------------------------------------------------------------------
    # Time Off
    # ---------------------------------------------------------------------

    @http.route(['/my/time-off', '/my/time-off/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_time_off(self, page=1, **kw):
        employee = self._get_portal_employee()
        HrLeave = request.env['hr.leave']
        domain = [('employee_id', '=', employee.id)]

        pager_values = portal_pager(
            url='/my/time-off',
            total=HrLeave.search_count(domain),
            page=page,
            step=self._items_per_page,
        )
        leaves = HrLeave.search(domain, order='create_date desc', limit=self._items_per_page, offset=pager_values['offset'])

        allocation_data = self._get_allocation_data(employee)

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'time_off',
            'leaves': leaves,
            'pager': pager_values,
            'allocation_data': allocation_data,
            'default_url': '/my/time-off',
        })
        return request.render('employee_client_self_service_portal.portal_my_time_off', values)

    @http.route(['/my/time-off/new'], type='http', auth='user', website=True, methods=['GET'])
    def portal_my_time_off_new(self, **kw):
        employee = self._get_portal_employee()
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'time_off_new',
            'leave_types': request.env['hr.leave.type'].sudo().search([]),
            'error': kw.get('error'),
        })
        return request.render('employee_client_self_service_portal.portal_my_time_off_new', values)

    @http.route(['/my/time-off/new/submit'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_time_off_create(self, **post):
        employee = self._get_portal_employee()
        leave_vals = {
            'employee_id': employee.id,
            'holiday_status_id': int(post.get('holiday_status_id')),
            'request_date_from': post.get('request_date_from'),
            'request_date_to': post.get('request_date_to'),
        }
        if post.get('name'):
            leave_vals['name'] = post['name']
        try:
            request.env['hr.leave'].with_context(mail_notify_author=True).create(leave_vals)
        except (UserError, ValueError) as e:
            return request.redirect('/my/time-off/new?error=%s' % str(e))
        return request.redirect('/my/time-off')

    @http.route(['/my/time-off/<int:leave_id>'], type='http', auth='user', website=True)
    def portal_my_time_off_detail(self, leave_id, **kw):
        try:
            leave_sudo = self._document_check_access('hr.leave', leave_id)
        except (AccessError, MissingError):
            return request.redirect('/my/time-off')

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'time_off',
            'leave': leave_sudo,
        })
        return request.render('employee_client_self_service_portal.portal_my_time_off_detail', values)

    @http.route(['/my/time-off/<int:leave_id>/cancel'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_time_off_cancel(self, leave_id, **kw):
        leave_sudo = self._document_check_access('hr.leave', leave_id)
        employee = self._get_portal_employee()
        if leave_sudo.employee_id.id == employee.id and leave_sudo.state in ('confirm', 'validate1'):
            leave_sudo.unlink()
            return request.redirect('/my/time-off')
        return request.redirect('/my/time-off/%d' % leave_id)

    # ---------------------------------------------------------------------
    # Attendances
    # ---------------------------------------------------------------------

    @http.route(['/my/attendances', '/my/attendances/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_attendances(self, page=1, **kw):
        employee = self._get_portal_employee()
        HrAttendance = request.env['hr.attendance']
        domain = [('employee_id', '=', employee.id)]

        pager_values = portal_pager(
            url='/my/attendances',
            total=HrAttendance.search_count(domain),
            page=page,
            step=self._items_per_page,
        )
        attendances = HrAttendance.search(domain, order='check_in desc', limit=self._items_per_page, offset=pager_values['offset'])

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'attendances',
            'attendances': attendances,
            'pager': pager_values,
            'employee': employee.sudo(),
            'default_url': '/my/attendances',
        })
        return request.render('employee_client_self_service_portal.portal_my_attendances', values)

    @http.route(['/my/attendances/toggle'], type='json', auth='user', website=True)
    def portal_my_attendance_toggle(self, **kw):
        employee = self._get_portal_employee()
        attendance = employee.sudo()._attendance_action_change()
        return {
            'attendance_state': employee.sudo().attendance_state,
            'check_in': fields.Datetime.to_string(attendance.check_in) if attendance.check_in else False,
            'check_out': fields.Datetime.to_string(attendance.check_out) if attendance.check_out else False,
        }

    # ---------------------------------------------------------------------
    # Tasks
    # ---------------------------------------------------------------------

    @http.route(['/my/tasks', '/my/tasks/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_tasks(self, page=1, **kw):
        ProjectTask = request.env['project.task']
        domain = [('user_ids', 'in', [request.env.user.id])]

        pager_values = portal_pager(
            url='/my/tasks',
            total=ProjectTask.search_count(domain),
            page=page,
            step=self._items_per_page,
        )
        tasks = ProjectTask.search(domain, order='date_deadline asc', limit=self._items_per_page, offset=pager_values['offset'])

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'tasks',
            'tasks': tasks,
            'pager': pager_values,
            'default_url': '/my/tasks',
        })
        return request.render('employee_client_self_service_portal.portal_my_tasks', values)

    # ---------------------------------------------------------------------
    # Team (manager)
    # ---------------------------------------------------------------------

    def _team_status(self, employees):
        today_start = fields.Datetime.to_string(fields.Datetime.now().replace(hour=0, minute=0, second=0))
        today_end = fields.Datetime.to_string(fields.Datetime.now().replace(hour=23, minute=59, second=59))
        today_leaves = request.env['hr.leave'].sudo().search([
            ('employee_id', 'in', employees.ids),
            ('state', '=', 'validate'),
            ('date_from', '<=', today_end),
            ('date_to', '>=', today_start),
        ])
        leaves_by_employee = {}
        for leave in today_leaves:
            leaves_by_employee.setdefault(leave.employee_id.id, leave)

        statuses = []
        for employee in employees:
            leave = leaves_by_employee.get(employee.id)
            if employee.attendance_state == 'checked_in':
                status = 'present'
            elif leave and leave.holiday_status_id.request_unit == 'hour':
                status = 'permission'
            elif leave:
                status = 'leave'
            else:
                status = 'absent'
            statuses.append({'employee': employee, 'status': status, 'leave': leave})
        return statuses

    @http.route(['/my/team'], type='http', auth='user', website=True)
    def portal_my_team(self, **kw):
        projects = self._get_managed_projects()
        projects_status = []
        for project in projects:
            employees = request.env['hr.employee'].sudo().search([('project_id', '=', project.id)])
            projects_status.append({'project': project, 'lines': self._team_status(employees)})

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'team',
            'projects_status': projects_status,
        })
        return request.render('employee_client_self_service_portal.portal_my_team', values)

    @http.route(['/my/team/approvals', '/my/team/approvals/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_team_approvals(self, page=1, **kw):
        employees = self._get_managed_employees()
        # sudo(): authorization already enforced above via project portal_manager_id ownership;
        # employee_id.name/job_title on team members are not readable by a portal user
        # otherwise (hr.employee.public has no portal ACL).
        HrLeave = request.env['hr.leave'].sudo()
        domain = [
            ('employee_id', 'in', employees.ids), ('state', 'in', ['confirm', 'validate1']),
            ('validation_type', 'in', ['manager', 'both']),
        ]

        pager_values = portal_pager(
            url='/my/team/approvals',
            total=HrLeave.search_count(domain),
            page=page,
            step=self._items_per_page,
        )
        leaves = HrLeave.search(domain, order='create_date desc', limit=self._items_per_page, offset=pager_values['offset'])

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'team_approvals',
            'leaves': leaves,
            'pager': pager_values,
            'default_url': '/my/team/approvals',
        })
        return request.render('employee_client_self_service_portal.portal_my_team_approvals', values)

    def _get_team_leave(self, leave_id):
        leave_sudo = self._document_check_access('hr.leave', leave_id)
        if leave_sudo.employee_id.project_id.portal_manager_id.id != request.env.user.id:
            raise AccessError(_("You are not the approver of this request."))
        if leave_sudo.validation_type not in ('manager', 'both'):
            # 'hr'/'no_validation' types are internal-HR-only; the client
            # Portal Manager may never finalize them, even if they guess the id.
            raise AccessError(_("This request does not require your approval."))
        return leave_sudo

    @http.route(['/my/team/approvals/<int:leave_id>/approve'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_team_approve(self, leave_id, **kw):
        try:
            leave_sudo = self._get_team_leave(leave_id)
            leave_sudo.action_approve()
        except (AccessError, MissingError, UserError):
            pass
        return request.redirect('/my/team/approvals')

    @http.route(['/my/team/approvals/<int:leave_id>/refuse'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_team_refuse(self, leave_id, **kw):
        try:
            leave_sudo = self._get_team_leave(leave_id)
            leave_sudo.action_refuse()
        except (AccessError, MissingError, UserError):
            pass
        return request.redirect('/my/team/approvals')

    # ---------------------------------------------------------------------
    # Team Tasks (manager assigns work to their project's employees)
    # ---------------------------------------------------------------------

    @http.route(['/my/team/tasks'], type='http', auth='user', website=True)
    def portal_my_team_tasks(self, **kw):
        employees = self._get_managed_employees()
        tasks = request.env['employee.portal.task'].sudo().search([
            ('employee_id', 'in', employees.ids),
        ])
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'team_tasks',
            'tasks': tasks,
        })
        return request.render('employee_client_self_service_portal.portal_my_team_tasks', values)

    @http.route(['/my/team/tasks/new'], type='http', auth='user', website=True)
    def portal_my_team_tasks_new(self, **kw):
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'team_tasks',
            'employees': self._get_managed_employees(),
            'error': kw.get('error'),
        })
        return request.render('employee_client_self_service_portal.portal_my_team_tasks_new', values)

    @http.route(['/my/team/tasks/new/submit'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_team_tasks_create(self, **post):
        employees = self._get_managed_employees()
        employee_id = int(post.get('employee_id') or 0)
        if employee_id not in employees.ids or not post.get('name'):
            return request.redirect('/my/team/tasks/new?error=%s' % _("Pick a valid employee and title."))
        request.env['employee.portal.task'].sudo().create({
            'employee_id': employee_id,
            'assigned_by_id': request.env.user.id,
            'name': post['name'],
            'description': post.get('description'),
            'deadline': post.get('deadline') or False,
        })
        return request.redirect('/my/team/tasks')

    # ---------------------------------------------------------------------
    # My Assignments (employee side)
    # ---------------------------------------------------------------------

    @http.route(['/my/assignments'], type='http', auth='user', website=True)
    def portal_my_assignments(self, **kw):
        employee = self._get_portal_employee()
        tasks = request.env['employee.portal.task'].sudo().search([
            ('employee_id', '=', employee.id),
        ])
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'assignments',
            'tasks': tasks,
        })
        return request.render('employee_client_self_service_portal.portal_my_assignments', values)

    def _get_own_task(self, task_id):
        employee = self._get_portal_employee()
        task_sudo = request.env['employee.portal.task'].sudo().browse(task_id).exists()
        if not task_sudo or task_sudo.employee_id.id != employee.id:
            raise AccessError(_("This assignment does not belong to you."))
        return task_sudo

    @http.route(['/my/assignments/<int:task_id>/accept'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_assignment_accept(self, task_id, **kw):
        try:
            task_sudo = self._get_own_task(task_id)
            if task_sudo.state == 'new':
                task_sudo.write({'state': 'accepted', 'last_update_date': fields.Datetime.now()})
        except AccessError:
            pass
        return request.redirect('/my/assignments')

    @http.route(['/my/assignments/<int:task_id>/update'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_assignment_update(self, task_id, **post):
        try:
            task_sudo = self._get_own_task(task_id)
            new_state = post.get('state')
            if new_state in ('in_progress', 'done'):
                task_sudo.write({
                    'state': new_state,
                    'status_note': post.get('status_note'),
                    'last_update_date': fields.Datetime.now(),
                })
        except AccessError:
            pass
        return request.redirect('/my/assignments')
