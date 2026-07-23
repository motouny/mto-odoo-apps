from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .sa_gov_asset_classification import ACCOUNTING_CLASS_SELECTION

MANAGER_GROUP = 'sa_gov_fixed_assets.group_sa_asset_manager'


class SaGovAsset(models.Model):
    _name = 'sa.gov.asset'
    _description = 'Government Fixed Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'asset_code'

    name = fields.Char(
        'Asset Description', required=True, tracking=True,
        help='وصف الأصل - description of the asset for identification purposes.')
    asset_code = fields.Char(
        'MOF Asset Code', readonly=True, copy=False, index=True, tracking=True,
        help='Classification code + accounting classification + sequence, '
             'e.g. 10020201-0001, per the guide\'s coding methodology (p.98-99).')
    sequence_number = fields.Char(readonly=True, copy=False)

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company, tracking=True)
    currency_id = fields.Many2one(related='company_id.currency_id')

    classification_id = fields.Many2one(
        'sa.gov.asset.classification', string='Classification', required=True,
        tracking=True, ondelete='restrict',
        help='Select the MOF classification matching this asset\'s nature '
             '(main group / sub-group / asset type / accounting nature).')
    l1_name = fields.Char(related='classification_id.l1_name', string='Main Group', store=True)
    l2_name = fields.Char(related='classification_id.l2_name', string='Sub-Group', store=True)
    l3_name = fields.Char(related='classification_id.l3_name', string='Asset Type', store=True)
    classification_code = fields.Char(related='classification_id.classification_code', store=True)

    accounting_class = fields.Selection(
        ACCOUNTING_CLASS_SELECTION, string='Accounting Classification',
        compute='_compute_capitalization', store=True,
        help='02 (under capitalization threshold) is applied automatically '
             'when the acquisition cost is below this asset type\'s '
             'capitalization threshold; otherwise the classification\'s '
             'natural accounting classification applies.')
    is_capitalized = fields.Boolean(
        'Capitalized (مرسملة)', compute='_compute_capitalization', store=True,
        help='Capitalized assets are depreciated fixed assets. '
             'Non-capitalized assets (غير مرسملة) are expensed on issue but '
             'remain coded and tracked in this register per the guide (p.23).')
    capitalization_override = fields.Boolean(
        'Manual Capitalization Override',
        help='Force this asset\'s capitalized/non-capitalized status instead '
             'of the automatic threshold determination.')
    capitalization_override_value = fields.Boolean('Override: Capitalized')
    capitalization_override_reason = fields.Text('Override Reason')

    effective_threshold = fields.Float(
        compute='_compute_capitalization', store=True,
        string='Applicable Capitalization Threshold')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('wip', 'Under Construction (أصول تحت الإنشاء)'),
        ('registered', 'Registered & Capitalized (تسجيل ورسملة)'),
        ('in_service', 'In Service'),
        ('disposed', 'Disposed'),
        ('transferred', 'Transferred'),
    ], default='draft', required=True, tracking=True, copy=False)

    # ------------------------------------------------------------------
    # Acquisition
    # ------------------------------------------------------------------
    acquisition_method = fields.Selection([
        ('purchase', 'Purchase'),
        ('construction', 'Self-Construction'),
        ('donation', 'Donation'),
        ('transfer_in', 'Transfer from Another Entity'),
        ('other', 'Other'),
    ], default='purchase', tracking=True)
    acquisition_date = fields.Date(tracking=True)
    acquisition_cost = fields.Monetary(
        'Acquisition Cost', currency_field='currency_id', tracking=True,
        help='تكلفة الاقتناء - cost the asset was acquired for.')
    ownership_document_type = fields.Char('Ownership Document Type')
    ownership_document_number = fields.Char('Ownership Document Number')
    ownership_document_date = fields.Date('Ownership Document Date')
    archive_document_number = fields.Char('Supporting Document Archive Number')

    date_placed_in_service = fields.Date(
        tracking=True, help='Determines the point when depreciation begins.')

    # ------------------------------------------------------------------
    # Location / custody
    # ------------------------------------------------------------------
    country_id = fields.Many2one('res.country', default=lambda self: self.env.company.country_id)
    region = fields.Char()
    city = fields.Char()
    building_number = fields.Char()
    floor_number = fields.Char()
    room_number = fields.Char()
    national_address = fields.Char()
    geo_coordinates = fields.Char('Geographic Coordinates')
    custodian_department = fields.Char('Custodian Department/Section')
    responsible_user_id = fields.Many2one('res.users', string='Responsible Person')

    # ------------------------------------------------------------------
    # Condition & tagging
    # ------------------------------------------------------------------
    condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ], default='good', tracking=True)
    asset_utilization = fields.Selection([
        ('in_use', 'In Use'),
        ('not_in_use', 'Not In Use'),
        ('partial', 'Partially Used'),
        ('backup', 'Backup/Reserve'),
    ], default='in_use')
    tag_number = fields.Char(copy=False, tracking=True)
    old_tag_number = fields.Char(copy=False)
    tag_ids = fields.One2many('sa.gov.asset.tag', 'asset_id', string='Tag History')
    photo = fields.Image(max_width=1024, max_height=1024)

    related_asset_id = fields.Many2one(
        'sa.gov.asset', string='Linked/Associated Asset', ondelete='set null',
        help='E.g. the land a building sits on, where relevant.')

    # ------------------------------------------------------------------
    # Depreciation
    # ------------------------------------------------------------------
    useful_life_years = fields.Integer('Useful Life (years)', tracking=True)
    salvage_value = fields.Monetary('Salvage Value', currency_field='currency_id', default=0.0)
    depreciable_value = fields.Monetary(
        compute='_compute_depreciation_totals', store=True, currency_field='currency_id')
    accumulated_depreciation = fields.Monetary(
        compute='_compute_depreciation_totals', store=True, currency_field='currency_id')
    book_value = fields.Monetary(
        compute='_compute_depreciation_totals', store=True, currency_field='currency_id')
    depreciation_line_ids = fields.One2many(
        'sa.gov.asset.depreciation.line', 'asset_id', string='Depreciation Schedule')

    # ------------------------------------------------------------------
    # Type-specific detail (family-specific fields, one optional record)
    # ------------------------------------------------------------------
    type_detail_ids = fields.One2many(
        'sa.gov.asset.type.detail', 'asset_id', string='Type-Specific Details')

    # ------------------------------------------------------------------
    # Disposal / transfer
    # ------------------------------------------------------------------
    disposal_method = fields.Selection([
        ('write_off', 'Write-off (شطب)'),
        ('destroy', 'Destruction (إتلاف)'),
        ('sell', 'Sale (بيع)'),
    ], copy=False, tracking=True)
    disposal_date = fields.Date(copy=False, tracking=True)
    disposal_reason = fields.Text(copy=False)
    disposal_proceeds = fields.Monetary(
        'Disposal Proceeds', currency_field='currency_id', copy=False)
    transfer_destination = fields.Char('Transferred To', copy=False)
    transfer_date = fields.Date(copy=False)

    notes = fields.Text()

    _sql_constraints = [
        ('asset_code_uniq', 'unique(company_id, asset_code)',
         'The MOF asset code must be unique per company.'),
    ]

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends('acquisition_cost', 'classification_id', 'capitalization_override',
                 'capitalization_override_value', 'company_id')
    def _compute_capitalization(self):
        for asset in self:
            cls = asset.classification_id
            threshold = cls.get_effective_threshold(asset.company_id) if cls else 0.0
            asset.effective_threshold = threshold
            if asset.capitalization_override:
                capitalized = asset.capitalization_override_value
            else:
                capitalized = not (threshold and asset.acquisition_cost < threshold)
            asset.is_capitalized = capitalized
            if capitalized:
                asset.accounting_class = cls.natural_accounting_class if cls else False
            else:
                asset.accounting_class = '02'

    @api.depends('depreciation_line_ids.depreciation_value', 'depreciation_line_ids.state',
                 'acquisition_cost', 'salvage_value')
    def _compute_depreciation_totals(self):
        for asset in self:
            asset.depreciable_value = max(asset.acquisition_cost - asset.salvage_value, 0.0)
            posted = asset.depreciation_line_ids.filtered(lambda l: l.state == 'posted')
            asset.accumulated_depreciation = sum(posted.mapped('depreciation_value'))
            asset.book_value = asset.acquisition_cost - asset.accumulated_depreciation

    @api.constrains('useful_life_years', 'classification_id')
    def _check_useful_life(self):
        for asset in self:
            cls = asset.classification_id
            if not cls or not asset.useful_life_years or not asset.is_capitalized:
                continue
            lo, hi = cls.useful_life_min, cls.useful_life_max
            if lo and hi and not (lo <= asset.useful_life_years <= hi):
                raise ValidationError(_(
                    'The useful life for "%(cls)s" must be between %(lo)s and %(hi)s years '
                    'per the MOF guide (got %(val)s).',
                    cls=cls.l3_name, lo=lo, hi=hi, val=asset.useful_life_years))

    # ------------------------------------------------------------------
    # Coding / registration
    # ------------------------------------------------------------------
    def _generate_asset_code(self):
        self.ensure_one()
        if not self.classification_id or not self.accounting_class:
            raise UserError(_('Set a classification before registering the asset.'))
        if not self.sequence_number:
            seq = self.env['ir.sequence'].next_by_code('sa.gov.asset') or '0001'
            self.sequence_number = seq
        self.asset_code = '%s%s-%s' % (
            self.classification_id.classification_code, self.accounting_class,
            self.sequence_number)

    def action_start_construction(self):
        for asset in self:
            if asset.state != 'draft':
                raise UserError(_('Only draft assets can move to Under Construction.'))
            asset.state = 'wip'

    def action_register(self):
        """تسجيل ورسملة - registration & capitalization (guide §7.1, p.122)."""
        for asset in self:
            if asset.state not in ('draft', 'wip'):
                raise UserError(_('Only draft or under-construction assets can be registered.'))
            if not asset.acquisition_cost:
                raise UserError(_('Set the acquisition cost before registering.'))
            asset._generate_asset_code()
            if not asset.date_placed_in_service:
                asset.date_placed_in_service = asset.acquisition_date or fields.Date.today()
            asset.state = 'registered'
            if asset.is_capitalized:
                asset._generate_depreciation_lines()
                asset.state = 'in_service'

    def _generate_depreciation_lines(self):
        self.ensure_one()
        self.depreciation_line_ids.filtered(lambda l: l.state == 'draft').unlink()
        years = self.useful_life_years or self.classification_id.useful_life_min
        if not years or not self.is_capitalized:
            return
        depreciable = self.depreciable_value
        if depreciable <= 0:
            return
        annual = round(depreciable / years, 2)
        lines = []
        accumulated = 0.0
        start_year = self.date_placed_in_service.year \
            if self.date_placed_in_service else fields.Date.today().year
        for i in range(1, years + 1):
            value = annual if i < years else round(depreciable - accumulated, 2)
            accumulated += value
            lines.append((0, 0, {
                'sequence': i,
                'date': fields.Date.to_date('%s-12-31' % (start_year + i - 1)),
                'depreciation_value': value,
                'accumulated_value': accumulated,
                'remaining_value': round(depreciable - accumulated, 2),
                'state': 'draft',
            }))
        self.depreciation_line_ids = lines

    def action_dispose(self):
        self.ensure_one()
        if self.state not in ('in_service', 'registered'):
            raise UserError(_('Only in-service assets can be disposed.'))
        if not self.disposal_method:
            raise UserError(_('Select a disposal method (write-off, destruction or sale).'))
        self.write({
            'state': 'disposed',
            'disposal_date': self.disposal_date or fields.Date.today(),
        })

    def action_transfer(self):
        self.ensure_one()
        if self.state not in ('in_service', 'registered'):
            raise UserError(_('Only in-service assets can be transferred.'))
        if not self.transfer_destination:
            raise UserError(_('Set the transfer destination before transferring.'))
        self.write({
            'state': 'transferred',
            'transfer_date': self.transfer_date or fields.Date.today(),
        })

    def action_reset_to_draft(self):
        self._check_manager()
        for asset in self:
            asset.write({'state': 'draft', 'asset_code': False, 'sequence_number': False})
            asset.depreciation_line_ids.filtered(lambda l: l.state == 'draft').unlink()

    def _check_manager(self):
        if self.env.su:
            return
        if not self.env.user.has_group(MANAGER_GROUP):
            raise UserError(_('Only an Asset Manager can perform this action.'))
