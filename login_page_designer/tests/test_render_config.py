from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLoginPageDesignerConfig(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company

    def test_disabled_returns_false(self):
        self.company.lpd_enabled = False
        self.assertFalse(self.company._lpd_get_render_config())

    def test_enabled_returns_full_config(self):
        self.company.write({
            'lpd_enabled': True,
            'lpd_position': 'left',
            'lpd_card_bg_color': '#111111',
            'lpd_button_color': '#222222',
            'lpd_bg_type': 'color',
            'lpd_bg_color': '#333333',
            'lpd_welcome_title': 'Hi there',
            'lpd_pro_mode': False,
            'lpd_custom_css': 'body { color: red; }',
        })
        cfg = self.company._lpd_get_render_config()
        self.assertTrue(cfg)
        self.assertEqual(cfg['position'], 'left')
        self.assertEqual(cfg['card_bg_color'], '#111111')
        self.assertEqual(cfg['welcome_title'], 'Hi there')
        # pro_mode is off, so custom_css must not leak into the config
        # even though the field itself is still populated on the company.
        self.assertEqual(cfg['custom_css'], '')

    def test_pro_mode_gates_custom_code(self):
        self.company.write({
            'lpd_enabled': True,
            'lpd_pro_mode': True,
            'lpd_custom_css': '.foo { color: blue; }',
            'lpd_custom_html': '<p>Hello</p>',
        })
        cfg = self.company._lpd_get_render_config()
        self.assertEqual(cfg['custom_css'], '.foo { color: blue; }')
        self.assertEqual(cfg['custom_html'], '<p>Hello</p>')

    def test_style_markup_contains_position_and_colors(self):
        cfg = {
            'position': 'right', 'card_bg_color': '#ABCDEF',
            'card_text_color': '#000000', 'button_color': '#FF00FF',
            'bg_type': 'color', 'bg_color': '#00FF00',
            'bg_gradient_start': '#000', 'bg_gradient_end': '#fff',
            'bg_gradient_angle': 90, 'bg_image_url': False,
            'bg_overlay_opacity': 0.0, 'pro_mode': False,
            'custom_css': '', 'custom_html': '',
        }
        style = self.company._lpd_build_style_markup(cfg)
        self.assertIn('flex-end', style)  # right -> justify-content: flex-end
        self.assertIn('#ABCDEF', style)
        self.assertIn('#FF00FF', style)
        self.assertIn('background-color: #00FF00', style)

    def test_style_markup_gradient_and_image(self):
        cfg = {
            'position': 'top', 'card_bg_color': '#fff', 'card_text_color': '#000',
            'button_color': '#000', 'bg_type': 'gradient', 'bg_color': '#000',
            'bg_gradient_start': '#111111', 'bg_gradient_end': '#222222',
            'bg_gradient_angle': 45, 'bg_image_url': False,
            'bg_overlay_opacity': 0.0, 'pro_mode': False,
            'custom_css': '', 'custom_html': '',
        }
        style = self.company._lpd_build_style_markup(cfg)
        self.assertIn('linear-gradient(45deg, #111111, #222222)', style)

        cfg['bg_type'] = 'image'
        cfg['bg_image_url'] = '/login_page_designer/background/1'
        cfg['bg_overlay_opacity'] = 0.4
        style = self.company._lpd_build_style_markup(cfg)
        self.assertIn('/login_page_designer/background/1', style)
        self.assertIn('rgba(0,0,0,0.4)', style)

    def test_custom_css_appended_only_in_pro_mode(self):
        base_cfg = {
            'position': 'center', 'card_bg_color': '#fff', 'card_text_color': '#000',
            'button_color': '#000', 'bg_type': 'none', 'bg_color': '#000',
            'bg_gradient_start': '#000', 'bg_gradient_end': '#000',
            'bg_gradient_angle': 0, 'bg_image_url': False,
            'bg_overlay_opacity': 0.0, 'custom_css': '.marker{}', 'custom_html': '',
        }
        base_cfg['pro_mode'] = False
        self.assertNotIn('.marker{}', self.company._lpd_build_style_markup(base_cfg))
        base_cfg['pro_mode'] = True
        self.assertIn('.marker{}', self.company._lpd_build_style_markup(base_cfg))

    def test_html_markup_gated_by_pro_mode(self):
        cfg = {'pro_mode': False, 'custom_html': '<p>secret</p>'}
        self.assertEqual(str(self.company._lpd_build_html_markup(cfg)), '')
        cfg['pro_mode'] = True
        self.assertIn('<p>secret</p>', str(self.company._lpd_build_html_markup(cfg)))
