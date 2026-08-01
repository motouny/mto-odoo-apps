{
    'name': 'Login Page Designer - Professional Login Customization',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Give every company its own branded /web/login page - position, colors, background, welcome text and a Pro mode for custom HTML/CSS',
    'description': """
Login Page Designer - Professional Login Customization
========================================================
Turn Odoo's plain login screen into a branded first impression, per
company, with no code required - and a Pro mode for teams who want to
add their own HTML/CSS on top.

Highlights
----------

* **Live preview while you design**: a real iframe of the actual login
  page updates instantly as you change settings, before you save anything
* **Position control**: place the login card center, left, right, top or
  bottom of the screen
* **Card styling**: card background color, text color and button/link
  color
* **Background**: solid color, two-color gradient (with angle), or a
  custom uploaded image, with an optional dark overlay for legible text
* **Welcome text**: an optional custom title and subtitle shown above the
  login form, translatable per installed language
* **Pro mode**: for advanced users - inject custom CSS and an extra HTML
  panel directly into the login page, on top of the same base template
  (not a full replacement), gated to Settings administrators only
* Fully independent - works standalone, no dependency on any other paid
  app from this publisher, multi-company ready

This app is fully independent - it does not require or depend on any
other paid application from this publisher.
""",
    'author': 'MTO',
    'website': 'https://mto-systems.com',
    'price': 30.0,
    'currency': 'EUR',
    'support': 'support@mto-systems.com',
    'images': ['static/description/banner.png'],
    'depends': ['web'],
    'data': [
        'views/login_templates.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'login_page_designer/static/src/scss/login_page_designer_frontend.scss',
        ],
        'web.assets_backend': [
            'login_page_designer/static/src/scss/login_page_designer_backend.scss',
            'login_page_designer/static/src/js/login_preview/login_preview_widget.js',
            'login_page_designer/static/src/js/login_preview/login_preview_widget.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
