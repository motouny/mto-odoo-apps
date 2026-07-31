{
    'name': 'Secure Digital Signature Workflow',
    'version': '18.0.1.0.1',
    'category': 'Productivity/Documents',
    'summary': 'Send PDF documents for sequential or parallel electronic signing with a full audit trail',
    'description': """
Secure Digital Signature Workflow
===================================
Internal electronic signature workflow with an audit trail and document
verification. This app does not claim to be a government-certified or
legally-qualified electronic signature service - it is a self-hosted
document signing workflow you fully control.

Highlights
----------
* Upload a PDF, add internal, portal or fully external signers, place
  signature/initials/name/date/text/checkbox/selection fields anywhere on
  the document
* Sequential or parallel signing order, with per-request expiration and
  reminders
* Each signer gets a single-purpose, cryptographically random signing
  token (never the database record id), revoked the moment the request is
  rejected, cancelled or completed
* The final signed PDF is generated server-side (fields burned into the
  page) using the same PDF libraries Odoo core already depends on -
  no new external dependency
* SHA-256 hashing of both the original and the final document, with a
  public verification page and QR code that never exposes personal data
* A full, immutable audit trail: every view, field change, signature and
  rejection is timestamped with IP address and user agent
* Multi-company, English and Arabic

This app is fully independent - it does not require or depend on any
other paid application from this publisher.
""",
    'author': 'MTO',
    'website': 'https://mto-systems.com',
    'price': 30.0,
    'currency': 'EUR',
    'support': 'support@mto-solutions.com',
    'images': ['static/description/banner.png'],
    'depends': ['base', 'mail', 'portal', 'web'],
    'data': [
        'security/secure_digital_signature_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/digital_signature_request_views.xml',
        'views/digital_signature_template_views.xml',
        'views/digital_signature_event_views.xml',
        'views/portal_templates.xml',
        'views/menus.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'secure_digital_signature/static/src/js/signature_pad.js',
            'secure_digital_signature/static/src/scss/secure_digital_signature.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    'post_init_hook': 'post_init_hook',
}
