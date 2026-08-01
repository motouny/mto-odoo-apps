from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestLoginPageDesignerWebsite(HttpCase):
    """website.login_layout (priority 20) replaces web.login_layout's own
    content wholesale - see the note in login_page_designer_website/views/
    website_login_templates.xml. These tests confirm the design still
    applies once Website is installed, and that the site's own header/
    footer are hidden for a clean branded login screen when enabled."""

    def test_disabled_shows_default_website_chrome(self):
        self.env.company.lpd_enabled = False
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('o_lpd_login_page', response.text)
        # the full site header/nav is still present when the designer is off
        self.assertIn('o_main_nav', response.text)

    def test_enabled_hides_site_chrome_and_shows_card(self):
        self.env.company.write({
            'lpd_enabled': True,
            'lpd_position': 'top',
            'lpd_welcome_title': 'Website Mode Title',
        })
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_lpd_login_page', response.text)
        self.assertIn('o_lpd_position_top', response.text)
        self.assertIn('Website Mode Title', response.text)
        self.assertIn('o_lpd_card', response.text)
        # the site's own navbar should be suppressed for a clean login screen
        self.assertNotIn('o_main_nav', response.text)
