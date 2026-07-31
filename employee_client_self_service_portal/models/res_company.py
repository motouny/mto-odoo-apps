from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    attendance_latitude = fields.Float(
        string='Attendance Zone Latitude', digits=(10, 7),
        help='Fallback site latitude for employee portal check in/out when the '
             "employee's project has no attendance zone of its own. Leave empty "
             'to not restrict attendance by location at the company level.')
    attendance_longitude = fields.Float(string='Attendance Zone Longitude', digits=(10, 7))
    attendance_radius = fields.Integer(
        string='Attendance Zone Radius (m)', default=200,
        help='Allowed distance, in meters, from the attendance zone coordinates.')
