from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    portal_manager_id = fields.Many2one(
        'res.users', string='Portal Manager',
        help='Portal user who can review this project\'s employees and approve '
             'their time off requests from the employee portal. Independent from '
             'the Project Manager above, which requires an internal user.',
    )
