from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    project_id = fields.Many2one(
        'project.project', string='Portal Project',
        help='Project this employee is reported under in the employee portal. '
             'The project\'s Portal Manager can see this employee\'s status and '
             'approve their time off requests from the portal.',
    )

    def action_grant_portal_access(self):
        self.ensure_one()
        if not self.work_contact_id:
            raise UserError(_("This employee has no related contact to grant portal access to."))
        return self.env['portal.wizard'].with_context(
            default_partner_ids=[self.work_contact_id.id],
        ).action_open_wizard()
