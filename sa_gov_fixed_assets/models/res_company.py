from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sa_gov_is_large_entity = fields.Boolean(
        string='Large Entity (Infrastructure & Specialized Equipment)',
        help='Government entities that own infrastructure and specialized '
             'equipment use the higher capitalization threshold defined per '
             'asset category, where the MOF guide provides one (e.g. '
             'furniture/IT: 10,000 SAR instead of 1,000 SAR).')
    sa_gov_asset_entity_name = fields.Char(
        string='MOF Entity Name',
        help='Entity name per the chart of accounts issued by the Ministry '
             'of Finance Budget & Organization Agency.')
    sa_gov_asset_entity_code = fields.Char(
        string='MOF Entity Code',
        help='Entity code per the chart of accounts issued by the Ministry '
             'of Finance Budget & Organization Agency.')
