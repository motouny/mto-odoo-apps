from odoo import fields, models


class DigitalSignatureTemplate(models.Model):
    _name = 'digital.signature.template'
    _description = 'Signature Request Template'
    _order = 'name'

    name = fields.Char(required=True)
    description = fields.Text()
    template_file = fields.Binary(string='Template PDF', attachment=True)
    template_filename = fields.Char()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    field_ids = fields.One2many(
        'digital.signature.template.field', 'template_id', string='Field Layout')
