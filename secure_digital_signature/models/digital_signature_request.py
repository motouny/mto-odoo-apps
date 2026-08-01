import base64
import secrets
from collections import defaultdict
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from . import pdf_engine

TOKEN_BYTES = 32


class DigitalSignatureRequest(models.Model):
    _name = 'digital.signature.request'
    _description = 'Signature Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda self: _('New'))
    subject = fields.Char(required=True, tracking=True)
    description = fields.Text()
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company, tracking=True)
    created_by_uid = fields.Many2one(
        'res.users', default=lambda self: self.env.user, readonly=True)

    signing_mode = fields.Selection([
        ('sequential', 'Sequential'),
        ('parallel', 'Parallel'),
    ], default='sequential', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('sent', 'Sent'),
        ('partially_signed', 'Partially Signed'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True, copy=False)

    expiration_date = fields.Datetime(
        default=lambda self: fields.Datetime.now() + timedelta(days=14), tracking=True)
    reminder_interval_days = fields.Integer(default=3)
    last_reminder_date = fields.Datetime(readonly=True, copy=False)

    document_ids = fields.One2many('digital.signature.document', 'request_id', string='Documents')
    signer_ids = fields.One2many('digital.signature.signer', 'request_id', string='Signers')

    original_file = fields.Binary(
        string='Original PDF', compute='_compute_original_file', inverse='_inverse_original_file')
    original_filename = fields.Char(
        compute='_compute_original_file', inverse='_inverse_original_file')

    original_hash = fields.Char(readonly=True, copy=False)
    final_hash = fields.Char(readonly=True, copy=False)
    completed_date = fields.Datetime(readonly=True, copy=False)

    verification_token = fields.Char(
        readonly=True, copy=False, default=lambda self: secrets.token_urlsafe(TOKEN_BYTES))

    event_ids = fields.One2many('digital.signature.event', 'request_id', string='Audit Trail')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'digital.signature.request') or _('New')
        records = super().create(vals_list)
        for record in records:
            record._log_event('created')
        return records

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _log_event(self, event_type, signer=False, note=False, ip_address=False, user_agent=False):
        self.env['digital.signature.event'].sudo().create({
            'request_id': self.id,
            'signer_id': signer.id if signer else False,
            'event_type': event_type,
            'note': note,
            'ip_address': ip_address,
            'user_agent': user_agent,
        })

    @api.depends('document_ids', 'document_ids.file', 'document_ids.filename')
    def _compute_original_file(self):
        for request in self:
            original = request.original_document()
            request.original_file = original.file if original else False
            request.original_filename = original.filename if original else False

    def _inverse_original_file(self):
        for request in self:
            if not request.original_file:
                continue
            original = request.original_document()
            vals = {
                'file': request.original_file,
                'filename': request.original_filename or 'document.pdf',
            }
            if original:
                original.write(vals)
            else:
                vals.update({'request_id': request.id, 'document_type': 'original'})
                self.env['digital.signature.document'].create(vals)

    def original_document(self):
        self.ensure_one()
        return self.document_ids.filtered(lambda d: d.document_type == 'original')[:1]

    def final_document(self):
        self.ensure_one()
        return self.document_ids.filtered(lambda d: d.document_type == 'final')[:1]

    def certificate_document(self):
        self.ensure_one()
        return self.document_ids.filtered(lambda d: d.document_type == 'certificate')[:1]

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_mark_ready(self):
        for request in self:
            if request.state != 'draft':
                raise UserError(_('Only draft requests can be marked ready.'))
            if not request.original_document():
                raise UserError(_('Upload the original PDF before continuing.'))
            if not request.signer_ids:
                raise UserError(_('Add at least one signer before continuing.'))
            for signer in request.signer_ids:
                if not signer.field_ids:
                    raise UserError(
                        _('Signer %s has no fields placed on the document.') % signer.name)
            request.state = 'ready'

    def action_send(self):
        for request in self:
            if request.state != 'ready':
                raise UserError(_('Only ready requests can be sent.'))
            request.state = 'sent'
            if request.signing_mode == 'sequential':
                first_signer = request.signer_ids.sorted('sequence')[:1]
                if first_signer:
                    request._activate_signer(first_signer)
            else:
                for signer in request.signer_ids:
                    request._activate_signer(signer)
            request._log_event('sent')

    def _activate_signer(self, signer):
        self.ensure_one()
        signer._generate_token()
        signer.write({'status': 'sent', 'sent_date': fields.Datetime.now()})
        self._log_event('sent', signer=signer)
        template = self.env.ref(
            'secure_digital_signature.mail_template_signature_invitation',
            raise_if_not_found=False)
        if template and signer.email:
            template.sudo().send_mail(signer.id, force_send=False)

    def action_resend(self):
        for request in self:
            pending = request.signer_ids.filtered(lambda s: s.status in ('sent', 'viewed'))
            for signer in pending:
                signer._generate_token()
                request._log_event('resent', signer=signer)
                template = self.env.ref(
                    'secure_digital_signature.mail_template_signature_invitation',
                    raise_if_not_found=False)
                if template and signer.email:
                    template.sudo().send_mail(signer.id, force_send=False)

    def action_cancel(self):
        for request in self:
            if request.state in ('completed', 'cancelled', 'rejected', 'expired'):
                raise UserError(_('This request can no longer be cancelled.'))
            request.signer_ids.filtered(lambda s: s.status not in ('signed', 'rejected'))._revoke_token()
            request.state = 'cancelled'
            request._log_event('cancelled')

    # ------------------------------------------------------------------
    # Signer-side actions (called from the public token-scoped controller)
    # ------------------------------------------------------------------
    @api.model
    def _find_by_signer_token(self, token):
        if not token:
            return self.env['digital.signature.signer']
        return self.env['digital.signature.signer'].sudo().search(
            [('token', '=', token)], limit=1)

    def _signer_view(self, signer, ip_address=False, user_agent=False):
        self.ensure_one()
        if signer.status == 'sent':
            signer.write({'status': 'viewed', 'viewed_date': fields.Datetime.now()})
        self._log_event('viewed', signer=signer, ip_address=ip_address, user_agent=user_agent)

    def _signer_sign(self, signer, ip_address=False, user_agent=False):
        self.ensure_one()
        if signer.token_revoked or signer.status not in ('sent', 'viewed'):
            raise UserError(_('This signing link is no longer valid.'))
        if signer.token_expiry and fields.Datetime.now() > signer.token_expiry:
            signer.status = 'expired'
            raise UserError(_('This signing link has expired.'))
        if not signer.all_required_fields_filled():
            raise UserError(_('Please complete all required fields before signing.'))

        signer.write({
            'status': 'signed',
            'signed_date': fields.Datetime.now(),
            'signed_ip': ip_address,
            'signed_user_agent': user_agent,
        })
        signer._revoke_token()
        self._log_event('signed', signer=signer, ip_address=ip_address, user_agent=user_agent)

        if self.signing_mode == 'sequential':
            remaining = self.signer_ids.filtered(lambda s: s.status == 'pending').sorted('sequence')
            if remaining:
                self._activate_signer(remaining[0])
                return
            if self.signer_ids.filtered(lambda s: s.status not in ('signed',)):
                # someone rejected/expired earlier in the chain - do not complete
                return
            self._complete_request()
        else:
            if all(s.status == 'signed' for s in self.signer_ids):
                self._complete_request()
            else:
                self.state = 'partially_signed'

    def _signer_reject(self, signer, reason, ip_address=False, user_agent=False):
        self.ensure_one()
        if signer.token_revoked or signer.status not in ('sent', 'viewed'):
            raise UserError(_('This signing link is no longer valid.'))
        signer.write({'status': 'rejected', 'rejection_reason': reason})
        signer._revoke_token()
        self._log_event('rejected', signer=signer, note=reason,
                         ip_address=ip_address, user_agent=user_agent)
        self.signer_ids.filtered(
            lambda s: s.id != signer.id and s.status not in ('signed', 'rejected'))._revoke_token()
        self.state = 'rejected'

    # ------------------------------------------------------------------
    # Completion / PDF generation
    # ------------------------------------------------------------------
    def _complete_request(self):
        self.ensure_one()
        original = self.original_document()
        if not original:
            raise UserError(_('No original document found.'))

        original_bytes = base64.b64decode(original.file)

        fields_by_page = defaultdict(list)
        for signer in self.signer_ids:
            for field in signer.field_ids:
                fields_by_page[field.page_number].append({
                    'pos_x': field.pos_x, 'pos_y': field.pos_y,
                    'width': field.width, 'height': field.height,
                    'field_type': field.field_type,
                    'value': field.value,
                    'signature_image': base64.b64decode(field.signature_image)
                    if field.signature_image else None,
                    'signer_label': signer.name,
                })

        final_bytes = pdf_engine.apply_fields_to_pdf(original_bytes, fields_by_page)
        final_hash = pdf_engine.sha256_hex(final_bytes)

        self.env['digital.signature.document'].sudo().create({
            'request_id': self.id,
            'document_type': 'final',
            'file': base64.b64encode(final_bytes),
            'filename': f'{self.name}-signed.pdf',
            'page_count': pdf_engine.get_page_count(final_bytes),
            'sha256_hash': final_hash,
        })

        verify_url = f"{self.get_base_url()}/sign/verify/{self.verification_token}"
        cert_bytes = pdf_engine.build_certificate_pdf(
            self.name, self.subject,
            [{
                'name': s.name, 'email': s.email,
                'signed_date': s.signed_date, 'signed_ip': s.signed_ip,
            } for s in self.signer_ids],
            self.original_hash, final_hash, verify_url,
        )
        self.env['digital.signature.document'].sudo().create({
            'request_id': self.id,
            'document_type': 'certificate',
            'file': base64.b64encode(cert_bytes),
            'filename': f'{self.name}-certificate.pdf',
            'page_count': 1,
        })

        self.write({
            'state': 'completed',
            'final_hash': final_hash,
            'completed_date': fields.Datetime.now(),
        })
        self._log_event('completed')

        template = self.env.ref(
            'secure_digital_signature.mail_template_signature_completed', raise_if_not_found=False)
        if template:
            for signer in self.signer_ids:
                if signer.email:
                    template.sudo().send_mail(self.id, force_send=False, email_values={
                        'email_to': signer.email,
                    })

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    @api.model
    def _cron_expire_requests(self):
        now = fields.Datetime.now()
        expired = self.search([
            ('state', 'in', ('sent', 'partially_signed')),
            ('expiration_date', '<', now),
        ])
        for request in expired:
            request.signer_ids.filtered(
                lambda s: s.status not in ('signed', 'rejected'))._revoke_token()
            request.state = 'expired'
            request._log_event('expired')

    @api.model
    def _cron_send_reminders(self):
        now = fields.Datetime.now()
        candidates = self.search([('state', 'in', ('sent', 'partially_signed'))])
        for request in candidates:
            if request.reminder_interval_days <= 0:
                continue
            due = (request.last_reminder_date or request.create_date) + timedelta(
                days=request.reminder_interval_days)
            if now < due:
                continue
            pending = request.signer_ids.filtered(lambda s: s.status in ('sent', 'viewed'))
            if not pending:
                continue
            template = self.env.ref(
                'secure_digital_signature.mail_template_signature_reminder',
                raise_if_not_found=False)
            for signer in pending:
                request._log_event('reminded', signer=signer)
                if template and signer.email:
                    template.sudo().send_mail(signer.id, force_send=False)
            request.last_reminder_date = now
