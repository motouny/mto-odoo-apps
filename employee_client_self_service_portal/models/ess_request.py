from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

MANAGER_GROUP = 'employee_client_self_service_portal.group_ess_request_manager'


class EssRequest(models.Model):
    _name = 'ess.request'
    _description = 'Employee / Client Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda self: _('New'))
    request_type_id = fields.Many2one('ess.request.type', required=True, tracking=True)

    requester_kind = fields.Selection([
        ('employee', 'Employee'),
        ('client', 'Client'),
    ], required=True, default='employee', tracking=True)
    employee_id = fields.Many2one('hr.employee', tracking=True, ondelete='restrict')
    partner_id = fields.Many2one('res.partner', string='Client Contact', tracking=True, ondelete='restrict')
    department = fields.Char()
    project_id = fields.Many2one(
        'project.project', string='Project', tracking=True,
        help='Project this request is scoped to. Auto-filled from the employee for '
             "employee requests; set explicitly for client requests tied to a "
             "project owner/client project manager's project.")

    subject = fields.Char(required=True, tracking=True)
    description = fields.Text()
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='normal', required=True, tracking=True)

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company, tracking=True)
    assigned_user_id = fields.Many2one('res.users', string='Assigned To', tracking=True)
    assigned_team_id = fields.Many2one('ess.request.team', string='Assigned Team', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('with_client_pm', 'With Client Project Manager'),
        ('under_review', 'Under Review'),
        ('waiting_info', 'Waiting for Information'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ], default='draft', required=True, tracking=True, copy=False)

    submitted_date = fields.Datetime(readonly=True, copy=False)
    due_date = fields.Datetime()
    closed_date = fields.Datetime(readonly=True, copy=False)

    customer_rating = fields.Selection([
        ('1', '1 - Very Unsatisfied'),
        ('2', '2 - Unsatisfied'),
        ('3', '3 - Neutral'),
        ('4', '4 - Satisfied'),
        ('5', '5 - Very Satisfied'),
    ], copy=False)

    internal_notes = fields.Text(help='Staff-only notes, never shown to the requester.')

    comment_ids = fields.One2many('ess.request.comment', 'request_id', string='Comments')
    status_history_ids = fields.One2many(
        'ess.request.status.history', 'request_id', string='Status History')

    _sql_constraints = [
        ('requester_check',
         "CHECK((requester_kind = 'employee' AND employee_id IS NOT NULL) OR "
         "(requester_kind = 'client' AND partner_id IS NOT NULL))",
         'An employee request needs an employee, a client request needs a client contact.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('ess.request') or _('New')
            if vals.get('request_type_id') and not vals.get('assigned_team_id'):
                request_type = self.env['ess.request.type'].browse(vals['request_type_id'])
                if request_type.default_assigned_team_id:
                    vals['assigned_team_id'] = request_type.default_assigned_team_id.id
            if vals.get('employee_id') and not vals.get('project_id'):
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                if employee.project_id:
                    vals['project_id'] = employee.project_id.id
        records = super().create(vals_list)
        for record in records:
            record._log_status(False, record.state)
        return records

    def _log_status(self, from_state, to_state, note=False):
        self.env['ess.request.status.history'].sudo().create({
            'request_id': self.id,
            'from_state': from_state,
            'to_state': to_state,
            'changed_by_uid': self.env.user.id,
            'note': note,
        })

    def _notify_requester(self, title, body):
        self.ensure_one()
        user = self.employee_id.user_id if self.requester_kind == 'employee' else (
            self.partner_id.user_ids[:1])
        if user:
            self.env['ess.portal.notification'].sudo().create({
                'user_id': user.id,
                'title': title,
                'body': body,
                'request_id': self.id,
            })
        email = self.employee_id.work_email or self.partner_id.email
        if email:
            template = self.env.ref(
                'employee_client_self_service_portal.mail_template_ess_request_status_update',
                raise_if_not_found=False)
            if template:
                template.sudo().send_mail(self.id, force_send=False)

    def _write_state(self, new_state, note=False):
        for request in self:
            old_state = request.state
            request.state = new_state
            if new_state == 'submitted' and request.project_id and not request.assigned_user_id:
                request.assigned_user_id = request.project_id.user_id
            request._log_status(old_state, new_state, note=note)

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_submit(self):
        for request in self:
            if request.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            request.submitted_date = fields.Datetime.now()
            request._write_state(request._next_state_after_submit())
            request._notify_requester(
                _('Request submitted'), _('Your request %s has been submitted.') % request.name)

    def _next_state_after_submit(self):
        """Client-submitted requests tied to a project sit with the Client
        Project Manager first, unless he is the one submitting - forwarding
        to himself would be pointless."""
        self.ensure_one()
        if (self.requester_kind == 'client' and self.project_id
                and self.env.user != self.project_id.portal_manager_id):
            return 'with_client_pm'
        return 'submitted'

    def _get_client_approver(self):
        """Resolve who on the client side may approve/reject this request,
        based on the request type's configured approver role. An empty
        recordset means either the project owner or client PM may act."""
        self.ensure_one()
        role = self.request_type_id.client_approver_role
        if role == 'owner':
            return self.project_id.project_owner_id
        if role == 'client_pm':
            return self.project_id.portal_manager_id
        return self.env['res.users']

    def _check_client_approver(self):
        self.ensure_one()
        if self.state != 'with_client_pm':
            raise UserError(_('This request is not awaiting the client project manager.'))
        if self.env.su:
            return
        project = self.project_id
        user = self.env.user
        if user not in (project.project_owner_id, project.portal_manager_id):
            raise AccessError(_('You do not manage this project.'))
        approver = self._get_client_approver()
        if approver and user != approver:
            raise AccessError(_('For this request type, only %s can approve it.') % approver.name)

    def action_client_pm_approve(self):
        for request in self:
            request._check_client_approver()
            request._write_state('submitted')
            request._notify_requester(
                _('Request forwarded'),
                _('Your request %s has been approved and forwarded to the company.') % request.name)

    def action_client_pm_reject(self, reason=False):
        for request in self:
            request._check_client_approver()
            request._write_state('rejected', note=reason)
            request._notify_requester(
                _('Request rejected'),
                reason or _('Your request %s was rejected by the project manager.') % request.name)

    def _check_manager(self):
        if not self.env.su and not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError(_('You are not allowed to perform this action.'))

    def action_start_review(self):
        self._check_manager()
        for request in self:
            if request.state != 'submitted':
                raise UserError(_('Only submitted requests can move to review.'))
            request._write_state('under_review')

    def action_request_info(self, note=False):
        self._check_manager()
        for request in self:
            if request.state not in ('submitted', 'under_review'):
                raise UserError(_('This request is not awaiting review.'))
            request._write_state('waiting_info', note=note)
            request._notify_requester(
                _('More information needed'),
                note or _('Please provide more information for request %s.') % request.name)

    def action_provide_info(self):
        for request in self:
            if request.state != 'waiting_info':
                raise UserError(_('This request is not waiting for information.'))
            request._write_state('under_review')

    def action_approve(self):
        self._check_manager()
        for request in self:
            if request.state not in ('submitted', 'under_review'):
                raise UserError(_('Only submitted or under-review requests can be approved.'))
            request._write_state('approved')
            request._notify_requester(
                _('Request approved'), _('Your request %s has been approved.') % request.name)

    def action_reject(self, reason=False):
        self._check_manager()
        for request in self:
            if request.state not in ('submitted', 'under_review'):
                raise UserError(_('Only submitted or under-review requests can be rejected.'))
            request._write_state('rejected', note=reason)
            request._notify_requester(
                _('Request rejected'), reason or _('Your request %s was rejected.') % request.name)

    def action_start_progress(self):
        self._check_manager()
        for request in self:
            if request.state != 'approved':
                raise UserError(_('Only approved requests can start progress.'))
            request._write_state('in_progress')

    def action_complete(self):
        self._check_manager()
        for request in self:
            if request.state != 'in_progress':
                raise UserError(_('Only in-progress requests can be completed.'))
            request._write_state('completed')
            request._notify_requester(
                _('Request completed'), _('Your request %s has been completed.') % request.name)

    def action_close(self):
        self._check_manager()
        for request in self:
            if request.state != 'completed':
                raise UserError(_('Only completed requests can be closed.'))
            request.closed_date = fields.Datetime.now()
            request._write_state('closed')

    def action_cancel(self):
        for request in self:
            if request.state in ('completed', 'closed', 'cancelled'):
                raise UserError(_('This request can no longer be cancelled.'))
            request._write_state('cancelled')

    def action_rate(self, rating):
        self.ensure_one()
        if self.state != 'closed':
            raise UserError(_('You can only rate a closed request.'))
        if rating not in ('1', '2', '3', '4', '5'):
            raise UserError(_('Invalid rating.'))
        self.customer_rating = rating
