from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BookingPricingRule(models.Model):
    _name = 'booking.pricing.rule'
    _description = 'Booking Pricing Rule'
    _order = 'priority desc, date_from'

    name = fields.Char(required=True, translate=True)
    resource_id = fields.Many2one('booking.resource', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='resource_id.currency_id', string='Currency')
    rule_type = fields.Selection([
        ('seasonal', 'Seasonal'),
        ('special_offer', 'Special Offer'),
    ], default='seasonal', required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    price = fields.Monetary(required=True)
    priority = fields.Integer(
        default=10,
        help='Higher priority rules win when several rules overlap the same date.',
    )
    active = fields.Boolean(default=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rule in self:
            if rule.date_from > rule.date_to:
                raise ValidationError(self.env._('The start date must be before or equal to the end date.'))
