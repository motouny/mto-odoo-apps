from odoo import fields, models


class EssRequestTeam(models.Model):
    _name = 'ess.request.team'
    _description = 'Request Handling Team'
    _order = 'name'

    name = fields.Char(required=True)
    member_ids = fields.Many2many('res.users', string='Members')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
