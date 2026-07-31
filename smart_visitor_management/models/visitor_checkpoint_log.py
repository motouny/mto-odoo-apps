from odoo import _, fields, models
from odoo.exceptions import AccessError


class VisitorCheckpointLog(models.Model):
    _name = 'visitor.checkpoint.log'
    _description = 'Visitor Checkpoint Scan Log'
    _order = 'scan_datetime desc'
    _log_access = True

    visit_id = fields.Many2one('visitor.visit', ondelete='cascade', index=True)
    guest_name = fields.Char(help='Snapshot of the guest name at scan time.')
    gate_id = fields.Many2one('visitor.gate', ondelete='set null')
    company_id = fields.Many2one('res.company', required=True)
    scan_type = fields.Selection([
        ('check_in', 'Check-In'),
        ('check_out', 'Check-Out'),
    ], required=True)
    scan_result = fields.Selection([
        ('success', 'Success'),
        ('invalid_token', 'Invalid Token'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked / Not Approved'),
        ('outside_window', 'Outside Allowed Window'),
        ('blacklisted', 'Blacklisted'),
        ('wrong_state', 'Wrong State'),
    ], required=True)
    scan_datetime = fields.Datetime(required=True, default=fields.Datetime.now)
    scanned_by_uid = fields.Many2one('res.users', string='Scanned By')
    note = fields.Char()

    def write(self, vals):
        if not self.env.su:
            raise AccessError(_('Checkpoint scan logs are immutable and cannot be modified.'))
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise AccessError(_('Checkpoint scan logs are immutable and cannot be deleted.'))
        return super().unlink()
