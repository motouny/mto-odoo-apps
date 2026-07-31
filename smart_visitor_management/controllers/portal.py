import base64

from werkzeug.exceptions import NotFound

from odoo import fields, http
from odoo.http import request

# States in which the invited guest is still allowed to complete / amend
# their own registration details through the public link.
EDITABLE_STATES = ('draft', 'pending_approval', 'approved', 'scheduled')


class VisitorPortalController(http.Controller):

    def _get_visit_by_token(self, token):
        """Look the visit up by its random invitation token only - never
        by database id, so the URL cannot be used to enumerate or guess
        other visitors' records (no IDOR)."""
        if not token:
            raise NotFound()
        visit = request.env['visitor.visit'].sudo().search(
            [('invitation_token', '=', token)], limit=1)
        if not visit:
            raise NotFound()
        return visit

    @http.route(['/visitor/invitation/<string:token>'], type='http',
                auth='public', website=True, sitemap=False)
    def visitor_invitation_form(self, token, **kw):
        visit = self._get_visit_by_token(token)
        expired = visit.state not in EDITABLE_STATES or (
            visit.visit_end and fields.Datetime.now() > visit.visit_end)
        return request.render('smart_visitor_management.portal_invitation_page', {
            'visit': visit,
            'guest': visit.guest_id,
            'expired': expired,
            'submitted': visit.invitation_completed,
        })

    @http.route(['/visitor/invitation/<string:token>/submit'], type='http',
                auth='public', website=True, methods=['POST'], csrf=True, sitemap=False)
    def visitor_invitation_submit(self, token, **post):
        visit = self._get_visit_by_token(token)
        if visit.state not in EDITABLE_STATES:
            return request.redirect('/visitor/invitation/%s' % token)
        if visit.visit_end and fields.Datetime.now() > visit.visit_end:
            return request.redirect('/visitor/invitation/%s' % token)

        guest_vals = {}
        for field_name in ('name', 'name_ar', 'identity_number', 'passport_number',
                            'company_name', 'mobile', 'email'):
            value = post.get(field_name)
            if value:
                guest_vals[field_name] = value.strip()
        if post.get('identity_type') in dict(
                request.env['visitor.guest']._fields['identity_type'].selection):
            guest_vals['identity_type'] = post.get('identity_type')
        if post.get('nationality_id'):
            guest_vals['nationality_id'] = int(post['nationality_id'])

        upload = request.httprequest.files.get('photo')
        if upload and upload.filename:
            guest_vals['photo'] = base64.b64encode(upload.read())

        if guest_vals:
            visit.sudo().guest_id.write(guest_vals)

        plate_number = (post.get('plate_number') or '').strip()
        if plate_number:
            existing_plate = visit.sudo().vehicle_ids.filtered(
                lambda v: v.plate_number == plate_number)
            if not existing_plate:
                request.env['visitor.vehicle'].sudo().create({
                    'visit_id': visit.id,
                    'plate_number': plate_number,
                    'color': (post.get('vehicle_color') or '').strip(),
                    'make_model': (post.get('vehicle_make_model') or '').strip(),
                })

        visit.sudo().write({'invitation_completed': True})
        if visit.state == 'draft':
            visit.sudo().action_submit()

        return request.redirect('/visitor/invitation/%s' % token)
