from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    visitor_default_entry_grace_minutes = fields.Integer(
        related='company_id.visitor_default_entry_grace_minutes', readonly=False)
    visitor_require_approval = fields.Boolean(
        related='company_id.visitor_require_approval', readonly=False)
    visitor_auto_expire_enabled = fields.Boolean(
        related='company_id.visitor_auto_expire_enabled', readonly=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    visitor_default_entry_grace_minutes = fields.Integer(default=30)
    visitor_require_approval = fields.Boolean(default=True)
    visitor_auto_expire_enabled = fields.Boolean(default=True)
