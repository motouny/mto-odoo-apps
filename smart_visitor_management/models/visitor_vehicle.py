from odoo import fields, models


class VisitorVehicle(models.Model):
    _name = 'visitor.vehicle'
    _description = 'Visitor Vehicle'

    visit_id = fields.Many2one('visitor.visit', required=True, ondelete='cascade')
    plate_number = fields.Char(required=True)
    vehicle_type = fields.Selection([
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
        ('truck', 'Truck'),
        ('other', 'Other'),
    ], default='car', required=True)
    color = fields.Char()
    make_model = fields.Char(string='Make / Model')
    notes = fields.Char()
    company_id = fields.Many2one(related='visit_id.company_id', store=True)
