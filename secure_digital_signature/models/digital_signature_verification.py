from odoo import _, fields, models
from odoo.exceptions import AccessError


class DigitalSignatureVerification(models.Model):
    _name = 'digital.signature.verification'
    _description = 'Public Verification Attempt'
    _order = 'verify_date desc'

    request_id = fields.Many2one(
        'digital.signature.request', ondelete='cascade', index=True)
    verify_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    ip_address = fields.Char(readonly=True)
    result = fields.Selection([
        ('valid', 'Valid'),
        ('invalid', 'Invalid / Tampered'),
        ('not_found', 'Not Found'),
    ], required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def write(self, vals):
        if not self.env.su:
            raise AccessError(_('Verification log entries are immutable.'))
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise AccessError(_('Verification log entries are immutable.'))
        return super().unlink()
