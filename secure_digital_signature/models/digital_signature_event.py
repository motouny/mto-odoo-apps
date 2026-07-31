from odoo import _, fields, models
from odoo.exceptions import AccessError


class DigitalSignatureEvent(models.Model):
    _name = 'digital.signature.event'
    _description = 'Signature Audit Event'
    _order = 'event_date desc'

    request_id = fields.Many2one(
        'digital.signature.request', required=True, ondelete='cascade', index=True)
    signer_id = fields.Many2one('digital.signature.signer', ondelete='set null')
    event_type = fields.Selection([
        ('created', 'Created'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('field_filled', 'Field Filled'),
        ('signed', 'Signed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('resent', 'Resent'),
        ('reminded', 'Reminder Sent'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('verified', 'Publicly Verified'),
        ('tamper_detected', 'Tamper Detected'),
    ], required=True)
    event_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    ip_address = fields.Char(readonly=True)
    user_agent = fields.Char(readonly=True)
    note = fields.Char()
    company_id = fields.Many2one(related='request_id.company_id', store=True)

    def write(self, vals):
        if not self.env.su:
            raise AccessError(_('Audit events are immutable and cannot be modified.'))
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise AccessError(_('Audit events are immutable and cannot be deleted.'))
        return super().unlink()
