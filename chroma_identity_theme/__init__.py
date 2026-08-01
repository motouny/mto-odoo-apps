from . import models


def post_init_hook(env):
    """Boolean columns added via _inherit to an existing model (res.company)
    are backfilled as NULL/False at the SQL level when the column is
    created - the field's Python default=True only applies to records
    created AFTER the column exists, never to pre-existing rows (and every
    real customer already has a res.company row before installing this
    theme). Without this, the sidebar would silently default to hidden on
    every real install despite default=True in the field definition -
    confirmed by testing: a genuinely new company record gets True
    correctly, the pre-existing one does not."""
    env['res.company'].search([('chroma_sidebar_enabled', '=', False)]).write({
        'chroma_sidebar_enabled': True,
    })
