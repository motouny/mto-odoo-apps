from odoo import fields, models

FIELD_TYPES = [
    ('signature', 'Signature'),
    ('initials', 'Initials'),
    ('name', 'Name'),
    ('date', 'Date'),
    ('text', 'Text'),
    ('checkbox', 'Checkbox'),
    ('selection', 'Selection'),
    ('stamp', 'Stamp'),
]


class DigitalSignatureTemplateField(models.Model):
    _name = 'digital.signature.template.field'
    _description = 'Signature Template Field'
    _order = 'page_number, id'

    template_id = fields.Many2one(
        'digital.signature.template', required=True, ondelete='cascade')
    field_type = fields.Selection(FIELD_TYPES, required=True, default='signature')
    signer_role = fields.Char(
        string='Signer Role', default='Signer 1',
        help='Free-text role label (e.g. "Signer 1", "Approver") used to '
             'match this field to a signer when the template is applied.')
    page_number = fields.Integer(default=1, required=True)
    pos_x = fields.Float(string='X (%)', required=True, help='0-100, from the left edge.')
    pos_y = fields.Float(string='Y (%)', required=True, help='0-100, from the top edge.')
    width = fields.Float(default=20.0, help='Percent of page width.')
    height = fields.Float(default=5.0, help='Percent of page height.')
    required = fields.Boolean(default=True)
    selection_options = fields.Char(help='Comma-separated options for a Selection field.')
