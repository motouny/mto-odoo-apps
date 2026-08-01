from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BookingAvailability(models.Model):
    _name = 'booking.availability'
    _description = 'Booking Resource Availability'
    _order = 'date'

    resource_id = fields.Many2one('booking.resource', required=True, ondelete='cascade')
    date = fields.Date(required=True)
    capacity_total = fields.Integer(
        required=True,
        help='Capacity for this specific date, overriding the resource default capacity.',
    )
    is_blackout = fields.Boolean(
        string='Blackout Date', default=False,
        help='When set, no booking can be made against this resource on this date regardless of capacity.',
    )
    note = fields.Char()
    capacity_booked = fields.Integer(compute='_compute_capacity_booked')
    capacity_remaining = fields.Integer(compute='_compute_capacity_booked')
    display_name = fields.Char(compute='_compute_display_name')

    _sql_constraints = [
        ('resource_date_uniq', 'UNIQUE(resource_id, date)',
         'Only one availability record is allowed per resource and per date.'),
        ('capacity_total_non_negative', 'CHECK(capacity_total >= 0)',
         'Capacity cannot be negative.'),
    ]

    @api.depends('resource_id.name', 'date')
    def _compute_display_name(self):
        for availability in self:
            availability.display_name = f'{availability.resource_id.name} - {availability.date}'

    @api.depends('resource_id', 'date', 'capacity_total', 'is_blackout')
    def _compute_capacity_booked(self):
        for availability in self:
            booked = self.env['booking.order.line']._booked_quantity(
                availability.resource_id.id, availability.date,
            )
            availability.capacity_booked = booked
            availability.capacity_remaining = 0 if availability.is_blackout else max(
                availability.capacity_total - booked, 0,
            )

    @api.constrains('capacity_total')
    def _check_capacity_total(self):
        for availability in self:
            if availability.capacity_total < 0:
                raise ValidationError(self.env._('Capacity cannot be negative.'))
