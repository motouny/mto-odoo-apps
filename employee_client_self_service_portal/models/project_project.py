from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    portal_manager_id = fields.Many2one(
        'res.users', string='Client Project Manager',
        help='Portal user, appointed by the client entity, who can review this '
             'project\'s employees, approve their time off requests, and relay '
             'requests on to the company. Independent from the Project Manager '
             'above, which requires an internal user.',
    )
    project_owner_id = fields.Many2one(
        'res.users', string='Project Owner (Client Entity)',
        help='Portal user representing the client entity/project owner. Sees '
             'the same team and statuses as the Client Project Manager, and can '
             'submit or approve requests depending on the request type\'s '
             'configured approver.',
    )
    attendance_latitude = fields.Float(
        string='Attendance Zone Latitude', digits=(10, 7),
        help='Site latitude employees assigned to this project must be near to '
             'check in/out from the employee portal. Leave empty to not restrict '
             'attendance by location for this project.')
    attendance_longitude = fields.Float(string='Attendance Zone Longitude', digits=(10, 7))
    attendance_radius = fields.Integer(
        string='Attendance Zone Radius (m)', default=200,
        help='Allowed distance, in meters, from the attendance zone coordinates.')
    employee_ids = fields.One2many(
        'hr.employee', 'project_id', string='Team Members',
        help='Employees reported under this project in the employee portal.')
    employee_count = fields.Integer(compute='_compute_employee_count')

    def _compute_employee_count(self):
        counts = self.env['hr.employee']._read_group(
            [('project_id', 'in', self.ids)], ['project_id'], ['__count'])
        counts_by_project = {project.id: count for project, count in counts}
        for project in self:
            project.employee_count = counts_by_project.get(project.id, 0)
