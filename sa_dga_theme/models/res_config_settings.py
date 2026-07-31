from odoo import _, fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # The preset -> primary/accent sync is handled client-side (see
    # DgaPresetRadioField in static/src/js/color_picker_field.js) rather
    # than via a server onchange - a related Selection field edited on this
    # transient wizard turned out not to reliably trigger a server
    # onchange round-trip in testing, so no @api.onchange is declared here.
    sa_dga_color_preset = fields.Selection(
        related='company_id.sa_dga_color_preset', readonly=False)
    sa_dga_primary_color = fields.Char(
        related='company_id.sa_dga_primary_color', readonly=False)
    sa_dga_accent_color = fields.Char(
        related='company_id.sa_dga_accent_color', readonly=False)
    sa_dga_chrome_color = fields.Char(
        related='company_id.sa_dga_chrome_color', readonly=False)

    sa_dga_font_pair = fields.Selection(
        related='company_id.sa_dga_font_pair', readonly=False)

    sa_dga_heading_color = fields.Char(
        related='company_id.sa_dga_heading_color', readonly=False)
    sa_dga_body_color = fields.Char(
        related='company_id.sa_dga_body_color', readonly=False)
    sa_dga_muted_color = fields.Char(
        related='company_id.sa_dga_muted_color', readonly=False)

    sa_dga_sidebar_enabled = fields.Boolean(
        related='company_id.sa_dga_sidebar_enabled', readonly=False)

    def action_sa_dga_extract_logo_colors(self):
        """Reuse Odoo core's own logo-color-extraction (the same method
        the website Configurator calls when you upload a logo there) so
        a company's existing res.company.logo drives the DGA palette
        instead of picking colors blind."""
        self.ensure_one()
        if not self.company_id.logo:
            raise UserError(_(
                "Upload a company logo first (Settings > General Settings "
                "> Companies), then try again."))
        primary, accent = self.env['base.document.layout']\
            .extract_image_primary_secondary_colors(self.company_id.logo)
        if not primary:
            raise UserError(_(
                "Couldn't detect colors in this logo - it may be too "
                "light or fully transparent. Try a different image, or "
                "set the colors manually below."))
        self.sa_dga_color_preset = 'custom'
        self.sa_dga_primary_color = primary
        self.sa_dga_accent_color = accent or primary
