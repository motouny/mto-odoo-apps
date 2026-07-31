def post_init_hook(env):
    """Make Arabic switchable on every website - without this, Arabic
    stays "installed" at the res.lang level (usable in the backend) but
    is invisible on the actual public site, since website frontend
    language switching is driven by website.language_ids, not by which
    languages are simply installed. Does NOT touch default_lang_id, so
    an existing site's default language is never changed by installing
    this theme."""
    arabic = env['res.lang'].search([('code', '=', 'ar_001')], limit=1)
    if not arabic:
        return
    for website in env['website'].search([]):
        if arabic.id not in website.language_ids.ids:
            website.language_ids = [(4, arabic.id)]
