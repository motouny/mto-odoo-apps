from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """Expose the sidebar on/off setting in the JS session bootstrap
        data (odoo.__session_info__) - the sidebar is a main_components
        registry entry that mounts before any ORM call could complete,
        so it needs this available synchronously at boot rather than
        fetched after the fact."""
        result = super().session_info()
        result['sa_dga_sidebar_enabled'] = bool(self.env.company.sa_dga_sidebar_enabled)
        return result
