# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from random import randint


class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    quarantine_store_account_id = fields.Many2one(comodel_name="account.account", string="Quarantine Store")


