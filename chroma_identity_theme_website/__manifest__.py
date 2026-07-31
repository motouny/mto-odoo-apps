{
    'name': 'Chroma Identity Theme - Website & eCommerce',
    'version': '18.0.1.0.0',
    # See chroma_identity_theme/__manifest__.py for why this is not 'Theme'.
    'category': 'Website',
    'summary': 'Extends the Chroma Identity Theme to the Website builder and eCommerce - auto-installs with Website',
    'description': """
Chroma Identity Theme - Website & eCommerce
================================================
Companion add-on to `chroma_identity_theme` (auto-installs automatically once
the Website app is installed - no manual step needed). Registers the same
customizable color palette as a selectable preset in Website > Configure >
Theme, and polishes the header, footer and eCommerce cards/buttons to
match the backend and portal.

A real, industry-neutral homepage (hero, services grid, animated stats,
news/announcements) replaces Odoo's blank default homepage on install -
fully snippet-editable, none of it locked content. Arabic is automatically
added as a selectable website language on install (the site's default
language is left untouched).

For public-sector customers, an optional "Government / Public Sector"
header and footer pack is available as an extra choice in Website >
Configure > Theme's own header/footer template pickers - opt-in, not
applied by default.

This app is fully independent - it does not require or depend on any
other paid application from this publisher beyond its own
`chroma_identity_theme` base.
""",
    'author': 'MTO',
    'website': 'https://mto-systems.com',
    'price': 0.0,
    'currency': 'EUR',
    'support': 'support@mto-solutions.com',
    'images': ['static/description/banner.png'],
    'depends': ['chroma_identity_theme', 'website'],
    'data': [
        'views/website_header_footer_templates.xml',
        'views/website_header_footer_options.xml',
        'views/website_homepage_default.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            (
                'after',
                'website/static/src/scss/primary_variables.scss',
                'chroma_identity_theme_website/static/src/scss/primary_variables.scss',
            ),
        ],
        'web.assets_frontend': [
            'chroma_identity_theme_website/static/src/scss/website.scss',
            'chroma_identity_theme_website/static/src/scss/header_footer.scss',
            'chroma_identity_theme_website/static/src/scss/homepage.scss',
            'chroma_identity_theme_website/static/src/js/counter_widget.js',
        ],
    },
    'installable': True,
    'auto_install': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'license': 'OPL-1',
}
