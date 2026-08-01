from odoo.tests.common import HttpCase, JsonRpcException, tagged


@tagged('post_install', '-at_install')
class TestLoginPageDesignerHttp(HttpCase):

    def test_default_login_untouched_when_disabled(self):
        self.env.company.lpd_enabled = False
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('o_lpd_login_page', response.text)

    def test_login_page_reflects_saved_design(self):
        self.env.company.write({
            'lpd_enabled': True,
            'lpd_position': 'right',
            'lpd_welcome_title': 'Hello Testers',
            'lpd_pro_mode': True,
            'lpd_custom_html': '<span class="lpd-marker">pro-panel</span>',
        })
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_lpd_login_page', response.text)
        self.assertIn('o_lpd_position_right', response.text)
        self.assertIn('Hello Testers', response.text)
        self.assertIn('lpd-marker', response.text)

    def test_custom_html_hidden_without_pro_mode(self):
        self.env.company.write({
            'lpd_enabled': True,
            'lpd_pro_mode': False,
            'lpd_custom_html': '<span class="lpd-marker">pro-panel</span>',
        })
        response = self.url_open('/web/login')
        self.assertNotIn('lpd-marker', response.text)

    def test_preview_route_rejects_non_admin(self):
        self.env.company.lpd_enabled = True
        user_demo = self.env.ref('base.user_demo', raise_if_not_found=False)
        if not user_demo:
            self.skipTest('base.user_demo not available in this database')
        self.authenticate(user_demo.login, user_demo.login)
        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request('/login_page_designer/set_preview', {
                'config': {'position': 'left'},
            })

    def test_preview_route_accepts_admin_and_affects_preview_only(self):
        self.env.company.write({'lpd_enabled': True, 'lpd_position': 'center'})
        self.authenticate('admin', 'admin')
        result = self.make_jsonrpc_request('/login_page_designer/set_preview', {
            'config': {
                'position': 'bottom', 'card_bg_color': '#fff', 'card_text_color': '#000',
                'button_color': '#000', 'bg_type': 'none', 'bg_color': '#000',
                'bg_gradient_start': '#000', 'bg_gradient_end': '#000',
                'bg_gradient_angle': 0, 'bg_image_url': False,
                'bg_overlay_opacity': 0.0, 'welcome_title': 'Preview Only Title',
                'welcome_subtitle': '', 'pro_mode': False,
                'custom_css': '', 'custom_html': '',
            },
        })
        self.assertTrue(result['ok'])

        preview_response = self.url_open('/web/login?login_page_designer_preview=1')
        self.assertIn('o_lpd_position_bottom', preview_response.text)
        self.assertIn('Preview Only Title', preview_response.text)

        # The saved company config (position=center) must be untouched -
        # a plain request without the preview flag should not see the draft.
        real_response = self.url_open('/web/login')
        self.assertIn('o_lpd_position_center', real_response.text)
        self.assertNotIn('Preview Only Title', real_response.text)
