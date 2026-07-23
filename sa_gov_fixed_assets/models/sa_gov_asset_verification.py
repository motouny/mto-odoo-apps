from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaGovAssetVerification(models.Model):
    _name = 'sa.gov.asset.verification'
    _description = 'Physical Verification Campaign (جرد)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'

    name = fields.Char(required=True, copy=False, default=lambda self: _('New'))
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    date_start = fields.Date(default=fields.Date.context_today, tracking=True)
    date_deadline = fields.Date(tracking=True)
    responsible_id = fields.Many2one(
        'res.users', string='Inventory Team Lead', default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], default='draft', required=True, tracking=True, copy=False)
    line_ids = fields.One2many(
        'sa.gov.asset.verification.line', 'verification_id', string='Assets to Verify')
    line_count = fields.Integer(compute='_compute_counts')
    discrepancy_count = fields.Integer(compute='_compute_counts')
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'sa.gov.asset.verification') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.discrepancy_type')
    def _compute_counts(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)
            rec.discrepancy_count = len(rec.line_ids.filtered('discrepancy_type'))

    def action_populate_from_domain(self, domain=None):
        """Bulk-add all matching (or all) capitalized/registered assets as
        verification lines - the physical/field inventory step (guide
        §7.5, p.134)."""
        for campaign in self:
            assets = self.env['sa.gov.asset'].search(
                domain or [('company_id', '=', campaign.company_id.id),
                           ('state', 'in', ('registered', 'in_service'))])
            existing = campaign.line_ids.asset_id
            new_assets = assets - existing
            campaign.line_ids = [(0, 0, {
                'asset_id': asset.id,
                'expected_location': ', '.join(filter(None, [
                    asset.building_number, asset.floor_number, asset.room_number])),
                'expected_condition': asset.condition,
            }) for asset in new_assets]

    def action_start(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft campaigns can be started.'))
            rec.state = 'in_progress'

    def action_done(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError(_('Only in-progress campaigns can be closed.'))
            rec.state = 'done'
            for line in rec.line_ids:
                if line.found and line.condition_found:
                    line.asset_id.condition = line.condition_found


class SaGovAssetVerificationLine(models.Model):
    _name = 'sa.gov.asset.verification.line'
    _description = 'Physical Verification Line'

    verification_id = fields.Many2one(
        'sa.gov.asset.verification', required=True, ondelete='cascade', index=True)
    asset_id = fields.Many2one(
        'sa.gov.asset', required=True, ondelete='cascade', index=True)
    asset_code = fields.Char(related='asset_id.asset_code', store=True)
    expected_location = fields.Char()
    expected_condition = fields.Selection(related='asset_id.condition', string='Expected Condition')

    inspection_date = fields.Date(default=fields.Date.context_today)
    found = fields.Boolean(default=True)
    location_matches = fields.Boolean(default=True)
    condition_found = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ])

    discrepancy_type = fields.Selection([
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
        ('stolen', 'Stolen'),
    ], help='Set when the physical count does not match the register '
            '(guide §7.5, Inventory Committee discrepancy report, p.135).')
    responsible_user_id = fields.Many2one(
        'res.users', string='Responsible Person',
        help='Person tied to the investigation when a discrepancy is found.')
    investigation_notes = fields.Text()

    @api.onchange('found')
    def _onchange_found(self):
        if not self.found and not self.discrepancy_type:
            self.discrepancy_type = 'lost'
