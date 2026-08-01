from odoo import fields, models


class EssRequestType(models.Model):
    _name = 'ess.request.type'
    _description = 'Employee/Client Request Type'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    description = fields.Text(translate=True)
    requester_kind = fields.Selection([
        ('employee', 'Employee'),
        ('client', 'Client'),
        ('both', 'Both'),
    ], default='both', required=True)
    requires_approval = fields.Boolean(default=True)
    default_assigned_team_id = fields.Many2one('ess.request.team', string='Default Team')
    client_approver_role = fields.Selection([
        ('owner', 'Project Owner'),
        ('client_pm', 'Client Project Manager'),
    ], string='Client-side Approver',
        help='Which entity-side role can approve/reject a client-submitted request of '
             'this type before it reaches the company. Leave empty to let either the '
             "project's Owner or Client Project Manager act.")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)',
         'The request type code must be unique per company.'),
    ]
