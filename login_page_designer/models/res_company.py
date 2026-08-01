from markupsafe import Markup

from odoo import SUPERUSER_ID, api, fields, models
from odoo.http import request


class ResCompany(models.Model):
    _inherit = 'res.company'

    lpd_enabled = fields.Boolean(
        string='Enable Login Page Designer', default=False,
        help="Turn on to apply this company's custom login page design. "
             "Leave off to keep Odoo's default login page untouched.")

    lpd_position = fields.Selection(
        [('center', 'Center'), ('left', 'Left'), ('right', 'Right'),
         ('top', 'Top'), ('bottom', 'Bottom')],
        string='Login Card Position', default='center', required=True)

    lpd_card_bg_color = fields.Char(string='Card Background Color', default='#FFFFFF')
    lpd_card_text_color = fields.Char(string='Card Text Color', default='#1F2937')
    lpd_button_color = fields.Char(string='Button / Link Color', default='#714B67')

    lpd_bg_type = fields.Selection(
        [('none', 'Default'), ('color', 'Solid Color'),
         ('gradient', 'Gradient'), ('image', 'Image')],
        string='Page Background', default='none', required=True)
    lpd_bg_color = fields.Char(string='Background Color', default='#F1F0F2')
    lpd_bg_gradient_start = fields.Char(string='Gradient Start Color', default='#5E4766')
    lpd_bg_gradient_end = fields.Char(string='Gradient End Color', default='#0A0A0A')
    lpd_bg_gradient_angle = fields.Integer(string='Gradient Angle', default=135)
    lpd_bg_image = fields.Binary(string='Login Page Background Image', attachment=True)
    lpd_bg_image_filename = fields.Char(string='Background Image Filename')
    lpd_bg_overlay_opacity = fields.Float(string='Dark Overlay Opacity', default=0.0)

    lpd_welcome_title = fields.Char(string='Welcome Title', translate=True)
    lpd_welcome_subtitle = fields.Char(string='Welcome Subtitle', translate=True)

    lpd_pro_mode = fields.Boolean(string='Enable Pro Mode', default=False)
    lpd_custom_css = fields.Text(string='Custom CSS')
    lpd_custom_html = fields.Text(string='Custom HTML Panel')

    @api.model
    def _lpd_get_login_render_company(self):
        """Resolve which company's login-page config to render for the
        current anonymous /web/login request - mirrors the same uid
        fallback web/controllers/binary.py's company_logo route uses
        (session uid, or the superuser as a last resort), so branding
        stays consistent with the logo that's already shown on the same
        page."""
        uid = (request.session.uid if request else None) or SUPERUSER_ID
        return self.env['res.users'].sudo().browse(uid).company_id

    def _lpd_get_render_config(self):
        """Return this company's login-page config as a plain dict, or
        False if the designer is off - the same shape the JS live-preview
        widget sends for an unsaved draft (see set_preview controller),
        so both real requests and preview requests share one renderer."""
        self.ensure_one()
        if not self.lpd_enabled:
            return False
        return {
            'position': self.lpd_position or 'center',
            'card_bg_color': self.lpd_card_bg_color or '#FFFFFF',
            'card_text_color': self.lpd_card_text_color or '#1F2937',
            'button_color': self.lpd_button_color or '#714B67',
            'bg_type': self.lpd_bg_type or 'none',
            'bg_color': self.lpd_bg_color or '#F1F0F2',
            'bg_gradient_start': self.lpd_bg_gradient_start or '#5E4766',
            'bg_gradient_end': self.lpd_bg_gradient_end or '#0A0A0A',
            'bg_gradient_angle': self.lpd_bg_gradient_angle or 0,
            'bg_image_url': (
                '/login_page_designer/background/%s' % self.id
                if self.lpd_bg_type == 'image' and self.lpd_bg_image else False),
            'bg_overlay_opacity': self.lpd_bg_overlay_opacity or 0.0,
            'welcome_title': self.lpd_welcome_title or '',
            'welcome_subtitle': self.lpd_welcome_subtitle or '',
            'pro_mode': self.lpd_pro_mode,
            'custom_css': self.lpd_custom_css if self.lpd_pro_mode else '',
            'custom_html': self.lpd_custom_html if self.lpd_pro_mode else '',
        }

    def _lpd_build_style_markup(self, cfg):
        """Compile a config dict (from _lpd_get_render_config or a
        session preview payload) into a single <style> body. Returns a
        markupsafe.Markup so the QWeb template can use t-out without
        HTML-escaping the CSS (t-esc would mangle quoted values)."""
        position = cfg.get('position') or 'center'
        justify = {'center': 'center', 'left': 'flex-start', 'right': 'flex-end',
                   'top': 'center', 'bottom': 'center'}.get(position, 'center')
        align = {'center': 'center', 'left': 'center', 'right': 'center',
                  'top': 'flex-start', 'bottom': 'flex-end'}.get(position, 'center')

        bg_type = cfg.get('bg_type') or 'none'
        overlay = max(0.0, min(0.9, float(cfg.get('bg_overlay_opacity') or 0.0)))
        background_decl = ''
        if bg_type == 'color':
            background_decl = 'background-color: %s;' % (cfg.get('bg_color') or '#F1F0F2')
        elif bg_type == 'gradient':
            background_decl = (
                'background-image: linear-gradient(%sdeg, %s, %s);' % (
                    cfg.get('bg_gradient_angle') or 0,
                    cfg.get('bg_gradient_start') or '#5E4766',
                    cfg.get('bg_gradient_end') or '#0A0A0A'))
        elif bg_type == 'image' and cfg.get('bg_image_url'):
            background_decl = (
                'background-image: linear-gradient(rgba(0,0,0,%s), rgba(0,0,0,%s)), '
                'url("%s"); background-size: cover; background-position: center; '
                'background-repeat: no-repeat;' % (overlay, overlay, cfg['bg_image_url']))

        css = """
body.o_lpd_login_page { %(background_decl)s }
body.o_lpd_login_page #wrapwrap { min-height: 100vh; display: flex; flex-direction: column; }
body.o_lpd_login_page #wrapwrap main { flex: 1 1 auto; display: flex; justify-content: %(justify)s; align-items: %(align)s; }
body.o_lpd_login_page .container.py-5 { margin: 0 !important; padding-top: 24px; padding-bottom: 24px; flex: 0 0 auto; }
body.o_lpd_login_page .o_lpd_card { background-color: %(card_bg_color)s !important; color: %(card_text_color)s !important; }
body.o_lpd_login_page .o_lpd_card label,
body.o_lpd_login_page .o_lpd_card .form-label { color: %(card_text_color)s; }
body.o_lpd_login_page .o_lpd_card .btn-primary { background-color: %(button_color)s !important; border-color: %(button_color)s !important; }
body.o_lpd_login_page .o_lpd_card a { color: %(button_color)s; }
""" % {
            'background_decl': background_decl,
            'justify': justify,
            'align': align,
            'card_bg_color': cfg.get('card_bg_color') or '#FFFFFF',
            'card_text_color': cfg.get('card_text_color') or '#1F2937',
            'button_color': cfg.get('button_color') or '#714B67',
        }
        if cfg.get('pro_mode') and cfg.get('custom_css'):
            css += '\n' + cfg['custom_css']
        return Markup(css)

    def _lpd_build_html_markup(self, cfg):
        if cfg.get('pro_mode') and cfg.get('custom_html'):
            return Markup(cfg['custom_html'])
        return Markup('')
