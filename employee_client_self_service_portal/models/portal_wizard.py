from odoo import models


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    def action_grant_access(self):
        result = super().action_grant_access()
        employee = self.env['hr.employee'].sudo().search([
            ('work_contact_id', '=', self.partner_id.id),
            ('user_id', '=', False),
        ], limit=1)
        if employee:
            employee.user_id = self.user_id.sudo()
        return result
