# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ReturnConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    return_reason = fields.Selection(string="", selection=[('1', '1'), ('2', '2'), ], required=False, )
    use_bridge_account = fields.Boolean(string="Use Bridge Account", config_parameter='base_setup.use_bridge_account', )
