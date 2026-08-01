from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lpd_enabled = fields.Boolean(related='company_id.lpd_enabled', readonly=False)
    lpd_position = fields.Selection(related='company_id.lpd_position', readonly=False)

    lpd_card_bg_color = fields.Char(related='company_id.lpd_card_bg_color', readonly=False)
    lpd_card_text_color = fields.Char(related='company_id.lpd_card_text_color', readonly=False)
    lpd_button_color = fields.Char(related='company_id.lpd_button_color', readonly=False)

    lpd_bg_type = fields.Selection(related='company_id.lpd_bg_type', readonly=False)
    lpd_bg_color = fields.Char(related='company_id.lpd_bg_color', readonly=False)
    lpd_bg_gradient_start = fields.Char(related='company_id.lpd_bg_gradient_start', readonly=False)
    lpd_bg_gradient_end = fields.Char(related='company_id.lpd_bg_gradient_end', readonly=False)
    lpd_bg_gradient_angle = fields.Integer(related='company_id.lpd_bg_gradient_angle', readonly=False)
    lpd_bg_image = fields.Binary(related='company_id.lpd_bg_image', readonly=False)
    lpd_bg_image_filename = fields.Char(related='company_id.lpd_bg_image_filename', readonly=False)
    lpd_bg_overlay_opacity = fields.Float(related='company_id.lpd_bg_overlay_opacity', readonly=False)

    lpd_welcome_title = fields.Char(related='company_id.lpd_welcome_title', readonly=False)
    lpd_welcome_subtitle = fields.Char(related='company_id.lpd_welcome_subtitle', readonly=False)

    lpd_pro_mode = fields.Boolean(related='company_id.lpd_pro_mode', readonly=False)
    lpd_custom_css = fields.Text(related='company_id.lpd_custom_css', readonly=False)
    lpd_custom_html = fields.Text(related='company_id.lpd_custom_html', readonly=False)
