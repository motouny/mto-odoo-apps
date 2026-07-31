from odoo import _, fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # The preset -> primary/accent sync is handled client-side (see
    # ChromaPresetRadioField in static/src/js/color_picker_field.js) rather
    # than via a server onchange - a related Selection field edited on this
    # transient wizard turned out not to reliably trigger a server
    # onchange round-trip in testing, so no @api.onchange is declared here.
    chroma_color_preset = fields.Selection(
        related='company_id.chroma_color_preset', readonly=False)
    chroma_primary_color = fields.Char(
        related='company_id.chroma_primary_color', readonly=False)
    chroma_accent_color = fields.Char(
        related='company_id.chroma_accent_color', readonly=False)
    chroma_chrome_color = fields.Char(
        related='company_id.chroma_chrome_color', readonly=False)

    chroma_font_pair = fields.Selection(
        related='company_id.chroma_font_pair', readonly=False)

    chroma_heading_color = fields.Char(
        related='company_id.chroma_heading_color', readonly=False)
    chroma_body_color = fields.Char(
        related='company_id.chroma_body_color', readonly=False)
    chroma_muted_color = fields.Char(
        related='company_id.chroma_muted_color', readonly=False)

    chroma_sidebar_enabled = fields.Boolean(
        related='company_id.chroma_sidebar_enabled', readonly=False)

    def action_chroma_extract_logo_colors(self):
        """Reuse Odoo core's own logo-color-extraction (the same method
        the website Configurator calls when you upload a logo there) so
        a company's existing res.company.logo drives the palette
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
        self.chroma_color_preset = 'custom'
        self.chroma_primary_color = primary
        self.chroma_accent_color = accent or primary
