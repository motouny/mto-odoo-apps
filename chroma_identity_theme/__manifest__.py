{
    'name': 'Chroma Identity Theme - Full Brand Customization & Arabic RTL',
    'version': '18.0.1.0.0',
    # NOT 'Theme': Odoo's website module treats that category (and its
    # sub-categories) as a mutually-exclusive, explicitly-selected page
    # theme (Website > Configure > Theme) and silently excludes such
    # modules' assets from every website-scoped bundle unless picked as
    # website.theme_id. This module is a branding/accessibility overlay
    # meant to apply regardless of which page theme is active, so it must
    # not be categorized as one.
    'category': 'Website',
    'summary': 'Full brand identity customization for backend, portal and website - colors, fonts, layout, RTL/Arabic-ready',
    'description': """
Chroma Identity Theme - Full Brand Customization & Arabic RTL
===============================================================
A complete visual identity system for the backend, portal and (with the
companion `chroma_identity_theme_website` module) website/eCommerce - give
every customer their own colors, fonts and layout from Settings, with no
rebuild and no code, while staying fully usable in Arabic/RTL and any
other installed language out of the box.

Highlights
----------

* **Full identity control from Settings**: primary, accent and "chrome"
  (the dark navbar/sidebar frame) colors, heading/body/muted text colors,
  and a choice of 4 Arabic/Latin Google Fonts pairs - every screen updates
  instantly, no page rebuild needed, all changeable per company
* A live-preview Settings card so you can judge the exact look before
  saving - buttons, headings, body text and muted text all rendered with
  the pending colors and fonts
* One-click "Extract colors from logo" - detects a starting palette
  straight from the company logo, the same way Odoo's own Website
  Configurator does
* Right-to-left first: every screen (backend, portal, website) is designed
  and verified in Arabic/RTL, with English/LTR fully preserved - Odoo's
  own rtlcss pipeline mirrors the layout automatically, this theme only
  adds the visual layer on top
* A brand-new, from-scratch "app launcher" card grid for the backend -
  searchable, categorized, keyboard-navigable - replacing the plain apps
  dropdown with a dynamic, professional home screen that works on
  Community (no Enterprise Home Menu required), plus an optional
  persistent left app sidebar with its own Settings toggle
* A professional default color palette (WCAG 2.1 AA contrast checked
  against both light and dark text) - fully customizable per company, no
  single hardcoded look
* Accessibility layer: visible focus states, a skip-to-content link on
  portal/website pages, and a font-size adjuster control
* Portal (My Account, documents, chatter) restyled with the same design
  tokens

Install the separate `chroma_identity_theme_website` add-on (auto-installs
automatically once Website is installed) to extend the same design
tokens to the Website builder and eCommerce - it also includes an
optional Government / Public Sector header, footer and homepage-styling
pack for customers who need it, alongside the theme's own general-purpose
default homepage.

This app is fully independent - it does not require or depend on any
other paid application from this publisher.
""",
    'author': 'MTO',
    'website': 'https://mto-systems.com',
    'price': 49.0,
    'currency': 'EUR',
    'support': 'support@mto-systems.com',
    'images': ['static/description/banner.png'],
    'depends': ['web', 'portal', 'mail'],
    'data': [
        'views/layout_templates.xml',
        'views/res_config_settings_views.xml',
        'views/actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'chroma_identity_theme/static/src/scss/variables.scss',
            'chroma_identity_theme/static/src/scss/fonts.scss',
            'chroma_identity_theme/static/src/scss/accessibility.scss',
            'chroma_identity_theme/static/src/scss/backend.scss',
            'chroma_identity_theme/static/src/scss/app_launcher.scss',
            'chroma_identity_theme/static/src/scss/app_sidebar.scss',
            'chroma_identity_theme/static/src/scss/chroma_home_menu.scss',
            'chroma_identity_theme/static/src/scss/theme_preview.scss',
            'chroma_identity_theme/static/src/scss/settings_page.scss',
            'chroma_identity_theme/static/src/js/app_launcher/app_launcher.js',
            'chroma_identity_theme/static/src/js/app_launcher/app_launcher.xml',
            'chroma_identity_theme/static/src/js/app_launcher/app_sidebar.js',
            'chroma_identity_theme/static/src/js/app_launcher/app_sidebar.xml',
            'chroma_identity_theme/static/src/js/app_launcher/chroma_home_menu.js',
            'chroma_identity_theme/static/src/js/app_launcher/chroma_home_menu.xml',
            'chroma_identity_theme/static/src/js/color_picker_field.js',
            'chroma_identity_theme/static/src/js/color_picker_field.xml',
            'chroma_identity_theme/static/src/js/theme_preview_widget.js',
            'chroma_identity_theme/static/src/js/theme_preview_widget.xml',
        ],
        'web.assets_frontend': [
            'chroma_identity_theme/static/src/scss/variables.scss',
            'chroma_identity_theme/static/src/scss/fonts.scss',
            'chroma_identity_theme/static/src/scss/accessibility.scss',
            'chroma_identity_theme/static/src/scss/portal.scss',
            'chroma_identity_theme/static/src/js/accessibility/font_size_adjuster.js',
        ],
    },
    'installable': True,
    'application': True,
    'post_init_hook': 'post_init_hook',
    'license': 'OPL-1',
}
