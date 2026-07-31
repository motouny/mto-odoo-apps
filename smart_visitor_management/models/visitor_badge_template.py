from odoo import fields, models


class VisitorBadgeTemplate(models.Model):
    _name = 'visitor.badge.template'
    _description = 'Visitor Badge Template'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    header_text = fields.Char(default='VISITOR')
    footer_text = fields.Char(default='Please return this badge at the exit gate')
    show_photo = fields.Boolean(default=True)
    show_qr = fields.Boolean(default=True)
    show_host = fields.Boolean(default=True)
    active = fields.Boolean(default=True)
    is_default = fields.Boolean(string='Default Template')
