import secrets
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

TOKEN_BYTES = 32
MANAGER_GROUP = 'smart_visitor_management.group_visitor_manager'
RECEPTIONIST_GROUP = 'smart_visitor_management.group_visitor_receptionist'
SECURITY_GROUP = 'smart_visitor_management.group_visitor_security'


class VisitorVisit(models.Model):
    _name = 'visitor.visit'
    _description = 'Visitor Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_start desc, id desc'

    name = fields.Char(
        required=True, copy=False, readonly=True, default=lambda self: _('New'))
    visit_type = fields.Selection([
        ('individual', 'Individual'),
        ('group', 'Group'),
    ], default='individual', required=True, tracking=True)

    guest_id = fields.Many2one(
        'visitor.guest', string='Primary Guest', required=True,
        tracking=True, ondelete='restrict')
    guest_ids = fields.Many2many(
        'visitor.guest', 'visitor_visit_guest_rel', 'visit_id', 'guest_id',
        string='Accompanying Guests',
        help='Additional guests included in this visit (group visits).')

    host_id = fields.Many2one(
        'visitor.host', string='Host', required=True, tracking=True, ondelete='restrict')
    department_id = fields.Many2one(
        'visitor.department', string='Department', tracking=True, ondelete='restrict')

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company, tracking=True)
    location_id = fields.Many2one('visitor.location', required=True, tracking=True)
    gate_id = fields.Many2one(
        'visitor.gate', string='Expected Gate',
        domain="[('location_id', '=', location_id)]")

    visit_purpose = fields.Text(required=True)
    visit_start = fields.Datetime(required=True, tracking=True)
    visit_end = fields.Datetime(required=True, tracking=True)
    entry_grace_minutes = fields.Integer(
        default=lambda self: self.env.company.visitor_default_entry_grace_minutes or 30,
        help='Minutes before Visit Start during which check-in is still allowed.')

    equipment_carried = fields.Text()
    notes = fields.Text()

    vehicle_ids = fields.One2many('visitor.vehicle', 'visit_id', string='Vehicles')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('blacklisted', 'Blacklisted'),
    ], default='draft', required=True, tracking=True, copy=False)

    approved_by = fields.Many2one('res.users', readonly=True, copy=False)
    approval_date = fields.Datetime(readonly=True, copy=False)
    rejection_reason = fields.Text(copy=False)

    # Public self-registration token: lets the invited guest complete
    # their own details without any Odoo account.
    invitation_token = fields.Char(
        readonly=True, copy=False, default=lambda self: secrets.token_urlsafe(TOKEN_BYTES))
    invitation_completed = fields.Boolean(default=False, copy=False)

    # QR check-in token: single purpose, random, only valid while the
    # visit is approved/scheduled and inside the allowed window.
    qr_token = fields.Char(readonly=True, copy=False, index='btree_not_null')
    qr_expiry = fields.Datetime(readonly=True, copy=False)
    qr_revoked = fields.Boolean(default=False, copy=False)

    badge_number = fields.Char(readonly=True, copy=False)

    check_in_datetime = fields.Datetime(readonly=True, copy=False)
    check_in_gate_id = fields.Many2one('visitor.gate', readonly=True, copy=False)
    checked_in_by_uid = fields.Many2one('res.users', readonly=True, copy=False)

    check_out_datetime = fields.Datetime(readonly=True, copy=False)
    check_out_gate_id = fields.Many2one('visitor.gate', readonly=True, copy=False)
    checked_out_by_uid = fields.Many2one('res.users', readonly=True, copy=False)

    checkpoint_log_ids = fields.One2many(
        'visitor.checkpoint.log', 'visit_id', string='Scan Log')

    is_overstayed = fields.Boolean(compute='_compute_is_overstayed')

    _sql_constraints = [
        ('visit_dates_check', 'CHECK(visit_end > visit_start)',
         'Visit End must be after Visit Start.'),
    ]

    @api.depends('state', 'visit_end')
    def _compute_is_overstayed(self):
        now = fields.Datetime.now()
        for visit in self:
            visit.is_overstayed = visit.state == 'checked_in' and bool(
                visit.visit_end) and now > visit.visit_end

    @api.onchange('host_id')
    def _onchange_host_id(self):
        for visit in self:
            if visit.host_id.department_id:
                visit.department_id = visit.host_id.department_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('visitor.visit') or _('New')
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('name', _('New'))
        default.setdefault('state', 'draft')
        default.setdefault('qr_token', False)
        default.setdefault('invitation_token', secrets.token_urlsafe(TOKEN_BYTES))
        return super().copy(default)

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def _check_any_group(self, *xmlids):
        if self.env.su:
            return
        user = self.env.user
        if not any(user.has_group(xmlid) for xmlid in xmlids):
            raise AccessError(_('You are not allowed to perform this action.'))

    def action_submit(self):
        for visit in self:
            if visit.state != 'draft':
                raise UserError(_('Only draft visits can be submitted.'))
            visit.state = 'pending_approval'
            if not visit.company_id.visitor_require_approval:
                # Policy-driven auto-approval: not a manual approval by the
                # submitter, so the manager-only guard does not apply here.
                visit._do_approve()

    def action_approve(self):
        self._check_any_group(MANAGER_GROUP)
        self._do_approve()

    def _do_approve(self):
        for visit in self:
            if visit.state != 'pending_approval':
                raise UserError(_('Only visits pending approval can be approved.'))
            if self.env['visitor.blacklist']._is_blacklisted(
                    visit.guest_id.identity_type, visit.guest_id.identity_number,
                    visit.company_id.id):
                visit.state = 'blacklisted'
                continue
            visit.write({
                'state': 'scheduled' if visit.visit_start > fields.Datetime.now() else 'approved',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'qr_token': secrets.token_urlsafe(TOKEN_BYTES),
                'qr_expiry': visit.visit_end,
                'qr_revoked': False,
            })
            if visit.state in ('approved', 'scheduled') and visit.guest_id.email:
                self.env.ref(
                    'smart_visitor_management.mail_template_visitor_approved'
                ).send_mail(visit.id, force_send=True)

    def action_reject(self, reason=False):
        self._check_any_group(MANAGER_GROUP)
        for visit in self:
            if visit.state not in ('draft', 'pending_approval'):
                raise UserError(_('Only draft or pending visits can be rejected.'))
            visit.write({
                'state': 'rejected',
                'rejection_reason': reason or visit.rejection_reason,
                'qr_token': False,
                'qr_revoked': True,
            })
            if visit.guest_id.email:
                self.env.ref(
                    'smart_visitor_management.mail_template_visitor_rejected'
                ).send_mail(visit.id, force_send=True)

    def action_send_invitation(self):
        for visit in self:
            if not visit.guest_id.email:
                raise UserError(_('The primary guest has no email address.'))
            self.env.ref(
                'smart_visitor_management.mail_template_visitor_invitation'
            ).send_mail(visit.id, force_send=True)

    def action_cancel(self):
        for visit in self:
            if visit.state in ('checked_out', 'cancelled'):
                raise UserError(_('This visit cannot be cancelled anymore.'))
            visit.write({'state': 'cancelled', 'qr_token': False, 'qr_revoked': True})

    def action_mark_no_show(self):
        self._check_any_group(MANAGER_GROUP, RECEPTIONIST_GROUP)
        for visit in self:
            if visit.state not in ('approved', 'scheduled'):
                raise UserError(_('Only approved or scheduled visits can be marked as no-show.'))
            visit.write({
                'state': 'expired', 'qr_token': False, 'qr_revoked': True,
                'notes': (visit.notes or '') + '\n' + _('Marked as No Show.'),
            })

    def action_add_to_blacklist(self):
        self.ensure_one()
        self._check_any_group(MANAGER_GROUP, RECEPTIONIST_GROUP)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'visitor.blacklist',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.guest_id.name,
                'default_identity_type': self.guest_id.identity_type,
                'default_identity_number': self.guest_id.identity_number,
                'default_company_id': self.company_id.id,
            },
        }

    def action_reset_to_draft(self):
        for visit in self:
            if visit.state not in ('rejected', 'cancelled', 'expired'):
                raise UserError(_('Only rejected, cancelled or expired visits can be reset.'))
            visit.write({
                'state': 'draft', 'qr_token': False, 'qr_revoked': False,
                'rejection_reason': False,
            })

    def action_manual_checkin(self):
        self.ensure_one()
        self._check_any_group(MANAGER_GROUP, RECEPTIONIST_GROUP, SECURITY_GROUP)
        result = self._process_checkin(self.qr_token, gate_id=self.gate_id.id, manual=True)
        if not result['ok']:
            raise UserError(result['message'])

    def action_manual_checkout(self):
        self.ensure_one()
        self._check_any_group(MANAGER_GROUP, RECEPTIONIST_GROUP, SECURITY_GROUP)
        result = self._process_checkout(self.qr_token, gate_id=self.check_in_gate_id.id, manual=True)
        if not result['ok']:
            raise UserError(result['message'])

    def action_print_badge(self):
        self.ensure_one()
        if not self.badge_number:
            self.badge_number = self.name.replace('VIS/', 'BDG/')
        return self.env.ref(
            'smart_visitor_management.action_report_visitor_badge'
        ).with_context(discard_logo_check=True).report_action(self)

    def action_print_vehicle_permit(self):
        self.ensure_one()
        if not self.vehicle_ids:
            raise UserError(_('This visit has no vehicle registered.'))
        return self.env.ref(
            'smart_visitor_management.action_report_vehicle_permit'
        ).with_context(discard_logo_check=True).report_action(self)

    # ------------------------------------------------------------------
    # QR verification (called by the kiosk controller, sudo-scoped)
    # ------------------------------------------------------------------
    @api.model
    def _log_scan(self, visit, scan_type, scan_result, gate_id, note=False, guest_name=False):
        self.env['visitor.checkpoint.log'].sudo().create({
            'visit_id': visit.id if visit else False,
            'guest_name': guest_name or (visit.guest_id.name if visit else False),
            'gate_id': gate_id,
            'company_id': (visit.company_id.id if visit else self.env.company.id),
            'scan_type': scan_type,
            'scan_result': scan_result,
            'scanned_by_uid': self.env.user.id,
            'note': note,
        })

    @api.model
    def _process_checkin(self, token, gate_id=False, manual=False):
        visit = self.sudo().search([('qr_token', '=', token)], limit=1) if token else self.browse()
        if not visit:
            self._log_scan(False, 'check_in', 'invalid_token', gate_id)
            return {'ok': False, 'message': _('Invalid or unknown QR code.')}

        if self.env['visitor.blacklist']._is_blacklisted(
                visit.guest_id.identity_type, visit.guest_id.identity_number, visit.company_id.id):
            visit.sudo().write({'state': 'blacklisted', 'qr_token': False, 'qr_revoked': True})
            self._log_scan(visit, 'check_in', 'blacklisted', gate_id)
            return {'ok': False, 'message': _('This guest is blacklisted.')}

        if visit.qr_revoked or visit.state not in ('approved', 'scheduled'):
            self._log_scan(visit, 'check_in', 'revoked', gate_id)
            return {'ok': False, 'message': _('This visit is not approved for check-in.')}

        now = fields.Datetime.now()
        window_start = visit.visit_start - timedelta(minutes=visit.entry_grace_minutes or 0)
        if now < window_start or now > visit.visit_end:
            self._log_scan(visit, 'check_in', 'outside_window', gate_id)
            return {'ok': False, 'message': _('Outside the allowed entry window.')}

        if visit.qr_expiry and now > visit.qr_expiry:
            self._log_scan(visit, 'check_in', 'expired', gate_id)
            return {'ok': False, 'message': _('This QR code has expired.')}

        visit.sudo().write({
            'state': 'checked_in',
            'check_in_datetime': now,
            'check_in_gate_id': gate_id or visit.gate_id.id,
            'checked_in_by_uid': self.env.user.id,
            'badge_number': visit.badge_number or visit.name.replace('VIS/', 'BDG/'),
        })
        self._log_scan(
            visit, 'check_in', 'success', gate_id,
            note=_('Manual check-in') if manual else _('QR check-in'))
        return {'ok': True, 'message': _('Checked in successfully.'), 'visit_id': visit.id}

    @api.model
    def _process_checkout(self, token, gate_id=False, manual=False):
        visit = self.sudo().search([('qr_token', '=', token)], limit=1) if token else self.browse()
        if not visit:
            self._log_scan(False, 'check_out', 'invalid_token', gate_id)
            return {'ok': False, 'message': _('Invalid or unknown QR code.')}

        if visit.state != 'checked_in':
            self._log_scan(visit, 'check_out', 'wrong_state', gate_id)
            return {'ok': False, 'message': _('This visit is not currently checked in.')}

        now = fields.Datetime.now()
        visit.sudo().write({
            'state': 'checked_out',
            'check_out_datetime': now,
            'check_out_gate_id': gate_id or visit.check_in_gate_id.id,
            'checked_out_by_uid': self.env.user.id,
            'qr_token': False,
            'qr_revoked': True,
        })
        self._log_scan(
            visit, 'check_out', 'success', gate_id,
            note=_('Manual check-out') if manual else _('QR check-out'))
        return {'ok': True, 'message': _('Checked out successfully.'), 'visit_id': visit.id}

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    @api.model
    def _cron_expire_overdue_visits(self):
        now = fields.Datetime.now()
        overdue = self.search([
            ('state', 'in', ('approved', 'scheduled', 'pending_approval')),
            ('visit_end', '<', now),
        ])
        overdue.write({'state': 'expired', 'qr_token': False, 'qr_revoked': True})
