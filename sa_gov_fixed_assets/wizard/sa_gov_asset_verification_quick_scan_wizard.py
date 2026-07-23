from odoo import _, api, fields, models


class SaGovAssetVerificationQuickScanWizard(models.TransientModel):
    _name = 'sa.gov.asset.verification.quick.scan.wizard'
    _description = 'Quick Scan (Barcode / QR / RFID)'

    verification_id = fields.Many2one(
        'sa.gov.asset.verification', required=True,
        default=lambda self: self.env.context.get('active_id'))
    scan_input = fields.Char(
        string='Scan Code',
        help='Point a barcode/QR scanner or a handheld RFID reader (HID/'
             'keyboard-wedge mode) at the asset tag - the scanned code lands '
             'here exactly like typed text, is looked up automatically, and '
             'this field clears itself for the next scan.')
    last_result = fields.Char(readonly=True)
    last_asset_id = fields.Many2one('sa.gov.asset', readonly=True)
    scanned_count = fields.Integer(compute='_compute_scanned_count')

    @api.depends('verification_id')
    def _compute_scanned_count(self):
        for wizard in self:
            wizard.scanned_count = len(wizard.verification_id.line_ids.filtered('found'))

    def _find_asset(self, code):
        return self.env['sa.gov.asset'].search([
            '|', '|', '|',
            ('asset_code', '=', code),
            ('tag_number', '=', code),
            ('tag_ids.tag_number', '=', code),
            ('tag_ids.rfid_tag_id', '=', code),
        ], limit=1)

    def action_scan(self):
        self.ensure_one()
        code = (self.scan_input or '').strip()
        if not code:
            return self._reload()

        asset = self._find_asset(code)
        if not asset:
            self.write({
                'scan_input': False,
                'last_result': _('Unknown code: %(code)s', code=code),
                'last_asset_id': False,
            })
            return self._reload()

        line = self.verification_id.line_ids.filtered(lambda l: l.asset_id == asset)
        if line:
            line.write({'found': True, 'inspection_date': fields.Date.context_today(self)})
            msg = _('Marked found: %(name)s', name=asset.name)
        else:
            self.env['sa.gov.asset.verification.line'].create({
                'verification_id': self.verification_id.id,
                'asset_id': asset.id,
                'found': True,
                'inspection_date': fields.Date.context_today(self),
                'condition_found': asset.condition,
            })
            msg = _('Added and marked found: %(name)s', name=asset.name)

        self.write({'scan_input': False, 'last_result': msg, 'last_asset_id': asset.id})
        return self._reload()

    def _reload(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
