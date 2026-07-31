from odoo import fields, models


class VisitorDepartment(models.Model):
    _name = 'visitor.department'
    _description = 'Visitor Department'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    manager_id = fields.Many2one('res.users', string='Department Manager', ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    notes = fields.Text()

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)',
         'The department code must be unique per company.'),
    ]
