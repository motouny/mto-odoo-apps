{
    'name': 'Smart Visitor Management',
    'version': '18.0.1.0.2',
    'category': 'Administration',
    'summary': 'Visitor invitations, approvals, secure QR check-in, badges, vehicles, blacklist and live occupancy',
    'description': """
Smart Visitor Management
=========================
Manage visitor invitations, approvals, secure QR-based check-in and
check-out, printed visitor badges, vehicle permits, a blacklist and a
live occupancy view - entirely inside Odoo.

Highlights
----------
* Visit invitations with approval workflow (Draft -> Pending Approval ->
  Approved -> Checked In -> Checked Out)
* Cryptographically random, single-purpose QR tokens with expiry and
  automatic revocation on rejection / cancellation - the token is never
  the database record id
* Backend camera-based QR scanner (reuses Odoo's own barcode detection
  widget, no third-party scanning library) with manual fallback entry
  for the security desk
* Public, token-protected self-registration page so an invited guest can
  complete their own details without any Odoo account and without ever
  being able to see another visit
* Vehicle permits, blacklist screening on check-in, and a full
  checkpoint scan audit log (immutable - success and failure both
  recorded)
* Printable visitor badge and vehicle permit reports
* Multi-company and multi-location, with dedicated security groups for
  Receptionist, Security Officer, Host, Visitor Manager and Auditor
* Arabic and English, right-to-left ready

This app is fully independent - it does not require or depend on any
other paid application from this publisher.
""",
    'author': 'MTO',
    'website': 'https://www.mto-solutions.com',
    'price': 30.0,
    'currency': 'EUR',
    'support': 'support@mto-solutions.com',
    'images': ['static/description/banner.png'],
    'depends': ['base', 'mail', 'portal', 'web'],
    'data': [
        'security/smart_visitor_management_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/visitor_visit_views.xml',
        'views/visitor_guest_views.xml',
        'views/visitor_location_views.xml',
        'views/visitor_gate_views.xml',
        'views/visitor_host_views.xml',
        'views/visitor_blacklist_views.xml',
        'views/visitor_checkpoint_log_views.xml',
        'views/visitor_badge_template_views.xml',
        'views/visitor_kiosk_views.xml',
        'views/res_config_settings_views.xml',
        'views/portal_templates.xml',
        'views/menus.xml',
        'report/visitor_badge_report_templates.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'smart_visitor_management/static/src/js/kiosk_scanner.js',
            'smart_visitor_management/static/src/xml/kiosk_scanner.xml',
            'smart_visitor_management/static/src/scss/smart_visitor_management.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
