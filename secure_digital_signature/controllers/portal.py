import base64

from werkzeug.exceptions import NotFound

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request

ACTIVE_STATES = ('sent', 'viewed')


class SignatureController(http.Controller):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_signer_by_token(self, token):
        signer = request.env['digital.signature.request']._find_by_signer_token(token)
        if not signer:
            raise NotFound()
        return signer

    def _client_meta(self):
        ip = request.httprequest.headers.get('X-Forwarded-For', request.httprequest.remote_addr)
        ua = request.httprequest.headers.get('User-Agent', '')[:250]
        return ip, ua

    # ------------------------------------------------------------------
    # Signer flow (public, token-scoped - never by database id)
    # ------------------------------------------------------------------
    @http.route(['/sign/<string:token>'], type='http', auth='public', website=True, sitemap=False)
    def sign_landing(self, token, **kw):
        signer = self._get_signer_by_token(token)
        req = signer.request_id.sudo()
        ip, ua = self._client_meta()

        if not signer.token_revoked and signer.status in ACTIVE_STATES:
            req._signer_view(signer, ip_address=ip, user_agent=ua)

        return request.render('secure_digital_signature.portal_sign_page', {
            'signer': signer,
            'req': req,
            'can_sign': (not signer.token_revoked) and signer.status in ACTIVE_STATES,
            'fields': signer.field_ids,
        })

    @http.route(['/sign/<string:token>/submit'], type='http', auth='public',
                website=True, methods=['POST'], csrf=True, sitemap=False)
    def sign_submit(self, token, **post):
        signer = self._get_signer_by_token(token)
        req = signer.request_id.sudo()
        ip, ua = self._client_meta()

        if signer.token_revoked or signer.status not in ACTIVE_STATES:
            return request.redirect('/sign/%s' % token)

        for field in signer.field_ids:
            key = 'field_%d' % field.id
            if field.field_type in ('signature', 'initials', 'stamp'):
                data_url = post.get(key)
                if data_url and ',' in data_url:
                    header, encoded = data_url.split(',', 1)
                    field.sudo().write({'signature_image': encoded})
            elif field.field_type == 'checkbox':
                field.sudo().write({'value': 'True' if post.get(key) else 'False'})
            else:
                value = post.get(key)
                if value:
                    field.sudo().write({'value': value})
            req._log_event('field_filled', signer=signer, ip_address=ip, user_agent=ua)

        try:
            req._signer_sign(signer, ip_address=ip, user_agent=ua)
        except UserError as e:
            return request.render('secure_digital_signature.portal_sign_page', {
                'signer': signer, 'req': req,
                'can_sign': signer.status in ACTIVE_STATES and not signer.token_revoked,
                'fields': signer.field_ids,
                'error': str(e),
            })
        return request.redirect('/sign/%s' % token)

    @http.route(['/sign/<string:token>/reject'], type='http', auth='public',
                website=True, methods=['POST'], csrf=True, sitemap=False)
    def sign_reject(self, token, **post):
        signer = self._get_signer_by_token(token)
        req = signer.request_id.sudo()
        ip, ua = self._client_meta()
        try:
            req._signer_reject(signer, post.get('reason'), ip_address=ip, user_agent=ua)
        except UserError:
            pass
        return request.redirect('/sign/%s' % token)

    @http.route(['/sign/<string:token>/download/<string:doc_type>'], type='http',
                auth='public', sitemap=False)
    def sign_download(self, token, doc_type, **kw):
        signer = self._get_signer_by_token(token)
        req = signer.request_id.sudo()
        if doc_type == 'original':
            document = req.original_document()
        elif doc_type == 'final' and req.state == 'completed':
            document = req.final_document()
        else:
            raise NotFound()
        if not document:
            raise NotFound()
        content = base64.b64decode(document.file)
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', 'attachment; filename="%s"' % document.filename),
            ('Content-Length', len(content)),
        ]
        return request.make_response(content, headers)

    # ------------------------------------------------------------------
    # Public verification (no personal data exposed)
    # ------------------------------------------------------------------
    @http.route(['/sign/verify/<string:verification_token>'], type='http',
                auth='public', website=True, sitemap=False)
    def verify_document(self, verification_token, **kw):
        req = request.env['digital.signature.request'].sudo().search(
            [('verification_token', '=', verification_token)], limit=1)
        ip = self._client_meta()[0]

        if not req:
            request.env['digital.signature.verification'].sudo().create({
                'result': 'not_found', 'ip_address': ip,
            })
            return request.render('secure_digital_signature.portal_verify_page', {
                'found': False,
            })

        is_valid = req.state == 'completed' and bool(req.final_hash)
        request.env['digital.signature.verification'].sudo().create({
            'request_id': req.id,
            'result': 'valid' if is_valid else 'invalid',
            'ip_address': ip,
        })
        req._log_event('verified', ip_address=ip)

        return request.render('secure_digital_signature.portal_verify_page', {
            'found': True,
            'req': req,
            'is_valid': is_valid,
        })
