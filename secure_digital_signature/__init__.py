from odoo import fields

from . import models
from . import controllers


def post_init_hook(env):
    """If demo data was loaded, drive demo_request_3 through an actual
    signature so the real PDF-signing engine (field burn-in, hashing,
    certificate generation) has run at least once, giving the store
    screenshots and a first-time evaluator something genuinely completed
    to look at - not just hand-set database fields."""
    signer = env.ref('secure_digital_signature.demo_signer_3a', raise_if_not_found=False)
    if not signer or signer.status != 'sent':
        return
    request = signer.request_id
    name_field = env.ref('secure_digital_signature.demo_field_3a_name', raise_if_not_found=False)
    date_field = env.ref('secure_digital_signature.demo_field_3a_date', raise_if_not_found=False)
    if name_field:
        name_field.write({'value': signer.name})
    if date_field:
        date_field.write({'value': fields.Date.to_string(fields.Date.context_today(request))})
    request._signer_sign(signer, ip_address='127.0.0.1', user_agent='Demo Data Generator')
