import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from . import pdf_engine


class DigitalSignatureDocument(models.Model):
    _name = 'digital.signature.document'
    _description = 'Signature Document Version'
    _order = 'create_date desc'

    request_id = fields.Many2one(
        'digital.signature.request', required=True, ondelete='cascade', index=True)
    document_type = fields.Selection([
        ('original', 'Original'),
        ('final', 'Final Signed'),
        ('certificate', 'Completion Certificate'),
    ], required=True)
    file = fields.Binary(required=True, attachment=True)
    filename = fields.Char(required=True)
    page_count = fields.Integer(readonly=True)
    sha256_hash = fields.Char(readonly=True, copy=False, index=True)
    company_id = fields.Many2one(related='request_id.company_id', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('document_type') == 'original' and vals.get('file'):
                if vals.get('request_id'):
                    request = self.env['digital.signature.request'].browse(vals['request_id'])
                    if request.state != 'draft':
                        raise UserError(
                            _('The original document cannot be replaced once the request '
                              'has left Draft.'))
                file_bytes = base64.b64decode(vals['file'])
                if not vals.get('sha256_hash'):
                    vals['sha256_hash'] = pdf_engine.sha256_hex(file_bytes)
                if not vals.get('page_count'):
                    try:
                        vals['page_count'] = pdf_engine.get_page_count(file_bytes)
                    except Exception:
                        vals['page_count'] = 0
        records = super().create(vals_list)
        for record in records:
            if record.document_type == 'original':
                record.request_id.original_hash = record.sha256_hash
        return records

    def write(self, vals):
        for record in self:
            if record.document_type == 'original' and record.request_id.state != 'draft' \
                    and ('file' in vals):
                raise UserError(
                    _('The original document cannot be replaced once the request '
                      'has left Draft.'))
        return super().write(vals)
