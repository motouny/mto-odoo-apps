from odoo import fields, models


class VisitorGuest(models.Model):
    _name = 'visitor.guest'
    _description = 'Visitor Guest'
    _order = 'name'

    name = fields.Char(string='Full Name', required=True)
    name_ar = fields.Char(string='Full Name (Arabic)')
    identity_type = fields.Selection([
        ('national_id', 'National ID'),
        ('iqama', 'Resident ID'),
        ('passport', 'Passport'),
        ('other', 'Other'),
    ], default='national_id', required=True)
    identity_number = fields.Char(required=True)
    passport_number = fields.Char()
    nationality_id = fields.Many2one('res.country', string='Nationality')
    company_name = fields.Char(string='Visitor Company')
    mobile = fields.Char()
    email = fields.Char()
    photo = fields.Image(max_width=1024, max_height=1024)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('identity_number_type_uniq', 'unique(identity_type, identity_number)',
         'A guest with this identity type and number already exists.'),
    ]
