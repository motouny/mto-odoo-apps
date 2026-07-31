from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

ALLOWED_GROUPS = (
    'smart_visitor_management.group_visitor_manager',
    'smart_visitor_management.group_visitor_receptionist',
    'smart_visitor_management.group_visitor_security',
)


class VisitorKioskController(http.Controller):

    def _check_kiosk_access(self):
        user = request.env.user
        if user._is_public() or not any(user.has_group(g) for g in ALLOWED_GROUPS):
            raise AccessError('You are not allowed to use the visitor kiosk.')

    @http.route('/visitor/kiosk/scan', type='json', auth='user')
    def visitor_kiosk_scan(self, token=None, action=None, gate_id=None):
        self._check_kiosk_access()
        Visit = request.env['visitor.visit']
        token = (token or '').strip()
        gate_id = int(gate_id) if gate_id else False

        if action == 'check_in':
            result = Visit._process_checkin(token, gate_id=gate_id, manual=False)
        elif action == 'check_out':
            result = Visit._process_checkout(token, gate_id=gate_id, manual=False)
        else:
            return {'ok': False, 'message': 'Unknown action.'}

        visit_id = result.get('visit_id')
        if visit_id:
            visit = Visit.sudo().browse(visit_id)
            result['guest_name'] = visit.guest_id.name
            result['visit_name'] = visit.name
            result['state'] = visit.state

        return result
