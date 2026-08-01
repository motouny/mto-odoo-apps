from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Order states that actually hold/occupy resource capacity for their dates.
OCCUPYING_STATES = ('paid', 'pending_supplier_confirmation', 'confirmed', 'completed')


class BookingOrderLine(models.Model):
    _name = 'booking.order.line'
    _description = 'Booking Order Line'

    order_id = fields.Many2one('booking.order', required=True, ondelete='cascade')
    order_state = fields.Selection(related='order_id.state', string='Order Status', store=True)
    partner_id = fields.Many2one(related='order_id.partner_id', store=True)
    resource_id = fields.Many2one('booking.resource', required=True)
    category_id = fields.Many2one(related='resource_id.category_id', string='Category', store=True)
    currency_id = fields.Many2one(related='order_id.currency_id', string='Currency')
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    nights = fields.Integer(compute='_compute_nights', store=True)
    quantity = fields.Integer(default=1, required=True)
    unit_price = fields.Monetary(required=True)
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True)

    _sql_constraints = [
        ('quantity_positive', 'CHECK(quantity > 0)', 'Quantity must be strictly positive.'),
        ('dates_consistent', 'CHECK(date_to >= date_from)', 'The end date must be on or after the start date.'),
    ]

    @api.depends('date_from', 'date_to')
    def _compute_nights(self):
        for line in self:
            if line.date_from and line.date_to:
                line.nights = max((line.date_to - line.date_from).days + 1, 1)
            else:
                line.nights = 1

    @api.depends('quantity', 'unit_price', 'nights')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price * line.nights

    @api.onchange('resource_id', 'date_from')
    def _onchange_resource_id(self):
        for line in self:
            if line.resource_id:
                if not line.date_to or (line.date_from and line.date_to < line.date_from):
                    line.date_to = line.date_from
                if line.date_from:
                    line.unit_price = line.resource_id.price_for_date(line.date_from)
                else:
                    line.unit_price = line.resource_id.unit_price

    @api.constrains('resource_id', 'quantity')
    def _check_max_quantity(self):
        for line in self:
            max_qty = line.resource_id.max_quantity_per_booking
            if max_qty and line.quantity > max_qty:
                raise ValidationError(self.env._(
                    '%(resource)s allows a maximum of %(max)s per booking (requested %(qty)s).',
                    resource=line.resource_id.name, max=max_qty, qty=line.quantity,
                ))

    @api.model
    def _booked_quantity(self, resource_id, date, exclude_order_ids=()):
        """Sum of quantities already occupying `resource_id`'s capacity on
        `date` across all lines whose order is in an OCCUPYING_STATE."""
        domain = [
            ('resource_id', '=', resource_id),
            ('date_from', '<=', date),
            ('date_to', '>=', date),
            ('order_id.state', 'in', OCCUPYING_STATES),
        ]
        if exclude_order_ids:
            domain.append(('order_id', 'not in', list(exclude_order_ids)))
        lines = self.search(domain)
        return sum(lines.mapped('quantity'))

    def check_availability(self, exclude_order_ids=()):
        """Raise if any of these lines would exceed remaining capacity on
        any date in their range, excluding their own order(s) from the
        current occupancy count (used when re-confirming an existing order)."""
        for line in self:
            resource = line.resource_id
            current = line.date_from
            while current <= line.date_to:
                availability = self.env['booking.availability'].search([
                    ('resource_id', '=', resource.id), ('date', '=', current),
                ], limit=1)
                if availability and availability.is_blackout:
                    raise ValidationError(self.env._(
                        '%(resource)s is not bookable on %(date)s (blackout date).',
                        resource=resource.name, date=current,
                    ))
                total = availability.capacity_total if availability else resource.capacity
                booked = self._booked_quantity(resource.id, current, exclude_order_ids=exclude_order_ids)
                if booked + line.quantity > total:
                    raise ValidationError(self.env._(
                        'Not enough availability for %(resource)s on %(date)s: '
                        '%(remaining)s remaining, %(requested)s requested.',
                        resource=resource.name, date=current,
                        remaining=max(total - booked, 0), requested=line.quantity,
                    ))
                current = current + timedelta(days=1)
