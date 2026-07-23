from odoo import fields, models


class SaGovAssetTypeDetail(models.Model):
    _name = 'sa.gov.asset.type.detail'
    _description = 'Asset Type-Specific Details'

    asset_id = fields.Many2one(
        'sa.gov.asset', required=True, ondelete='cascade', index=True)
    l1_code = fields.Char(related='asset_id.classification_id.l1_code', store=True)

    # --- Land ---
    land_area_m2 = fields.Float('Land Area (m²)')
    land_area_per_deed = fields.Float('Area per Title Deed (m²)')
    land_length = fields.Float('Length (m)')
    land_width = fields.Float('Width (m)')
    land_plot_number = fields.Char('Plot Number')
    land_district = fields.Char('Neighborhood / District')
    land_use_type = fields.Char('Type of Land Use')
    land_street_name = fields.Char('Street Name')

    # --- Buildings ---
    built_up_area = fields.Float('Built-up Area (m²)')
    building_land_area = fields.Float('Building Land Area (m²)')
    floors_above_ground = fields.Integer('Floors Above Ground')
    floors_below_ground = fields.Integer('Floors Below Ground')
    construction_material = fields.Char('Construction Material')
    building_services = fields.Text('Building Services (HVAC, plumbing, etc.)')
    number_of_units = fields.Integer('Number of Units')

    # --- Vehicles / equipment ---
    manufacturer = fields.Char('Manufacturer')
    model_name = fields.Char('Model')
    country_of_origin = fields.Char('Country of Origin')
    manufacturer_serial_number = fields.Char('Manufacturer Serial Number')
    year_of_manufacture = fields.Char('Year of Manufacture')
    registration_plate_number = fields.Char('Registration / Plate Number')
    engine_capacity = fields.Char('Engine Capacity')

    # --- IT / intangible ---
    software_version = fields.Char('Version')
    developer = fields.Char('Developer / Vendor')
    license_expiration_date = fields.Date('License Expiration Date')

    # --- Biological ---
    biological_age = fields.Char('Biological Age')
    biological_stage = fields.Char('Stage in Biological Cycle')
    production_capacity = fields.Char('Production Capacity')

    _sql_constraints = [
        ('asset_uniq', 'unique(asset_id)',
         'Only one type-specific detail record is allowed per asset.'),
    ]
