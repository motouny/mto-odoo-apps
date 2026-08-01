from math import asin, cos, radians, sin, sqrt

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

EARTH_RADIUS_METERS = 6371000


def _haversine_meters(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in meters."""
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(a))


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    project_id = fields.Many2one(
        'project.project', string='Portal Project',
        help='Project this employee is reported under in the employee portal. '
             'The project\'s Portal Manager can see this employee\'s status and '
             'approve their time off requests from the portal.',
    )

    def _get_attendance_zones(self):
        """List of (latitude, longitude, radius) zones this employee may
        check in/out from: their project's site, and/or the company's."""
        self.ensure_one()
        zones = []
        project = self.project_id
        if project and project.attendance_latitude and project.attendance_longitude:
            zones.append((project.attendance_latitude, project.attendance_longitude, project.attendance_radius or 200))
        company = self.company_id
        if company.attendance_latitude and company.attendance_longitude:
            zones.append((company.attendance_latitude, company.attendance_longitude, company.attendance_radius or 200))
        return zones

    def _check_attendance_zone(self, latitude, longitude):
        """Raise if this employee is not allowed to check in/out from the
        given coordinates. No-op if no attendance zone is configured for
        their project or company (unrestricted by default)."""
        self.ensure_one()
        zones = self._get_attendance_zones()
        if not zones:
            return
        if not latitude or not longitude:
            raise UserError(_(
                "Location access is required to check in/out for this project. "
                "Please allow location access and try again."))
        for zone_lat, zone_lng, radius in zones:
            if _haversine_meters(latitude, longitude, zone_lat, zone_lng) <= radius:
                return
        raise UserError(_(
            "You must be on-site (within your project's or the company's location) "
            "to check in or out."))

    def action_grant_portal_access(self):
        self.ensure_one()
        if not self.work_contact_id:
            raise UserError(_("This employee has no related contact to grant portal access to."))
        return self.env['portal.wizard'].with_context(
            default_partner_ids=[self.work_contact_id.id],
        ).action_open_wizard()
