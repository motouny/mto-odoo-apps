from odoo import api, fields, models


class SaGovAssetTag(models.Model):
    _name = 'sa.gov.asset.tag'
    _description = 'Asset Physical Tag'
    _order = 'issue_date desc, id desc'

    asset_id = fields.Many2one(
        'sa.gov.asset', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='asset_id.company_id', store=True)
    tag_number = fields.Char(required=True, copy=False)
    issue_date = fields.Date(default=fields.Date.context_today)
    active = fields.Boolean(default=True)

    is_movable = fields.Boolean(
        'Asset is Movable',
        help='Portability affects whether a physical tag is used to track '
             'the asset\'s current location (guide §4.4, p.36).')
    safety_risk = fields.Boolean(
        'Physical Tag Poses a Safety Risk',
        help='If affixing a physical tag could create a hazard or damage '
             'risk, the asset is coded/tracked without a physical sticker.')
    requires_physical_tag = fields.Boolean(
        compute='_compute_requires_physical_tag', store=True)

    barcode_type = fields.Selection([
        ('qr', 'QR Code'),
        ('code128', 'Barcode (Code128)'),
    ], default='qr', required=True,
        help='The guide (p.37) accepts either a QR code or a linear barcode '
             'on the printed tag - pick whichever your scanning hardware reads.')
    scan_value = fields.Char(compute='_compute_scan_value', store=True)

    rfid_tag_id = fields.Char(
        'RFID Tag ID (EPC)', copy=False, index='btree_not_null',
        help='Electronic Product Code or unique ID encoded on an RFID tag '
             'physically attached to the asset, if one is used instead of '
             '(or alongside) a printed QR/barcode label. Handheld RFID '
             'readers normally emulate a keyboard (HID mode) and can feed '
             'this value straight into the Quick Scan screen for fast '
             'electronic verification counts.')

    _sql_constraints = [
        ('rfid_tag_id_uniq', 'unique(rfid_tag_id)',
         'This RFID Tag ID is already assigned to another tag.'),
    ]

    @api.depends('is_movable', 'safety_risk')
    def _compute_requires_physical_tag(self):
        for tag in self:
            tag.requires_physical_tag = bool(tag.is_movable) and not tag.safety_risk

    @api.depends('tag_number', 'asset_id.asset_code')
    def _compute_scan_value(self):
        for tag in self:
            tag.scan_value = tag.tag_number or tag.asset_id.asset_code

    def action_reissue(self):
        """Move the current tag number to old_tag_number on the asset and
        clear this record's fields for a fresh tag number to be entered."""
        for tag in self:
            asset = tag.asset_id
            if asset.tag_number:
                asset.old_tag_number = asset.tag_number
            asset.tag_number = tag.tag_number
