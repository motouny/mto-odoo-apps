from datetime import date, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBookingOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.policy = cls.env['booking.cancellation.policy'].create({
            'name': 'Test Policy',
            'line_ids': [
                (0, 0, {'days_before_start': 7, 'refund_percentage': 100.0}),
                (0, 0, {'days_before_start': 3, 'refund_percentage': 50.0}),
                (0, 0, {'days_before_start': 0, 'refund_percentage': 0.0}),
            ],
        })
        cls.resource = cls.env['booking.resource'].create({
            'name': 'Test Room',
            'capacity': 2,
            'unit_price': 100.0,
            'cancellation_policy_id': cls.policy.id,
        })

    def _create_order(self, quantity=1, date_from=None, date_to=None, partner=None):
        date_from = date_from or (date.today() + timedelta(days=10))
        date_to = date_to or date_from
        return self.env['booking.order'].create({
            'partner_id': (partner or self.partner).id,
            'line_ids': [(0, 0, {
                'resource_id': self.resource.id,
                'date_from': date_from,
                'date_to': date_to,
                'quantity': quantity,
                'unit_price': self.resource.unit_price,
            })],
        })

    def test_sequence_assigned_on_create(self):
        order = self._create_order()
        self.assertNotEqual(order.name, '/')
        self.assertTrue(order.name.startswith('BK/'))

    def test_pricing_rule_resolution(self):
        rule_date = date.today() + timedelta(days=30)
        self.env['booking.pricing.rule'].create({
            'name': 'Peak',
            'resource_id': self.resource.id,
            'date_from': rule_date,
            'date_to': rule_date + timedelta(days=5),
            'price': 250.0,
            'priority': 20,
        })
        self.assertEqual(self.resource.price_for_date(rule_date), 250.0)
        self.assertEqual(
            self.resource.price_for_date(date.today() + timedelta(days=1)),
            self.resource.unit_price,
        )

    def test_capacity_guard_blocks_overbooking(self):
        target_date = date.today() + timedelta(days=15)
        order1 = self._create_order(quantity=2, date_from=target_date)
        order1.action_request_payment()
        order1.action_mark_paid()

        order2 = self._create_order(quantity=1, date_from=target_date)
        order2.action_request_payment()
        with self.assertRaises(ValidationError):
            order2.action_mark_paid()

    def test_full_workflow_confirm_and_complete(self):
        order = self._create_order()
        order.action_request_payment()
        self.assertEqual(order.state, 'pending_payment')
        order.action_mark_paid()
        self.assertEqual(order.state, 'paid')
        order.action_send_to_supplier()
        self.assertEqual(order.state, 'pending_supplier_confirmation')
        order.action_supplier_confirm()
        self.assertEqual(order.state, 'confirmed')
        order.action_complete()
        self.assertEqual(order.state, 'completed')

    def test_invalid_transition_raises(self):
        order = self._create_order()
        with self.assertRaises(UserError):
            order.action_mark_paid()

    def test_cancellation_refund_percentage(self):
        order = self._create_order(date_from=date.today() + timedelta(days=8))
        order.action_request_payment()
        order.action_mark_paid()
        order.action_cancel_by_customer()
        self.assertEqual(order.state, 'cancelled_by_customer')
        self.assertEqual(order.refund_percentage, 100.0)
        self.assertAlmostEqual(order.refund_amount, order.amount_total)

    def test_cancellation_refund_percentage_partial(self):
        order = self._create_order(date_from=date.today() + timedelta(days=4))
        order.action_request_payment()
        order.action_mark_paid()
        order.action_cancel_by_customer()
        self.assertEqual(order.refund_percentage, 50.0)

    def test_max_quantity_per_booking_constraint(self):
        self.resource.max_quantity_per_booking = 1
        with self.assertRaises(ValidationError):
            self._create_order(quantity=2)
