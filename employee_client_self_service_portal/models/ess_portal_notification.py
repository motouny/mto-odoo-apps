from odoo import fields, models


class EssPortalNotification(models.Model):
    _name = 'ess.portal.notification'
    _description = 'Portal Notification'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', required=True, index=True)
    title = fields.Char(required=True)
    body = fields.Text()
    request_id = fields.Many2one('ess.request', ondelete='cascade')
    is_read = fields.Boolean(default=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
