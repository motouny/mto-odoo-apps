from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class BookingAvailabilityGenerator(models.TransientModel):
    _name = 'booking.availability.generator'
    _description = 'Bulk Availability Generator'

    resource_id = fields.Many2one('booking.resource', required=True)
    date_from = fields.Date(required=True, default=fields.Date.context_today)
    date_to = fields.Date(required=True, default=fields.Date.context_today)
    capacity_total = fields.Integer(required=True)
    overwrite_existing = fields.Boolean(
        default=False,
        help='If set, existing availability records in the range are updated instead of skipped.',
    )

    @api.onchange('resource_id')
    def _onchange_resource_id(self):
        if self.resource_id:
            self.capacity_total = self.resource_id.capacity

    def action_generate(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(self.env._('The start date must be before or equal to the end date.'))

        Availability = self.env['booking.availability']
        existing = Availability.search([
            ('resource_id', '=', self.resource_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ])
        existing_by_date = {rec.date: rec for rec in existing}

        current = self.date_from
        to_create = []
        while current <= self.date_to:
            record = existing_by_date.get(current)
            if record:
                if self.overwrite_existing:
                    record.capacity_total = self.capacity_total
            else:
                to_create.append({
                    'resource_id': self.resource_id.id,
                    'date': current,
                    'capacity_total': self.capacity_total,
                })
            current += timedelta(days=1)

        if to_create:
            Availability.create(to_create)
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Availability'),
            'res_model': 'booking.availability',
            'view_mode': 'list,form',
            'domain': [('resource_id', '=', self.resource_id.id),
                       ('date', '>=', self.date_from), ('date', '<=', self.date_to)],
            'context': {'default_resource_id': self.resource_id.id},
        }
