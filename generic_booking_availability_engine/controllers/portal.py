from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

ONGOING_STATES = ('pending_payment', 'paid', 'pending_supplier_confirmation', 'confirmed')
CANCELLED_STATES = ('cancelled_by_customer', 'cancelled_by_admin', 'refund_requested', 'refunded')


class BookingCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'booking_order_count' in counters:
            partner = request.env.user.partner_id
            BookingOrder = request.env['booking.order']
            values['booking_order_count'] = BookingOrder.search_count(
                self._get_booking_order_domain(partner)
            ) if BookingOrder.check_access_rights('read', raise_exception=False) else 0
        return values

    def _get_booking_order_domain(self, partner):
        return [('partner_id', 'child_of', [partner.commercial_partner_id.id])]

    @http.route(['/my/bookings', '/my/bookings/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_bookings(self, page=1, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        BookingOrder = request.env['booking.order']
        partner = request.env.user.partner_id
        domain = self._get_booking_order_domain(partner)

        searchbar_sortings = {
            'date': {'label': _('Booking Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'active': {'label': _('In Progress'), 'domain': [('state', 'in', list(ONGOING_STATES))]},
            'done': {'label': _('Completed'), 'domain': [('state', '=', 'completed')]},
            'cancelled': {'label': _('Cancelled'), 'domain': [('state', 'in', list(CANCELLED_STATES))]},
        }
        if not sortby:
            sortby = 'date'
        if not filterby:
            filterby = 'all'
        order = searchbar_sortings[sortby]['order']
        domain += searchbar_filters[filterby]['domain']

        order_count = BookingOrder.search_count(domain)
        pager = portal_pager(
            url="/my/bookings",
            url_args={'sortby': sortby, 'filterby': filterby},
            total=order_count,
            page=page,
            step=self._items_per_page,
        )
        orders = BookingOrder.search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset'],
        )

        values.update({
            'orders': orders,
            'page_name': 'booking_order',
            'pager': pager,
            'default_url': '/my/bookings',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
        })
        return request.render('generic_booking_availability_engine.portal_my_bookings', values)

    @http.route(['/my/bookings/<int:order_id>'], type='http', auth='user', website=True)
    def portal_booking_order_page(self, order_id, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('booking.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._get_page_view_values(
            order_sudo, access_token, {'page_name': 'booking_order', 'order': order_sudo},
            'my_bookings_history', False, **kw,
        )
        return request.render('generic_booking_availability_engine.portal_my_booking', values)

    @http.route(['/my/bookings/<int:order_id>/voucher'], type='http', auth='user', website=True)
    def portal_booking_order_voucher(self, order_id, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('booking.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        pdf, _ext = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'generic_booking_availability_engine.action_report_booking_voucher', [order_sudo.id],
        )
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', f'attachment; filename={order_sudo.name}.pdf'),
        ]
        return request.make_response(pdf, headers=headers)

    @http.route(['/my/bookings/<int:order_id>/cancel'], type='http', auth='user', website=True, methods=['POST'])
    def portal_booking_order_cancel(self, order_id, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('booking.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if order_sudo.state in ONGOING_STATES:
            order_sudo.action_cancel_by_customer()
        return request.redirect(f'/my/bookings/{order_id}')
