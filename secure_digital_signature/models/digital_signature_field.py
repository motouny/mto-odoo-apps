from odoo import _, fields, models
from odoo.exceptions import UserError

# Attributes a signer legitimately fills in while signing - these remain
# writable after the request has been sent. Everything else defines where
# and what the field *is*, and must be frozen once recipients have been
# notified, so a request cannot be silently altered mid-flight.
FILL_IN_KEYS = {'value', 'signature_image', 'attachment_file', 'attachment_filename'}

FIELD_TYPES = [
    ('signature', 'Signature'),
    ('initials', 'Initials'),
    ('name', 'Name'),
    ('date', 'Date'),
    ('text', 'Text'),
    ('checkbox', 'Checkbox'),
    ('selection', 'Selection'),
    ('stamp', 'Stamp'),
    ('attachment', 'Attachment'),
]


class DigitalSignatureField(models.Model):
    _name = 'digital.signature.field'
    _description = 'Signature Field Placement'
    _order = 'page_number, id'

    request_id = fields.Many2one(
        'digital.signature.request', required=True, ondelete='cascade', index=True)
    signer_id = fields.Many2one(
        'digital.signature.signer', required=True, ondelete='cascade', index=True)
    field_type = fields.Selection(FIELD_TYPES, required=True, default='signature')
    page_number = fields.Integer(default=1, required=True)
    pos_x = fields.Float(string='X (%)', required=True)
    pos_y = fields.Float(string='Y (%)', required=True)
    width = fields.Float(default=20.0)
    height = fields.Float(default=5.0)
    required = fields.Boolean(default=True)
    selection_options = fields.Char(help='Comma-separated options for a Selection field.')

    # Filled-in value once the signer completes this field.
    value = fields.Char(copy=False)
    signature_image = fields.Binary(copy=False, attachment=True)
    attachment_file = fields.Binary(copy=False, attachment=True)
    attachment_filename = fields.Char(copy=False)

    company_id = fields.Many2one(related='request_id.company_id', store=True)

    # Locked once the request has been sent - fields cannot be repositioned
    # or retyped after the recipients have already been notified.
    locked = fields.Boolean(compute='_compute_locked')

    def _compute_locked(self):
        for field in self:
            field.locked = field.request_id.state not in ('draft', 'ready')

    def write(self, vals):
        # No sudo() bypass here, unlike the audit-log style models elsewhere
        # in this app: nothing in this app's own code ever needs to change a
        # field's position/definition after send, so this stays absolute -
        # "prevent field changes after sending" admits no exception.
        definition_keys = set(vals.keys()) - FILL_IN_KEYS
        if definition_keys:
            for field in self:
                if field.request_id.state not in ('draft', 'ready'):
                    raise UserError(_(
                        'Field position/definition cannot change once the request has '
                        'been sent - only the signer-filled value can.'))
        return super().write(vals)

    def unlink(self):
        for field in self:
            if field.request_id.state not in ('draft', 'ready'):
                raise UserError(_(
                    'Fields cannot be removed once the request has been sent.'))
        return super().unlink()
