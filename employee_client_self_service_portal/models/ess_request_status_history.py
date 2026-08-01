from odoo import _, fields, models
from odoo.exceptions import AccessError


class EssRequestStatusHistory(models.Model):
    _name = 'ess.request.status.history'
    _description = 'Request Status History'
    _order = 'create_date desc'

    request_id = fields.Many2one('ess.request', required=True, ondelete='cascade', index=True)
    from_state = fields.Char()
    to_state = fields.Char(required=True)
    changed_by_uid = fields.Many2one('res.users', readonly=True)
    change_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    note = fields.Char()
    company_id = fields.Many2one(related='request_id.company_id', store=True)

    def write(self, vals):
        if not self.env.su:
            raise AccessError(_('The request status history is immutable.'))
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise AccessError(_('The request status history is immutable.'))
        return super().unlink()
