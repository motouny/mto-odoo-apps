{
    'name': 'Saudi Government Fixed Asset Management (MOF Compliant)',
    'version': '18.0.1.1.0',
    'category': 'Accounting/Localizations',
    'summary': 'Asset classification, MOF coding, capitalization threshold, depreciation, tagging and physical verification for Saudi government entities',
    'description': """
Saudi Government Fixed Asset Management
========================================
Implements the Saudi Ministry of Finance's "الدليل الشامل لحصر وتقييم
الأصول للجهات الحكومية" (Comprehensive Guide for Inventory and Valuation of
Government Entity Assets) inside Odoo.

Highlights
----------
* Official MOF asset classification hierarchy (31 main groups, 173
  sub-groups, hundreds of specific asset types) pre-loaded with every
  8-digit classification code
* Automatic مرسملة/غير مرسملة (capitalized / non-capitalized) determination
  based on each asset type's official capitalization threshold - assets
  below threshold are still coded and tracked in a control register, per
  the guide, without being depreciated
* Full MOF asset code generation (classification code + accounting
  classification + sequence, e.g. 10020201-0001)
* Straight-line depreciation schedule bounded by each classification's
  official useful-life range
* Physical tagging with QR or Code128 barcodes (Odoo's own barcode route,
  no third-party library), plus an RFID Tag ID field, following the guide's
  movability/safety tagging decision logic
* Physical verification (جرد) campaigns with discrepancy tracking
  (lost/damaged/stolen) and responsible-employee follow-up, including a
  Quick Scan screen for fast barcode/QR/RFID-based counts (works with any
  handheld scanner or RFID reader in keyboard-wedge/HID mode)
* Asset register, classification & coding sheet, and physical count QWeb
  reports
* Multi-company, Arabic and English, right-to-left ready

This app is fully independent - it does not require or depend on any other
paid application from this publisher, and does not depend on Odoo
Enterprise's Assets module (it ships its own, so it installs cleanly on
Community).
""",
    'author': 'MTO',
    'website': 'https://www.mto-solutions.com',
    'price': 30.0,
    'currency': 'EUR',
    'support': 'support@mto-solutions.com',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/sa_gov_fixed_assets_security.xml',
        'security/ir.model.access.csv',
        'data/sa.gov.asset.classification.csv',
        'data/ir_sequence_data.xml',
        'views/sa_gov_asset_classification_views.xml',
        'views/sa_gov_asset_views.xml',
        'views/sa_gov_asset_tag_views.xml',
        'wizard/sa_gov_asset_verification_wizard_views.xml',
        'views/sa_gov_asset_verification_views.xml',
        'views/res_config_settings_views.xml',
        'views/menus.xml',
        'report/sa_gov_asset_reports.xml',
        'report/sa_gov_asset_report_templates.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
