{
    'name': 'Generic Booking & Availability Engine',
    'version': '18.0.1.0.0',
    'category': 'Services',
    'summary': 'Bookable resources, date-based availability/capacity, seasonal pricing, cancellation policies and a full booking status workflow',
    'description': """
Generic Booking & Availability Engine
======================================
A domain-agnostic booking engine for anything that is sold or rented by the
day (or by a date range): hotel rooms, vehicles, tour guides, equipment
rental, clinic slots, event seats, meal plans - any bookable resource.

Highlights
----------
* Bookable resources organized by category, each with its own capacity,
  base price and cancellation policy
* Day-by-day availability calendar with per-date capacity and blackout dates
* Seasonal / special-offer pricing rules resolved by priority and date range
* Configurable cancellation policies (refund percentage by days-before-start)
* A full booking order workflow covering draft, pending payment, payment
  failed, paid, pending supplier confirmation, confirmed, rejected by
  supplier, cancelled by customer, cancelled by admin, refund requested,
  refunded, completed and no-show
* Automatic capacity guard - a booking cannot be confirmed past a
  resource's available capacity for the requested dates
* Automatic refund percentage calculation from the resource's cancellation
  policy when a customer requests cancellation
* Portal self-service: customers see their own bookings, download the
  booking voucher and request cancellation, without seeing anyone else's
  bookings
* Printable booking voucher (PDF)
* Bulk availability generator wizard to open a date range for a resource in
  one action
* Multi-company, and works standalone or alongside standard Sales/Invoicing
* Arabic and English, right-to-left ready

This app is fully independent - it does not require or depend on any other
paid application from this publisher.
""",
    'author': 'MTO',
    'website': 'https://www.mto-solutions.com',
    'price': 30.0,
    'currency': 'EUR',
    'support': 'support@mto-solutions.com',
    'images': ['static/description/banner.png'],
    'depends': ['base', 'mail', 'portal', 'product', 'sale'],
    'data': [
        'security/booking_security.xml',
        'security/ir.model.access.csv',
        'security/booking_record_rules.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'wizard/booking_availability_generator_views.xml',
        'views/booking_resource_category_views.xml',
        'views/booking_resource_views.xml',
        'views/booking_availability_views.xml',
        'views/booking_pricing_rule_views.xml',
        'views/booking_cancellation_policy_views.xml',
        'report/booking_voucher_templates.xml',
        'report/booking_voucher_report.xml',
        'views/booking_order_views.xml',
        'views/portal_templates.xml',
        'views/menus.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
