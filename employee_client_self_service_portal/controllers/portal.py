from datetime import datetime

import pytz

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request
from odoo.tools import html2plaintext

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

PROFILE_EDITABLE_FIELDS = [
    'private_street', 'private_street2', 'private_city', 'private_state_id',
    'private_zip', 'private_country_id', 'private_phone', 'private_email',
    'emergency_contact', 'emergency_phone', 'study_field', 'study_school',
    'certificate',
]
PROFILE_MANY2ONE_FIELDS = ('private_state_id', 'private_country_id')


def _parse_portal_datetime_local(value, tz_name):
    """Convert an HTML ``<input type="datetime-local">`` value (e.g.
    ``2026-07-23T00:08``, in the current user's timezone) into a naive
    UTC datetime suitable for an Odoo Datetime field."""
    if not value:
        return False
    naive = datetime.strptime(value, '%Y-%m-%dT%H:%M')
    user_tz = pytz.timezone(tz_name or 'UTC')
    localized = user_tz.localize(naive)
    return localized.astimezone(pytz.UTC).replace(tzinfo=None)


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
                '|', ('employee_id.project_id.portal_manager_id', '=', request.env.user.id),
                ('employee_id.project_id.project_owner_id', '=', request.env.user.id),
                ('state', 'in', ['confirm', 'validate1']),
                ('validation_type', 'in', ['manager', 'both']),
            ])
        if 'team_request_count' in counters:
            values['team_request_count'] = request.env['ess.request'].sudo().search_count([
                ('project_id', 'in', self._get_managed_projects().ids),
                ('state', '=', 'with_client_pm'),
            ])
        if 'ess_request_count' in counters:
            try:
                requester = self._get_ess_requester()
            except AccessError:
                requester = False
            if requester:
                domain = [('employee_id', '=', requester['employee'].id)] if requester['kind'] == 'employee' \
                    else [('partner_id', '=', requester['partner'].id)]
                values['ess_request_count'] = request.env['ess.request'].search_count(domain)
        if 'ess_notification_unread_count' in counters:
            values['ess_notification_unread_count'] = request.env['ess.portal.notification'].sudo().search_count([
                ('user_id', '=', request.env.user.id), ('is_read', '=', False),
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
            '|', ('portal_manager_id', '=', request.env.user.id), ('project_owner_id', '=', request.env.user.id),
            '|', ('company_id', '=', False), ('company_id', 'in', request.env.companies.ids),
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
        if request.env.user.has_group('employee_client_self_service_portal.group_ess_client'):
            return request.redirect('/my/requests')
        return super().home(**kw)

    @http.route(['/my/dashboard'], type='http', auth='user', website=True)
    def portal_my_dashboard(self, **kw):
        employee = request.env.user.employee_id
        managed_projects = self._get_managed_projects()
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'dashboard',
            'dash_employee': False,
            'dash_projects_status': bool(managed_projects),
            'dash_manager': False,
        })

        if not employee and managed_projects:
            managed_employees = self._get_managed_employees()
            values['dash_manager'] = {
                'projects': managed_projects,
                'employee_count': len(managed_employees),
                'team_request_count': request.env['ess.request'].sudo().search_count([
                    ('project_id', 'in', managed_projects.ids), ('state', '=', 'with_client_pm'),
                ]),
                'leave_approval_count': request.env['hr.leave'].sudo().search_count([
                    ('employee_id', 'in', managed_employees.ids), ('state', '=', 'confirm'),
                    ('validation_type', 'in', ['manager', 'both']),
                ]),
                'is_client': request.env.user.has_group('employee_client_self_service_portal.group_ess_client'),
            }

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
                'request_count': request.env['ess.request'].sudo().search_count([
                    ('employee_id', '=', employee.id),
                    ('state', 'not in', ('closed', 'cancelled', 'rejected')),
                ]),
            }

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
        except (UserError, ValidationError, ValueError) as e:
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
    def portal_my_attendance_toggle(self, latitude=None, longitude=None, **kw):
        employee = self._get_portal_employee()
        employee.sudo()._check_attendance_zone(latitude, longitude)
        geo_information = {'latitude': latitude, 'longitude': longitude} if latitude and longitude else None
        attendance = employee.sudo()._attendance_action_change(geo_information)
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

    @http.route(['/my/team/employees/<int:employee_id>'], type='http', auth='user', website=True)
    def portal_my_team_employee_detail(self, employee_id, **kw):
        employees = self._get_managed_employees()
        if employee_id not in employees.ids:
            return request.redirect('/my/team')
        employee = employees.filtered(lambda e: e.id == employee_id)
        tasks = request.env['employee.portal.task'].sudo().search([
            ('employee_id', '=', employee_id),
        ])
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'team_employee_detail',
            'employee': employee,
            'status': self._team_status(employee)[0],
            'tasks': tasks,
        })
        return request.render('employee_client_self_service_portal.portal_my_team_employee_detail', values)

    @http.route(['/my/team/approvals', '/my/team/approvals/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_team_approvals(self, page=1, **kw):
        employees = self._get_managed_employees()
        # sudo(): authorization already enforced above via project portal_manager_id ownership;
        # employee_id.name/job_title on team members are not readable by a portal user
        # otherwise (hr.employee.public has no portal ACL).
        HrLeave = request.env['hr.leave'].sudo()
        domain = [
            ('employee_id', 'in', employees.ids), ('state', '=', 'confirm'),
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
            'error': kw.get('error'),
        })
        return request.render('employee_client_self_service_portal.portal_my_team_approvals', values)

    def _get_team_leave(self, leave_id):
        leave_sudo = self._document_check_access('hr.leave', leave_id)
        project = leave_sudo.employee_id.project_id
        if request.env.user.id not in (project.portal_manager_id.id, project.project_owner_id.id):
            raise AccessError(_("You are not the approver of this request."))
        if leave_sudo.validation_type not in ('manager', 'both'):
            # 'hr'/'no_validation' types are internal-HR-only; the client
            # Portal Manager may never finalize them, even if they guess the id.
            raise AccessError(_("This request does not require your approval."))
        if leave_sudo.state != 'confirm':
            # Already handled (approved/refused), or - for validation_type
            # 'both' - past the client's stage and now awaiting internal HR.
            raise UserError(_("This request is no longer awaiting your approval."))
        return leave_sudo

    @http.route(['/my/team/approvals/<int:leave_id>/approve'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_team_approve(self, leave_id, **kw):
        try:
            leave_sudo = self._get_team_leave(leave_id)
            leave_sudo.action_approve()
        except (AccessError, MissingError, UserError) as e:
            return request.redirect('/my/team/approvals?error=%s' % str(e))
        return request.redirect('/my/team/approvals')

    @http.route(['/my/team/approvals/<int:leave_id>/refuse'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_team_refuse(self, leave_id, **kw):
        try:
            leave_sudo = self._get_team_leave(leave_id)
            leave_sudo.action_refuse()
        except (AccessError, MissingError, UserError) as e:
            return request.redirect('/my/team/approvals?error=%s' % str(e))
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
            'deadline': _parse_portal_datetime_local(post.get('deadline'), request.env.user.tz),
        })
        return request.redirect('/my/team/tasks')

    # ---------------------------------------------------------------------
    # Team Requests (Project Owner / Client Project Manager review queue)
    # ---------------------------------------------------------------------

    def _get_team_request(self, request_id):
        projects = self._get_managed_projects()
        req_sudo = request.env['ess.request'].sudo().browse(request_id).exists()
        if not req_sudo or req_sudo.project_id.id not in projects.ids:
            raise AccessError(_("This request is not part of a project you manage."))
        return req_sudo

    @http.route(['/my/team/requests'], type='http', auth='user', website=True)
    def portal_my_team_requests(self, **kw):
        projects = self._get_managed_projects()
        requests = request.env['ess.request'].sudo().search([
            ('project_id', 'in', projects.ids),
            ('state', '=', 'with_client_pm'),
        ], order='create_date desc')

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'team_requests',
            'requests': requests,
            'error': kw.get('error'),
        })
        return request.render('employee_client_self_service_portal.portal_my_team_requests', values)

    @http.route(['/my/team/requests/<int:request_id>/approve'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_team_request_approve(self, request_id, **kw):
        try:
            req_sudo = self._get_team_request(request_id)
            req_sudo.action_client_pm_approve()
        except (AccessError, MissingError, UserError) as e:
            return request.redirect('/my/team/requests?error=%s' % str(e))
        return request.redirect('/my/team/requests')

    @http.route(['/my/team/requests/<int:request_id>/reject'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_team_request_reject(self, request_id, **post):
        try:
            req_sudo = self._get_team_request(request_id)
            req_sudo.action_client_pm_reject(reason=post.get('reason'))
        except (AccessError, MissingError, UserError) as e:
            return request.redirect('/my/team/requests?error=%s' % str(e))
        return request.redirect('/my/team/requests')

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
            'ess_overdue_label': _('Overdue by %s'),
            'ess_left_label': _('%s left'),
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

    # ---------------------------------------------------------------------
    # General requests (employee + true external client)
    # ---------------------------------------------------------------------

    def _get_ess_requester(self):
        """Server-derived requester identity - never taken from the client.
        A user in the Client group is a 'client' requester scoped to their
        own partner; anyone else with an employee record is an 'employee'
        requester. Neither can impersonate the other."""
        user = request.env.user
        if user.has_group('employee_client_self_service_portal.group_ess_client'):
            return {'kind': 'client', 'employee': False, 'partner': user.partner_id}
        employee = user.employee_id
        if employee:
            return {'kind': 'employee', 'employee': employee, 'partner': False}
        raise AccessError(_("Your account is not linked to an employee or client record."))

    def _get_own_request(self, request_id):
        requester = self._get_ess_requester()
        req_sudo = request.env['ess.request'].sudo().browse(request_id).exists()
        if not req_sudo:
            raise MissingError(_("This request does not exist."))
        owns = (
            (requester['kind'] == 'employee' and req_sudo.employee_id.id == requester['employee'].id)
            or (requester['kind'] == 'client' and req_sudo.partner_id.id == requester['partner'].id)
        )
        if not owns:
            raise AccessError(_("This request does not belong to you."))
        return req_sudo

    ESS_REQUEST_CLOSED_STATES = ('completed', 'closed', 'rejected', 'cancelled')

    @http.route(['/my/requests', '/my/requests/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_requests(self, page=1, **kw):
        requester = self._get_ess_requester()
        EssRequest = request.env['ess.request']
        if requester['kind'] == 'employee':
            domain = [('employee_id', '=', requester['employee'].id)]
        else:
            domain = [('partner_id', '=', requester['partner'].id)]

        total = EssRequest.search_count(domain)
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'ess_requests',
            'default_url': '/my/requests',
        })

        if total <= self._items_per_page:
            # Small list: keep the plain flat table, no tab chrome needed.
            pager_values = portal_pager(url='/my/requests', total=total, page=page, step=self._items_per_page)
            requests = EssRequest.search(
                domain, order='create_date desc', limit=self._items_per_page, offset=pager_values['offset'])
            values.update({
                'show_tabs': False,
                'requests': requests,
                'pager': pager_values,
            })
        else:
            active_tab = 'history' if kw.get('tab') == 'history' else 'open'
            closed_domain = domain + [('state', 'in', self.ESS_REQUEST_CLOSED_STATES)]
            open_domain = domain + [('state', 'not in', self.ESS_REQUEST_CLOSED_STATES)]
            tab_domain = closed_domain if active_tab == 'history' else open_domain
            pager_values = portal_pager(
                url='/my/requests', total=EssRequest.search_count(tab_domain), page=page,
                step=self._items_per_page, url_args={'tab': active_tab})
            requests = EssRequest.search(
                tab_domain, order='create_date desc', limit=self._items_per_page, offset=pager_values['offset'])
            values.update({
                'show_tabs': True,
                'active_tab': active_tab,
                'open_count': EssRequest.search_count(open_domain),
                'history_count': EssRequest.search_count(closed_domain),
                'requests': requests,
                'pager': pager_values,
            })

        return request.render('employee_client_self_service_portal.portal_my_requests', values)

    @http.route(['/my/requests/new'], type='http', auth='user', website=True)
    def portal_my_requests_new(self, **kw):
        requester = self._get_ess_requester()
        request_types = request.env['ess.request.type'].sudo().search([
            ('requester_kind', 'in', [requester['kind'], 'both']),
        ])
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'ess_requests',
            'request_types': request_types,
            'managed_projects': self._get_managed_projects() if requester['kind'] == 'client' else request.env['project.project'],
            'error': kw.get('error'),
        })
        return request.render('employee_client_self_service_portal.portal_my_requests_new', values)

    @http.route(['/my/requests/new/submit'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_requests_create(self, **post):
        requester = self._get_ess_requester()
        allowed_types = request.env['ess.request.type'].sudo().search([
            ('requester_kind', 'in', [requester['kind'], 'both']),
        ])
        request_type_id = int(post.get('request_type_id') or 0)
        if request_type_id not in allowed_types.ids or not post.get('subject'):
            return request.redirect(
                '/my/requests/new?error=%s' % _("Pick a valid request type and subject."))

        vals = {
            'request_type_id': request_type_id,
            'requester_kind': requester['kind'],
            'subject': post['subject'],
            'description': post.get('description'),
            'priority': post.get('priority') if post.get('priority') in (
                'low', 'normal', 'high', 'urgent') else 'normal',
        }
        if requester['kind'] == 'employee':
            vals['employee_id'] = requester['employee'].id
        else:
            vals['partner_id'] = requester['partner'].id
            managed_projects = self._get_managed_projects()
            project_id = int(post.get('project_id') or 0)
            if project_id and project_id in managed_projects.ids:
                vals['project_id'] = project_id

        new_request = request.env['ess.request'].sudo().create(vals)
        new_request.action_submit()
        return request.redirect('/my/requests/%d' % new_request.id)

    @http.route(['/my/requests/<int:request_id>'], type='http', auth='user', website=True)
    def portal_my_request_detail(self, request_id, **kw):
        try:
            req_sudo = self._get_own_request(request_id)
        except (AccessError, MissingError):
            return request.redirect('/my/requests')

        mirrored_message_ids = req_sudo.comment_ids.mapped('chatter_message_id').ids
        staff_messages = req_sudo.message_ids.filtered(
            lambda m: m.subtype_id and not m.subtype_id.internal and m.message_type == 'comment'
            and m.id not in mirrored_message_ids)
        thread_entries = sorted([
            {'author': c.author_user_id.name, 'body': c.body, 'date': c.create_date}
            for c in req_sudo.comment_ids.filtered(lambda c: not c.is_internal)
        ] + [
            {'author': m.author_id.name, 'body': html2plaintext(m.body or ''), 'date': m.date}
            for m in staff_messages
        ], key=lambda entry: entry['date'])

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'ess_requests',
            'req': req_sudo,
            'thread_entries': thread_entries,
        })
        return request.render('employee_client_self_service_portal.portal_my_request_detail', values)

    @http.route(['/my/requests/<int:request_id>/comment'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_request_comment(self, request_id, **post):
        req_sudo = self._get_own_request(request_id)
        if post.get('body'):
            request.env['ess.request.comment'].sudo().create({
                'request_id': req_sudo.id,
                'author_user_id': request.env.user.id,
                'body': post['body'],
                'is_internal': False,
            })
        return request.redirect('/my/requests/%d' % request_id)

    @http.route(['/my/requests/<int:request_id>/cancel'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_request_cancel(self, request_id, **kw):
        req_sudo = self._get_own_request(request_id)
        if req_sudo.state not in ('completed', 'closed', 'cancelled'):
            req_sudo.action_cancel()
        return request.redirect('/my/requests/%d' % request_id)

    @http.route(['/my/requests/<int:request_id>/rate'], type='http', auth='user', website=True, methods=['POST'])
    def portal_my_request_rate(self, request_id, **post):
        req_sudo = self._get_own_request(request_id)
        rating = post.get('rating')
        if req_sudo.state == 'closed' and rating in ('1', '2', '3', '4', '5'):
            req_sudo.action_rate(rating)
        return request.redirect('/my/requests/%d' % request_id)

    # ---------------------------------------------------------------------
    # Notifications
    # ---------------------------------------------------------------------

    @http.route(['/my/notifications'], type='http', auth='user', website=True)
    def portal_my_notifications(self, **kw):
        notifications = request.env['ess.portal.notification'].sudo().search([
            ('user_id', '=', request.env.user.id),
        ], order='create_date desc', limit=80)
        notifications.filtered(lambda n: not n.is_read).write({'is_read': True})
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'ess_notifications',
            'notifications': notifications,
        })
        return request.render('employee_client_self_service_portal.portal_my_notifications', values)
