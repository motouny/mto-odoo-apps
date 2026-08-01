from werkzeug.exceptions import NotFound

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

# Keys the Settings live-preview widget is allowed to stash in the
# session as an unsaved draft - anything else sent is dropped rather
# than stored, since this dict is later fed straight into
# _lpd_build_style_markup()/_lpd_build_html_markup() for rendering.
LPD_PREVIEW_KEYS = {
    'position', 'card_bg_color', 'card_text_color', 'button_color',
    'bg_type', 'bg_color', 'bg_gradient_start', 'bg_gradient_end',
    'bg_gradient_angle', 'bg_image_url', 'bg_overlay_opacity',
    'welcome_title', 'welcome_subtitle', 'pro_mode', 'custom_css',
    'custom_html',
}
LPD_MAX_TEXT_LEN = 50000


class LoginPageDesignerController(http.Controller):

    @http.route('/login_page_designer/background/<int:company_id>', type='http', auth='public')
    def lpd_background_image(self, company_id, **kwargs):
        company = request.env['res.company'].sudo().browse(company_id)
        if not company.exists() or not company.lpd_bg_image:
            raise NotFound()
        stream = request.env['ir.binary']._get_image_stream_from(
            company, field_name='lpd_bg_image')
        return stream.get_response()

    @http.route('/login_page_designer/set_preview', type='json', auth='user')
    def lpd_set_preview(self, config=None, **kwargs):
        if not request.env.user.has_group('base.group_system'):
            raise AccessError("Only Settings administrators can use the login page live preview.")
        config = config or {}
        if not isinstance(config, dict):
            return {'ok': False}
        clean = {}
        for key in LPD_PREVIEW_KEYS:
            if key not in config:
                continue
            value = config[key]
            if isinstance(value, str) and len(value) > LPD_MAX_TEXT_LEN:
                value = value[:LPD_MAX_TEXT_LEN]
            clean[key] = value
        request.session['login_page_designer_preview'] = clean
        return {'ok': True}

    @http.route('/login_page_designer/clear_preview', type='json', auth='user')
    def lpd_clear_preview(self, **kwargs):
        request.session.pop('login_page_designer_preview', None)
        return {'ok': True}
