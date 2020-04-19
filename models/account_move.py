# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from random import randint


class AccountMove(models.Model):
    _inherit = 'account.move'

    return_id = fields.Many2one(comodel_name="return.order")