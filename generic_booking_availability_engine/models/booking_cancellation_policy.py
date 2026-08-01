from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BookingCancellationPolicy(models.Model):
    _name = 'booking.cancellation.policy'
    _description = 'Booking Cancellation Policy'

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    line_ids = fields.One2many(
        'booking.cancellation.policy.line', 'policy_id', string='Refund Rules', copy=True,
    )
    resource_ids = fields.One2many('booking.resource', 'cancellation_policy_id', string='Resources')

    def compute_refund_percentage(self, days_before_start):
        """Return the refund percentage (0-100) for a cancellation made
        `days_before_start` full days before the booking's start date,
        picking the most specific (smallest days_before_start threshold
        still satisfied) matching rule."""
        self.ensure_one()
        applicable = self.line_ids.filtered(lambda line: days_before_start >= line.days_before_start)
        if not applicable:
            return 0.0
        best = max(applicable, key=lambda line: line.days_before_start)
        return best.refund_percentage


class BookingCancellationPolicyLine(models.Model):
    _name = 'booking.cancellation.policy.line'
    _description = 'Booking Cancellation Policy Line'
    _order = 'days_before_start desc'

    policy_id = fields.Many2one(
        'booking.cancellation.policy', required=True, ondelete='cascade',
    )
    days_before_start = fields.Integer(
        string='Days Before Start', required=True,
        help='Minimum number of full days before the booking start date for this refund rate to apply.',
    )
    refund_percentage = fields.Float(string='Refund %', required=True)

    @api.constrains('refund_percentage')
    def _check_refund_percentage(self):
        for line in self:
            if not (0.0 <= line.refund_percentage <= 100.0):
                raise ValidationError(self.env._('Refund percentage must be between 0 and 100.'))

    @api.constrains('days_before_start')
    def _check_days_before_start(self):
        for line in self:
            if line.days_before_start < 0:
                raise ValidationError(self.env._('Days before start cannot be negative.'))
