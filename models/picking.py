# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from random import randint


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    return_id = fields.Many2one(comodel_name="return.order")


