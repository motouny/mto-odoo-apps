from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sa_gov_is_large_entity = fields.Boolean(
        related='company_id.sa_gov_is_large_entity', readonly=False)
    sa_gov_asset_entity_name = fields.Char(
        related='company_id.sa_gov_asset_entity_name', readonly=False)
    sa_gov_asset_entity_code = fields.Char(
        related='company_id.sa_gov_asset_entity_code', readonly=False)
