# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ReturnConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_bridge_account = fields.Boolean(string="Use Bridge Account", config_parameter='base_setup.use_bridge_account', )
