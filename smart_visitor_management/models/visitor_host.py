from odoo import api, fields, models


class VisitorHost(models.Model):
    _name = 'visitor.host'
    _description = 'Visitor Host'
    _inherit = ['mail.thread']
    _order = 'name'
    _rec_name = 'name'

    user_id = fields.Many2one('res.users', string='Linked User', ondelete='restrict')
    name = fields.Char(required=True)
    department_id = fields.Many2one('visitor.department', string='Department', ondelete='restrict')
    phone = fields.Char()
    mobile = fields.Char()
    email = fields.Char()
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.onchange('user_id')
    def _onchange_user_id(self):
        for host in self:
            if host.user_id:
                host.name = host.name or host.user_id.name
                host.email = host.email or host.user_id.email
