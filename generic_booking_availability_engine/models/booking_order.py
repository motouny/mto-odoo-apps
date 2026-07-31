from datetime import date

from odoo import api, fields, models
from odoo.exceptions import UserError

STATES = [
    ('draft', 'Draft'),
    ('pending_payment', 'Pending Payment'),
    ('payment_failed', 'Payment Failed'),
    ('paid', 'Paid'),
    ('pending_supplier_confirmation', 'Pending Supplier Confirmation'),
    ('confirmed', 'Confirmed'),
    ('rejected_by_supplier', 'Rejected by Supplier'),
    ('cancelled_by_customer', 'Cancelled by Customer'),
    ('cancelled_by_admin', 'Cancelled by Admin'),
    ('refund_requested', 'Refund Requested'),
    ('refunded', 'Refunded'),
    ('completed', 'Completed'),
    ('no_show', 'No-show'),
]

CANCELLABLE_STATES = ('pending_payment', 'paid', 'pending_supplier_confirmation', 'confirmed')
ADMIN_CANCELLABLE_STATES = (
    'draft', 'pending_payment', 'payment_failed', 'paid',
    'pending_supplier_confirmation', 'confirmed',
)


class BookingOrder(models.Model):
    _name = 'booking.order'
    _description = 'Booking Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_order desc, id desc'

    name = fields.Char(default='/', copy=False, readonly=True)
    partner_id = fields.Many2one('res.partner', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Booked By', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    date_order = fields.Datetime(default=fields.Datetime.now, required=True)
    state = fields.Selection(STATES, default='draft', required=True, tracking=True, copy=False)

    line_ids = fields.One2many('booking.order.line', 'order_id', string='Booking Lines', copy=True)
    amount_total = fields.Monetary(compute='_compute_amount_total', store=True)

    sale_order_id = fields.Many2one(
        'sale.order', string='Related Sales Order', copy=False,
        help='Optional: link to a Sales Order to reuse standard invoicing.',
    )
    note = fields.Text()
    rejection_reason = fields.Text(copy=False)
    cancellation_reason = fields.Text(copy=False)
    cancelled_date = fields.Datetime(copy=False)
    refund_percentage = fields.Float(copy=False, readonly=True)
    refund_amount = fields.Monetary(compute='_compute_refund_amount', store=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name, company_id)', 'Booking order reference must be unique per company.'),
    ]

    @api.depends('line_ids.subtotal')
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = sum(order.line_ids.mapped('subtotal'))

    @api.depends('amount_total', 'refund_percentage')
    def _compute_refund_amount(self):
        for order in self:
            order.refund_amount = order.amount_total * (order.refund_percentage / 100.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('booking.order') or '/'
        return super().create(vals_list)

    def _compute_cancellation_refund_percentage(self):
        """Weighted refund percentage across all lines, based on each
        line's resource cancellation policy and days remaining until its
        start date. Lines whose resource has no policy refund 0%."""
        self.ensure_one()
        if not self.amount_total:
            return 0.0
        today = date.today()
        weighted_refund = 0.0
        for line in self.line_ids:
            policy = line.resource_id.cancellation_policy_id
            if not policy:
                continue
            days_before_start = (line.date_from - today).days
            pct = policy.compute_refund_percentage(days_before_start)
            weighted_refund += line.subtotal * (pct / 100.0)
        return (weighted_refund / self.amount_total) * 100.0

    def action_request_payment(self):
        for order in self:
            if order.state != 'draft':
                raise UserError(self.env._('Only draft bookings can be sent to payment.'))
            if not order.line_ids:
                raise UserError(self.env._('Add at least one booking line before requesting payment.'))
        self.write({'state': 'pending_payment'})

    def action_mark_paid(self):
        for order in self:
            if order.state not in ('pending_payment', 'payment_failed'):
                raise UserError(self.env._('Only bookings pending payment can be marked as paid.'))
            order.line_ids.check_availability(exclude_order_ids=order.ids)
        self.write({'state': 'paid'})

    def action_mark_payment_failed(self):
        for order in self:
            if order.state != 'pending_payment':
                raise UserError(self.env._('Only bookings pending payment can fail payment.'))
        self.write({'state': 'payment_failed'})

    def action_send_to_supplier(self):
        for order in self:
            if order.state != 'paid':
                raise UserError(self.env._('Only paid bookings can be sent for supplier confirmation.'))
        self.write({'state': 'pending_supplier_confirmation'})

    def action_supplier_confirm(self):
        for order in self:
            if order.state != 'pending_supplier_confirmation':
                raise UserError(self.env._('Only bookings pending supplier confirmation can be confirmed.'))
            order.line_ids.check_availability(exclude_order_ids=order.ids)
        self.write({'state': 'confirmed'})

    def action_supplier_reject(self):
        for order in self:
            if order.state != 'pending_supplier_confirmation':
                raise UserError(self.env._('Only bookings pending supplier confirmation can be rejected.'))
        self.write({'state': 'rejected_by_supplier'})

    def action_cancel_by_customer(self):
        for order in self:
            if order.state not in CANCELLABLE_STATES:
                raise UserError(self.env._('This booking cannot be cancelled by the customer from its current state.'))
            order.refund_percentage = order._compute_cancellation_refund_percentage()
        self.write({'state': 'cancelled_by_customer', 'cancelled_date': fields.Datetime.now()})

    def action_cancel_by_admin(self):
        for order in self:
            if order.state not in ADMIN_CANCELLABLE_STATES:
                raise UserError(self.env._('This booking cannot be cancelled from its current state.'))
            if not order.refund_percentage:
                order.refund_percentage = 100.0
        self.write({'state': 'cancelled_by_admin', 'cancelled_date': fields.Datetime.now()})

    def action_request_refund(self):
        for order in self:
            if order.state not in ('cancelled_by_customer', 'cancelled_by_admin'):
                raise UserError(self.env._('Only cancelled bookings can request a refund.'))
        self.write({'state': 'refund_requested'})

    def action_mark_refunded(self):
        for order in self:
            if order.state != 'refund_requested':
                raise UserError(self.env._('Only bookings with a pending refund request can be marked as refunded.'))
        self.write({'state': 'refunded'})

    def action_complete(self):
        for order in self:
            if order.state != 'confirmed':
                raise UserError(self.env._('Only confirmed bookings can be marked as completed.'))
        self.write({'state': 'completed'})

    def action_mark_no_show(self):
        for order in self:
            if order.state != 'confirmed':
                raise UserError(self.env._('Only confirmed bookings can be marked as no-show.'))
        self.write({'state': 'no_show'})

    def action_reset_to_draft(self):
        for order in self:
            if order.state not in ('payment_failed', 'rejected_by_supplier', 'cancelled_by_admin'):
                raise UserError(self.env._('This booking cannot be reset to draft from its current state.'))
        self.write({'state': 'draft', 'refund_percentage': 0.0, 'cancelled_date': False})
