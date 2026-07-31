from odoo import api, fields, models


class VisitorBlacklist(models.Model):
    _name = 'visitor.blacklist'
    _description = 'Visitor Blacklist'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Guest Name', required=True)
    identity_type = fields.Selection([
        ('national_id', 'National ID'),
        ('iqama', 'Resident ID'),
        ('passport', 'Passport'),
        ('other', 'Other'),
    ], default='national_id', required=True)
    identity_number = fields.Char(required=True)
    reason = fields.Text(required=True)
    blacklisted_by = fields.Many2one(
        'res.users', default=lambda self: self.env.user, readonly=True)
    blacklist_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.model
    def _is_blacklisted(self, identity_type, identity_number, company_id):
        if not identity_number:
            return False
        return bool(self.search_count([
            ('identity_type', '=', identity_type),
            ('identity_number', '=', identity_number),
            ('company_id', '=', company_id),
            ('active', '=', True),
        ]))
