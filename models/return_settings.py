# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ReturnConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    return_reason = fields.Selection(string="Reason", selection=[('1', '----'), ('2', '-----'), ], required=False, )
