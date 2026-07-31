import secrets

from odoo import _, api, fields, models

TOKEN_BYTES = 32


class DigitalSignatureSigner(models.Model):
    _name = 'digital.signature.signer'
    _description = 'Signature Request Signer'
    _order = 'sequence, id'

    request_id = fields.Many2one(
        'digital.signature.request', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    signer_type = fields.Selection([
        ('internal', 'Internal User'),
        ('portal', 'Portal Contact'),
        ('external', 'External (no Odoo account)'),
    ], default='external', required=True)
    user_id = fields.Many2one('res.users', string='Internal User')
    partner_id = fields.Many2one('res.partner', string='Contact')
    name = fields.Char(required=True)
    email = fields.Char(required=True)

    token = fields.Char(readonly=True, copy=False, index='btree_not_null')
    token_expiry = fields.Datetime(readonly=True, copy=False)
    token_revoked = fields.Boolean(default=False, copy=False)

    status = fields.Selection([
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('signed', 'Signed'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ], default='pending', required=True, copy=False)

    sent_date = fields.Datetime(readonly=True, copy=False)
    viewed_date = fields.Datetime(readonly=True, copy=False)
    signed_date = fields.Datetime(readonly=True, copy=False)
    rejection_reason = fields.Text(copy=False)
    signed_ip = fields.Char(readonly=True, copy=False)
    signed_user_agent = fields.Char(readonly=True, copy=False)

    field_ids = fields.One2many('digital.signature.field', 'signer_id', string='Fields')
    company_id = fields.Many2one(related='request_id.company_id', store=True)

    @api.onchange('user_id')
    def _onchange_user_id(self):
        for signer in self:
            if signer.user_id:
                signer.signer_type = 'internal'
                signer.name = signer.name or signer.user_id.name
                signer.email = signer.user_id.email

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for signer in self:
            if signer.partner_id:
                signer.name = signer.name or signer.partner_id.name
                signer.email = signer.partner_id.email

    def _generate_token(self):
        for signer in self:
            signer.write({
                'token': secrets.token_urlsafe(TOKEN_BYTES),
                'token_expiry': signer.request_id.expiration_date,
                'token_revoked': False,
            })

    def _revoke_token(self):
        self.write({'token_revoked': True})

    def action_open_fields(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'digital.signature.signer',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_ref': 'secure_digital_signature.view_digital_signature_signer_field_form'},
        }

    def all_required_fields_filled(self):
        self.ensure_one()
        required = self.field_ids.filtered('required')
        for field in required:
            if field.field_type in ('signature', 'initials', 'stamp'):
                if not field.signature_image:
                    return False
            elif not field.value:
                return False
        return True
