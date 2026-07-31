from odoo import api, SUPERUSER_ID

# post_init_hook only runs on a fresh install, not on `-u` upgrades - an
# existing sa_dga_theme_website install upgrading from 18.0.1.1.0 would
# otherwise never get Arabic added to website.language_ids. Same logic,
# reachable on upgrade too.


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.sa_dga_theme_website import post_init_hook
    post_init_hook(env)
