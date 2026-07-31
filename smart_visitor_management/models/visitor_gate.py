from odoo import fields, models


class VisitorGate(models.Model):
    _name = 'visitor.gate'
    _description = 'Visitor Gate'
    _order = 'name'

    name = fields.Char(required=True)
    gate_type = fields.Selection([
        ('entry', 'Entry Only'),
        ('exit', 'Exit Only'),
        ('both', 'Entry & Exit'),
    ], default='both', required=True)
    location_id = fields.Many2one('visitor.location', required=True, ondelete='restrict')
    company_id = fields.Many2one(
        related='location_id.company_id', store=True, readonly=True)
    active = fields.Boolean(default=True)
