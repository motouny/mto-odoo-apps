from odoo import fields, models


class BookingResourceCategory(models.Model):
    _name = 'booking.resource.category'
    _description = 'Booking Resource Category'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    note = fields.Text()
    active = fields.Boolean(default=True)
    resource_ids = fields.One2many('booking.resource', 'category_id', string='Resources')
    resource_count = fields.Integer(compute='_compute_resource_count')

    def _compute_resource_count(self):
        counts = self.env['booking.resource']._read_group(
            [('category_id', 'in', self.ids)], ['category_id'], ['__count'],
        )
        mapped = {category.id: count for category, count in counts}
        for category in self:
            category.resource_count = mapped.get(category.id, 0)
