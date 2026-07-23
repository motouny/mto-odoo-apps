from odoo import api, fields, models

# Fixed 4th-segment "accounting classification" codes, per the MOF guide
# (الدليل الشامل لحصر وتقييم الأصول للجهات الحكومية, §6.5, p.98). Code 02
# is never stored on a classification row - it is computed at runtime on
# the asset itself when the acquisition cost is below the category's
# capitalization threshold (see sa_gov_asset.py).
ACCOUNTING_CLASS_SELECTION = [
    ('01', 'PPE - الآلات والمعدات والعقارات'),
    ('02', 'Under Capitalization Threshold - الأصول تحت حد الرسملة'),
    ('03', 'Investment Property - العقارات الاستثمارية'),
    ('04', 'Service Concession Assets - أصول ترتيب امتياز تقديم الخدمات'),
    ('05', 'Intangible Assets - الأصول الغير ملموسة'),
    ('06', 'Biological Assets - أصول بيولوجية'),
]


class SaGovAssetClassification(models.Model):
    _name = 'sa.gov.asset.classification'
    _description = 'MOF Asset Classification & Coding'
    _order = 'full_code'
    _rec_name = 'display_name'

    l1_code = fields.Char('Level 1 Code', required=True, size=2)
    l1_name = fields.Char('Level 1 (Main Group)', required=True)
    l1_name_en = fields.Char('Level 1 (English)')

    l2_code = fields.Char('Level 2 Code', required=True, size=2)
    l2_name = fields.Char('Level 2 (Sub-Group)', required=True)
    l2_name_en = fields.Char('Level 2 (English)')

    l3_code = fields.Char('Level 3 Code', required=True, size=2)
    l3_name = fields.Char('Level 3 (Asset Type)', required=True)
    l3_name_en = fields.Char('Level 3 (English)')

    natural_accounting_class = fields.Selection(
        ACCOUNTING_CLASS_SELECTION, string='Natural Accounting Classification',
        required=True,
        help='The accounting classification this asset type naturally takes '
             'when it is capitalized. Replaced at runtime by 02 (under '
             'capitalization threshold) when the acquisition cost is below '
             'this category\'s threshold.')

    classification_code = fields.Char(
        'Classification Code', size=6, required=True, index=True,
        help='L1+L2+L3, 6 digits - the classification prefix shared by all '
             'accounting-classification variants of this asset type.')
    full_code = fields.Char(
        'Full Classification Code', size=8, required=True, index=True,
        help='Classification code + natural accounting classification, 8 digits.')

    cap_threshold = fields.Float(
        'Capitalization Threshold (SAR)',
        help='Minimum acquisition cost for this asset type to be capitalized. '
             'Empty means no threshold applies (e.g. land, heritage assets, '
             'licenses) - always capitalized regardless of cost.')
    cap_threshold_large_entity = fields.Float(
        'Capitalization Threshold - Large Entities (SAR)',
        help='Alternate, higher threshold for large entities that own '
             'infrastructure and specialized equipment (per the guide), used '
             'instead of the standard threshold when the company is flagged '
             'as such in Settings.')
    has_threshold = fields.Boolean(compute='_compute_has_threshold', store=True)

    useful_life_min = fields.Integer('Useful Life Min (years)')
    useful_life_max = fields.Integer('Useful Life Max (years)')

    active = fields.Boolean(default=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    _sql_constraints = [
        ('full_code_uniq', 'unique(full_code)', 'The full classification code must be unique.'),
    ]

    @api.depends('cap_threshold')
    def _compute_has_threshold(self):
        for rec in self:
            rec.has_threshold = bool(rec.cap_threshold)

    @api.depends('full_code', 'l1_name', 'l2_name', 'l3_name', 'natural_accounting_class')
    def _compute_display_name(self):
        for rec in self:
            ag_label = dict(ACCOUNTING_CLASS_SELECTION).get(rec.natural_accounting_class, '')
            rec.display_name = '[%s] %s / %s / %s (%s)' % (
                rec.full_code, rec.l1_name, rec.l2_name, rec.l3_name, ag_label.split(' - ')[0])

    def get_effective_threshold(self, company):
        """Threshold to apply for the given company, honoring the
        large-entity override where the category defines one."""
        self.ensure_one()
        if not self.cap_threshold:
            return 0.0
        if company.sa_gov_is_large_entity and self.cap_threshold_large_entity:
            return self.cap_threshold_large_entity
        return self.cap_threshold
