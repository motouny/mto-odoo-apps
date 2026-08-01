from odoo import api, fields, models


class EssRequestComment(models.Model):
    _name = 'ess.request.comment'
    _description = 'Request Comment'
    _order = 'create_date asc'

    request_id = fields.Many2one('ess.request', required=True, ondelete='cascade', index=True)
    author_user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, readonly=True)
    body = fields.Text(required=True)
    is_internal = fields.Boolean(
        default=False, help='Internal notes are never shown to the requester in the portal.')
    company_id = fields.Many2one(related='request_id.company_id', store=True)
    chatter_message_id = fields.Many2one(
        'mail.message', readonly=True, copy=False,
        help='The chatter message this comment was mirrored to, so staff watching the '
             "record's chatter see it without having to open the Comments tab.")

    @api.model_create_multi
    def create(self, vals_list):
        comments = super().create(vals_list)
        for comment in comments:
            if not comment.is_internal:
                message = comment.request_id.sudo().message_post(
                    body=comment.body,
                    author_id=comment.author_user_id.partner_id.id,
                    subtype_xmlid='mail.mt_comment',
                )
                comment.chatter_message_id = message.id
        return comments
