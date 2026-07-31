{
    'name': 'DGA-Ready Theme - Arabic RTL for Government & Enterprise',
    'version': '18.0.1.8.0',
    # NOT 'Theme': Odoo's website module treats that category (and its
    # sub-categories) as a mutually-exclusive, explicitly-selected page
    # theme (Website > Configure > Theme) and silently excludes such
    # modules' assets from every website-scoped bundle unless picked as
    # website.theme_id. This module is a branding/accessibility overlay
    # meant to apply regardless of which page theme is active, so it must
    # not be categorized as one.
    'category': 'Website',
    'summary': 'Arabic-first RTL theme for backend, portal and website - DGA-aligned typography, colors and accessibility',
    'description': """
DGA-Ready Theme - Arabic RTL for Government & Enterprise
===========================================================
A complete visual overhaul of the backend, portal and (with the companion
`sa_dga_theme_website` module) website/eCommerce, purpose-built for
Saudi Arabia's Digital Government Authority (DGA) digital service
expectations while remaining fully usable in English and any other
installed language.

Highlights
----------

* Right-to-left first: every screen (backend, portal, website) is designed
  and verified in Arabic/RTL, with English/LTR fully preserved - Odoo's
  own rtlcss pipeline mirrors the layout automatically, this theme only
  adds the visual layer on top
* Arabic typography aligned with the Saudi Design System's public
  guidance: IBM Plex Sans Arabic for Arabic text, IBM Plex Sans for Latin
  text, applied by language rather than forced globally so every other
  language keeps its native font
* A brand-new, from-scratch "app launcher" card grid for the backend -
  searchable, categorized, keyboard-navigable - replacing the plain apps
  dropdown with a dynamic, professional home screen that works on
  Community (no Enterprise Home Menu required)
* A full Settings > DGA Theme screen with a live preview card: color
  presets (or custom hex), a choice of 4 Arabic/Latin Google Fonts pairs,
  and separate heading/body/muted text color pickers - so you can judge
  the exact look before saving, all applied instantly, no rebuild needed
* A Government-appropriate default color palette (WCAG 2.1 AA contrast
  checked against both light and dark text) - fully customizable per
  company, no single hardcoded look
* Accessibility layer: visible focus states, a skip-to-content link on
  portal/website pages, and a font-size adjuster control, following the
  accessibility patterns published on Saudi government digital service
  guidelines
* Portal (My Account, documents, chatter) restyled with the same design
  tokens

Honesty note: colors follow a professional, WCAG-AA-checked palette
inspired by Saudi national identity and public Saudi Design System
guidance (IBM Plex Sans Arabic, WCAG 2.1 AA, RTL-first). This app does
not claim official DGA certification, since DGA's exact internal brand
color values are published in a restricted guideline document this
package cannot verify against - the palette is fully customizable from
Settings for teams that hold the official guideline.

Install the separate `sa_dga_theme_website` add-on (auto-installs
automatically once Website is installed) to extend the same design
tokens to the Website builder and eCommerce.

This app is fully independent - it does not require or depend on any
other paid application from this publisher.
""",
    'author': 'MTO',
    'website': 'https://www.mto-solutions.com',
    'price': 49.0,
    'currency': 'EUR',
    'support': 'support@mto-solutions.com',
    # 'images' key intentionally omitted until static/description/banner.png
    # is designed - a missing-but-referenced image is worse than no key.
    'depends': ['web', 'portal', 'mail'],
    'data': [
        'views/layout_templates.xml',
        'views/res_config_settings_views.xml',
        'views/actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sa_dga_theme/static/src/scss/variables.scss',
            'sa_dga_theme/static/src/scss/fonts.scss',
            'sa_dga_theme/static/src/scss/accessibility.scss',
            'sa_dga_theme/static/src/scss/backend.scss',
            'sa_dga_theme/static/src/scss/app_launcher.scss',
            'sa_dga_theme/static/src/scss/app_sidebar.scss',
            'sa_dga_theme/static/src/scss/dga_home_menu.scss',
            'sa_dga_theme/static/src/scss/theme_preview.scss',
            'sa_dga_theme/static/src/js/app_launcher/app_launcher.js',
            'sa_dga_theme/static/src/js/app_launcher/app_launcher.xml',
            'sa_dga_theme/static/src/js/app_launcher/app_sidebar.js',
            'sa_dga_theme/static/src/js/app_launcher/app_sidebar.xml',
            'sa_dga_theme/static/src/js/app_launcher/dga_home_menu.js',
            'sa_dga_theme/static/src/js/app_launcher/dga_home_menu.xml',
            'sa_dga_theme/static/src/js/color_picker_field.js',
            'sa_dga_theme/static/src/js/color_picker_field.xml',
            'sa_dga_theme/static/src/js/theme_preview_widget.js',
            'sa_dga_theme/static/src/js/theme_preview_widget.xml',
        ],
        'web.assets_frontend': [
            'sa_dga_theme/static/src/scss/variables.scss',
            'sa_dga_theme/static/src/scss/fonts.scss',
            'sa_dga_theme/static/src/scss/accessibility.scss',
            'sa_dga_theme/static/src/scss/portal.scss',
            'sa_dga_theme/static/src/js/accessibility/font_size_adjuster.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
