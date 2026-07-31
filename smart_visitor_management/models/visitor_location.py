from odoo import fields, models


class VisitorLocation(models.Model):
    _name = 'visitor.location'
    _description = 'Visitor Location'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    notes = fields.Text()

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)',
         'The location code must be unique per company.'),
    ]
