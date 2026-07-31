{
    'name': 'DGA-Ready Theme - Website & eCommerce',
    'version': '18.0.1.3.0',
    # See sa_dga_theme/__manifest__.py for why this is not 'Theme'.
    'category': 'Website',
    'summary': 'Extends the DGA-Ready Theme to the Website builder and eCommerce - auto-installs with Website',
    'description': """
DGA-Ready Theme - Website & eCommerce
=========================================
Companion add-on to `sa_dga_theme` (auto-installs automatically once the
Website app is installed - no manual step needed). Registers the same
DGA-aligned color palette as a selectable preset in Website > Configure >
Theme, and polishes the header, footer and eCommerce cards/buttons to
match the backend and portal.

A "DGA Government" header and footer are added as new choices in
Website > Configure > Theme's own header/footer template pickers, and a
complete DGA-styled homepage (hero, quick e-services grid, animated
stats, news/announcements) replaces Odoo's blank default homepage on
install - all fully snippet-editable, none of it locked content. Arabic
is automatically added as a selectable website language on install (the
site's default language is left untouched).

This app is fully independent - it does not require or depend on any
other paid application from this publisher beyond its own `sa_dga_theme`
base.
""",
    'author': 'MTO',
    'website': 'https://www.mto-solutions.com',
    'price': 0.0,
    'currency': 'EUR',
    'support': 'support@mto-solutions.com',
    'depends': ['sa_dga_theme', 'website'],
    'data': [
        'views/website_header_footer_templates.xml',
        'views/website_header_footer_options.xml',
        'views/website_homepage_dga.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            (
                'after',
                'website/static/src/scss/primary_variables.scss',
                'sa_dga_theme_website/static/src/scss/primary_variables.scss',
            ),
        ],
        'web.assets_frontend': [
            'sa_dga_theme_website/static/src/scss/website.scss',
            'sa_dga_theme_website/static/src/scss/header_footer.scss',
            'sa_dga_theme_website/static/src/scss/homepage.scss',
            'sa_dga_theme_website/static/src/js/counter_widget.js',
        ],
    },
    'installable': True,
    'auto_install': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'license': 'OPL-1',
}
