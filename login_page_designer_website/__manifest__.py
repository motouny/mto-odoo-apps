{
    'name': 'Login Page Designer - Website Compatibility',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Makes Login Page Designer work correctly once the Website app is installed (auto-installs, no manual step)',
    'description': """
Login Page Designer - Website Compatibility
==============================================
Companion add-on to `login_page_designer` (auto-installs automatically
once the Website app is installed - no manual step needed).

Why this exists
----------------
Once Website is installed, it takes over Odoo's `/web/login` page layout
to show the site's own header and footer instead of the plain standalone
login card - a change made entirely inside the `website` module, which
replaces the base login layout's content instead of extending it. This
add-on re-applies the same Login Page Designer position/colors/
background/welcome-text/Pro mode design directly on top of that
website-driven layout, so the designer keeps working exactly the same
way whether or not Website is installed.

This app is fully independent - it does not require or depend on any
other paid application from this publisher beyond its own
`login_page_designer` base.
""",
    'author': 'MTO',
    'website': 'https://mto-systems.com',
    'price': 0.0,
    'currency': 'EUR',
    'support': 'support@mto-systems.com',
    'images': ['static/description/banner.png'],
    'depends': ['login_page_designer', 'website'],
    'data': [
        'views/website_login_templates.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
    'license': 'OPL-1',
}
