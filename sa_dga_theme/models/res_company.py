from markupsafe import Markup

from odoo import api, fields, models

# Professional, WCAG 2.1 AA contrast-checked starting palettes. Not an
# extraction from DGA's restricted internal brand guideline - fully
# overridable per company from Settings > General Settings > DGA Theme.
# 'mto_signature' (purple/black) is the theme's own default brand
# identity - explicitly requested to replace Saudi Green as the
# out-of-the-box look, while keeping the other presets selectable.
DGA_COLOR_PRESETS = {
    'mto_signature': {'primary': '#5E4766', 'accent': '#010101', 'chrome': '#0A0A0A'},
    'saudi_green': {'primary': '#046A38', 'accent': '#0B7A45', 'chrome': '#0A2E1C'},
    'gov_navy': {'primary': '#0B3D59', 'accent': '#12608C', 'chrome': '#081E2E'},
}

# Curated Arabic/Latin font pairs, all Google Fonts (open license, no extra
# runtime dependency). IBM Plex Sans Arabic is the default because it
# matches the pairing used in Saudi DGA's public component library: see
# [[project sa_dga_theme]] research notes in __manifest__.py.
DGA_FONT_PAIRS = {
    'ibm_plex': {
        'label': 'IBM Plex Sans Arabic',
        'arabic': '"IBM Plex Sans Arabic"',
        'latin': '"IBM Plex Sans"',
        'google_families': 'IBM+Plex+Sans+Arabic:400,500,600,700|IBM+Plex+Sans:400,500,600,700',
    },
    'cairo': {
        'label': 'Cairo',
        'arabic': '"Cairo"',
        'latin': '"Cairo"',
        'google_families': 'Cairo:400,500,600,700',
    },
    'tajawal': {
        'label': 'Tajawal',
        'arabic': '"Tajawal"',
        'latin': '"Tajawal"',
        'google_families': 'Tajawal:400,500,700',
    },
    'noto_kufi': {
        'label': 'Noto Kufi Arabic',
        'arabic': '"Noto Kufi Arabic"',
        'latin': '"IBM Plex Sans"',
        'google_families': 'Noto+Kufi+Arabic:400,500,600,700|IBM+Plex+Sans:400,500,600,700',
    },
}

DGA_DEFAULT_TEXT_COLORS = {
    'heading': '#111827',
    'body': '#1F2937',
    'muted': '#6B7280',
}


class ResCompany(models.Model):
    _inherit = 'res.company'

    sa_dga_color_preset = fields.Selection(
        [
            ('mto_signature', 'MTO Signature (Purple/Black)'),
            ('saudi_green', 'Saudi Green'),
            ('gov_navy', 'Government Navy'),
            ('custom', 'Custom'),
        ],
        string='Theme Color Preset', default='mto_signature', required=True)
    sa_dga_primary_color = fields.Char(
        string='DGA Primary Color', default='#5E4766')
    sa_dga_accent_color = fields.Char(
        string='DGA Accent Color', default='#010101')
    sa_dga_chrome_color = fields.Char(
        string='DGA Chrome Color', default='#0A0A0A',
        help='Background of the backend navbar, the app sidebar (if '
             'shown) and their card-launcher dropdowns - the dark '
             '"frame" around the app, separate from the primary/accent '
             'brand colors.')

    sa_dga_font_pair = fields.Selection(
        [(key, val['label']) for key, val in DGA_FONT_PAIRS.items()],
        string='DGA Font', default='ibm_plex', required=True)

    sa_dga_heading_color = fields.Char(
        string='DGA Heading Color', default=DGA_DEFAULT_TEXT_COLORS['heading'])
    sa_dga_body_color = fields.Char(
        string='DGA Body Text Color', default=DGA_DEFAULT_TEXT_COLORS['body'])
    sa_dga_muted_color = fields.Char(
        string='DGA Muted Text Color', default=DGA_DEFAULT_TEXT_COLORS['muted'])

    sa_dga_sidebar_enabled = fields.Boolean(
        string='Show Backend App Sidebar', default=True,
        help='Persistent left icon rail for switching between apps. '
             'Turn off to use the standard top-navbar app dropdown only.')

    @api.onchange('sa_dga_color_preset')
    def _onchange_sa_dga_color_preset(self):
        preset = DGA_COLOR_PRESETS.get(self.sa_dga_color_preset)
        if preset:
            self.sa_dga_primary_color = preset['primary']
            self.sa_dga_accent_color = preset['accent']
            self.sa_dga_chrome_color = preset['chrome']

    def _sa_dga_readable_text_color(self, hex_color):
        """Pick black or white text for readable contrast on hex_color."""
        try:
            hex_color = (hex_color or '').lstrip('#')
            r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return '#FFFFFF'
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return '#1A1A1A' if luminance > 0.6 else '#FFFFFF'

    def _sa_dga_rgb_triplet(self, hex_color):
        """'#5E4766' -> '94, 71, 102' - lets CSS build rgba() (focus
        rings, hover tints) from the runtime primary/accent color, since
        a CSS custom property alone can't be decomposed into its R/G/B
        channels in plain CSS."""
        try:
            hex_color = (hex_color or '').lstrip('#')
            r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return '0, 0, 0'
        return f'{r}, {g}, {b}'

    def _sa_dga_font_pair_values(self):
        """Returns {'arabic': Markup, 'latin': Markup, ...} - the values
        deliberately contain literal double quotes (CSS font-family
        syntax, e.g. '"IBM Plex Sans Arabic"'), so they're wrapped in
        Markup here and consumed via t-out (not t-esc) in
        views/layout_templates.xml. Safe: these are trusted constants
        from DGA_FONT_PAIRS above, never user input."""
        self.ensure_one()
        pair = DGA_FONT_PAIRS.get(self.sa_dga_font_pair) or DGA_FONT_PAIRS['ibm_plex']
        return {
            **pair,
            'arabic': Markup(pair['arabic']),
            'latin': Markup(pair['latin']),
        }
