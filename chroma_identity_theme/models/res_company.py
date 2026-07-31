from markupsafe import Markup

from odoo import api, fields, models

# Professional, WCAG 2.1 AA contrast-checked starting palettes - fully
# overridable per company from Settings > General Settings > Chroma Identity.
# 'mto_signature' (purple/black) is the theme's own default brand
# identity - explicitly requested to replace Saudi Green as the
# out-of-the-box look, while keeping the other presets selectable.
# 'gov_navy' is a color scheme only, not tied to the optional Government/
# Public Sector content pack (see chroma_identity_theme_website) - any
# preset can be paired with any header/footer/homepage content.
CHROMA_COLOR_PRESETS = {
    'mto_signature': {'primary': '#5E4766', 'accent': '#010101', 'chrome': '#0A0A0A'},
    'saudi_green': {'primary': '#046A38', 'accent': '#0B7A45', 'chrome': '#0A2E1C'},
    'gov_navy': {'primary': '#0B3D59', 'accent': '#12608C', 'chrome': '#081E2E'},
}

# Curated Arabic/Latin font pairs, all Google Fonts (open license, no extra
# runtime dependency). IBM Plex Sans Arabic is the default for its broad
# Arabic Unicode coverage and clean, professional look - also the pairing
# used in Saudi digital-government component libraries, a strong public
# reference point for Arabic UI typography.
CHROMA_FONT_PAIRS = {
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

CHROMA_DEFAULT_TEXT_COLORS = {
    'heading': '#111827',
    'body': '#1F2937',
    'muted': '#6B7280',
}


class ResCompany(models.Model):
    _inherit = 'res.company'

    chroma_color_preset = fields.Selection(
        [
            ('mto_signature', 'MTO Signature (Purple/Black)'),
            ('saudi_green', 'Saudi Green'),
            ('gov_navy', 'Government Navy'),
            ('custom', 'Custom'),
        ],
        string='Theme Color Preset', default='mto_signature', required=True)
    chroma_primary_color = fields.Char(
        # 'Primary Color'/'Accent Color' collide with base's own unrelated
        # res.company.primary_color/secondary_color (report-layout branding,
        # see odoo/addons/base/models/res_company.py) - same visible label,
        # different fields; "Brand ..." disambiguates them in field lists.
        string='Brand Primary Color', default='#5E4766')
    chroma_accent_color = fields.Char(
        string='Brand Accent Color', default='#010101')
    chroma_chrome_color = fields.Char(
        string='Chrome Color', default='#0A0A0A',
        help='Background of the backend navbar, the app sidebar (if '
             'shown) and their card-launcher dropdowns - the dark '
             '"frame" around the app, separate from the primary/accent '
             'brand colors.')

    chroma_font_pair = fields.Selection(
        [(key, val['label']) for key, val in CHROMA_FONT_PAIRS.items()],
        string='Font Pair', default='ibm_plex', required=True)

    chroma_heading_color = fields.Char(
        string='Heading Color', default=CHROMA_DEFAULT_TEXT_COLORS['heading'])
    chroma_body_color = fields.Char(
        string='Body Text Color', default=CHROMA_DEFAULT_TEXT_COLORS['body'])
    chroma_muted_color = fields.Char(
        string='Muted Text Color', default=CHROMA_DEFAULT_TEXT_COLORS['muted'])

    chroma_sidebar_enabled = fields.Boolean(
        string='Show Backend App Sidebar', default=True,
        help='Persistent left icon rail for switching between apps. '
             'Turn off to use the standard top-navbar app dropdown only.')

    @api.onchange('chroma_color_preset')
    def _onchange_chroma_color_preset(self):
        preset = CHROMA_COLOR_PRESETS.get(self.chroma_color_preset)
        if preset:
            self.chroma_primary_color = preset['primary']
            self.chroma_accent_color = preset['accent']
            self.chroma_chrome_color = preset['chrome']

    def _chroma_readable_text_color(self, hex_color):
        """Pick black or white text for readable contrast on hex_color."""
        try:
            hex_color = (hex_color or '').lstrip('#')
            r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return '#FFFFFF'
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return '#1A1A1A' if luminance > 0.6 else '#FFFFFF'

    def _chroma_rgb_triplet(self, hex_color):
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

    def _chroma_font_pair_values(self):
        """Returns {'arabic': Markup, 'latin': Markup, ...} - the values
        deliberately contain literal double quotes (CSS font-family
        syntax, e.g. '"IBM Plex Sans Arabic"'), so they're wrapped in
        Markup here and consumed via t-out (not t-esc) in
        views/layout_templates.xml. Safe: these are trusted constants
        from CHROMA_FONT_PAIRS above, never user input."""
        self.ensure_one()
        pair = CHROMA_FONT_PAIRS.get(self.chroma_font_pair) or CHROMA_FONT_PAIRS['ibm_plex']
        return {
            **pair,
            'arabic': Markup(pair['arabic']),
            'latin': Markup(pair['latin']),
        }
