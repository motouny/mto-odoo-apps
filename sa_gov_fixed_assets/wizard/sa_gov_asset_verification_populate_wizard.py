from odoo import fields, models


class SaGovAssetVerificationPopulateWizard(models.TransientModel):
    _name = 'sa.gov.asset.verification.populate.wizard'
    _description = 'Add Assets to Verification Campaign'

    verification_id = fields.Many2one(
        'sa.gov.asset.verification', required=True,
        default=lambda self: self.env.context.get('active_id'))
    classification_id = fields.Many2one('sa.gov.asset.classification')
    custodian_department = fields.Char()
    building_number = fields.Char()
    only_capitalized = fields.Boolean(default=False)

    def action_populate(self):
        self.ensure_one()
        domain = [
            ('company_id', '=', self.verification_id.company_id.id),
            ('state', 'in', ('registered', 'in_service')),
        ]
        if self.classification_id:
            domain.append(('classification_id', '=', self.classification_id.id))
        if self.custodian_department:
            domain.append(('custodian_department', 'ilike', self.custodian_department))
        if self.building_number:
            domain.append(('building_number', '=', self.building_number))
        if self.only_capitalized:
            domain.append(('is_capitalized', '=', True))
        self.verification_id.action_populate_from_domain(domain)
        return {'type': 'ir.actions.act_window_close'}
