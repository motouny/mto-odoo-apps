from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BookingResource(models.Model):
    _name = 'booking.resource'
    _description = 'Booking Resource'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True, tracking=True)
    code = fields.Char(copy=False)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    category_id = fields.Many2one('booking.resource.category', string='Category', tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    description = fields.Html(translate=True)
    image_1920 = fields.Image()

    capacity = fields.Integer(
        default=1, required=True, tracking=True,
        help='Maximum number of concurrent bookings this resource can accept on any given date.',
    )
    unit_price = fields.Monetary(
        string='Base Price', required=True, default=0.0,
        help='Fallback price used when no pricing rule matches the requested date.',
    )
    min_advance_booking_hours = fields.Integer(
        string='Minimum Advance Booking (Hours)', default=0,
        help='A booking cannot start earlier than this many hours from now.',
    )
    max_quantity_per_booking = fields.Integer(
        string='Max Quantity per Booking', default=0,
        help='0 means no per-booking limit (still bounded by remaining capacity).',
    )

    product_id = fields.Many2one(
        'product.product', string='Linked Product',
        help='Optional: link this resource to a product to reuse standard Odoo pricelists, taxes and invoicing.',
    )
    responsible_partner_id = fields.Many2one(
        'res.partner', string='Managed By',
        help='Optional owner/supplier of this resource (vendor, guide, agency...).',
    )
    cancellation_policy_id = fields.Many2one('booking.cancellation.policy', string='Cancellation Policy')

    is_published = fields.Boolean(string='Bookable', default=True, tracking=True)

    availability_ids = fields.One2many('booking.availability', 'resource_id', string='Availability')
    pricing_rule_ids = fields.One2many('booking.pricing.rule', 'resource_id', string='Pricing Rules')
    order_line_ids = fields.One2many('booking.order.line', 'resource_id', string='Booking Lines')

    _sql_constraints = [
        ('capacity_positive', 'CHECK(capacity > 0)', 'Capacity must be strictly positive.'),
    ]

    @api.constrains('max_quantity_per_booking')
    def _check_max_quantity_per_booking(self):
        for resource in self:
            if resource.max_quantity_per_booking < 0:
                raise ValidationError(self.env._('Max quantity per booking cannot be negative.'))

    def price_for_date(self, date):
        """Resolve the applicable price for this resource on `date`,
        preferring the highest-priority matching pricing rule and falling
        back to the resource's base price."""
        self.ensure_one()
        rule = self.env['booking.pricing.rule'].search([
            ('resource_id', '=', self.id),
            ('date_from', '<=', date),
            ('date_to', '>=', date),
        ], order='priority desc, id desc', limit=1)
        return rule.price if rule else self.unit_price

    def available_capacity_for_date(self, date):
        """Remaining bookable capacity for this resource on `date`,
        accounting for any blackout override and already-booked quantity."""
        self.ensure_one()
        availability = self.env['booking.availability'].search([
            ('resource_id', '=', self.id), ('date', '=', date),
        ], limit=1)
        if availability:
            if availability.is_blackout:
                return 0
            total = availability.capacity_total
        else:
            total = self.capacity
        booked = self.env['booking.order.line']._booked_quantity(self.id, date)
        return max(total - booked, 0)
