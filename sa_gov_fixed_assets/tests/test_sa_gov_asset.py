from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaGovAsset(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cls_land = cls.env.ref('sa_gov_fixed_assets.cls_01010101')
        cls.cls_chair = cls.env.ref('sa_gov_fixed_assets.cls_09020301')
        cls.cls_laptop = cls.env.ref('sa_gov_fixed_assets.cls_13020401')

    def test_land_always_capitalized(self):
        asset = self.env['sa.gov.asset'].create({
            'name': 'Test land',
            'classification_id': self.cls_land.id,
            'acquisition_cost': 100.0,
        })
        self.assertTrue(asset.is_capitalized)
        self.assertEqual(asset.accounting_class, '01')

    def test_below_threshold_is_not_capitalized(self):
        asset = self.env['sa.gov.asset'].create({
            'name': 'Cheap chair',
            'classification_id': self.cls_chair.id,
            'acquisition_cost': 500.0,
        })
        self.assertFalse(asset.is_capitalized)
        self.assertEqual(asset.accounting_class, '02')

    def test_above_threshold_is_capitalized(self):
        asset = self.env['sa.gov.asset'].create({
            'name': 'Executive chair',
            'classification_id': self.cls_chair.id,
            'acquisition_cost': 1500.0,
        })
        self.assertTrue(asset.is_capitalized)
        self.assertEqual(asset.accounting_class, '01')

    def test_large_entity_threshold_override(self):
        self.env.company.sa_gov_is_large_entity = True
        asset = self.env['sa.gov.asset'].create({
            'name': 'Chair for large entity',
            'classification_id': self.cls_chair.id,
            'acquisition_cost': 5000.0,
        })
        self.assertFalse(asset.is_capitalized)
        self.assertEqual(asset.effective_threshold, 10000.0)

    def test_registration_generates_code_and_depreciation(self):
        asset = self.env['sa.gov.asset'].create({
            'name': 'Laptop',
            'classification_id': self.cls_laptop.id,
            'acquisition_cost': 4500.0,
            'useful_life_years': 4,
            'acquisition_date': '2024-01-01',
        })
        asset.action_register()
        self.assertEqual(asset.state, 'in_service')
        self.assertTrue(asset.asset_code)
        self.assertIn('13020401', asset.asset_code)
        self.assertEqual(len(asset.depreciation_line_ids), 4)
        first_line = asset.depreciation_line_ids.sorted('sequence')[0]
        first_line.action_post()
        self.assertEqual(asset.accumulated_depreciation, first_line.depreciation_value)
        self.assertEqual(asset.book_value, asset.acquisition_cost - first_line.depreciation_value)
        self.assertAlmostEqual(
            sum(asset.depreciation_line_ids.mapped('depreciation_value')),
            asset.depreciable_value, places=2)

    def test_useful_life_out_of_range_raises(self):
        asset = self.env['sa.gov.asset'].create({
            'name': 'Laptop out of range',
            'classification_id': self.cls_chair.id,
            'acquisition_cost': 5000.0,
        })
        with self.assertRaises(ValidationError):
            asset.useful_life_years = 100

    def test_manual_capitalization_override(self):
        asset = self.env['sa.gov.asset'].create({
            'name': 'Manually forced capitalization',
            'classification_id': self.cls_chair.id,
            'acquisition_cost': 500.0,
            'capitalization_override': True,
            'capitalization_override_value': True,
            'capitalization_override_reason': 'Strategic asset, tracked regardless of cost.',
        })
        self.assertTrue(asset.is_capitalized)

    def test_disposal_requires_method(self):
        asset = self.env['sa.gov.asset'].create({
            'name': 'Laptop to dispose',
            'classification_id': self.cls_laptop.id,
            'acquisition_cost': 4500.0,
            'useful_life_years': 4,
        })
        asset.action_register()
        with self.assertRaises(Exception):
            asset.action_dispose()
        asset.disposal_method = 'write_off'
        asset.action_dispose()
        self.assertEqual(asset.state, 'disposed')
