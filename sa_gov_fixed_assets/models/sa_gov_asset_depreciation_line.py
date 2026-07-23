from odoo import fields, models


class SaGovAssetDepreciationLine(models.Model):
    _name = 'sa.gov.asset.depreciation.line'
    _description = 'Asset Depreciation Line'
    _order = 'asset_id, sequence'

    asset_id = fields.Many2one(
        'sa.gov.asset', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='asset_id.company_id', store=True)
    currency_id = fields.Many2one(related='asset_id.currency_id')
    sequence = fields.Integer(default=1)
    date = fields.Date(required=True)
    depreciation_value = fields.Monetary(currency_field='currency_id')
    accumulated_value = fields.Monetary(currency_field='currency_id')
    remaining_value = fields.Monetary(currency_field='currency_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], default='draft', required=True)

    def action_post(self):
        self.filtered(lambda l: l.state == 'draft').write({'state': 'posted'})
