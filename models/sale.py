# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from random import randint


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    return_ids = fields.One2many(comodel_name="return.order", inverse_name="sale_id")
    return_count = fields.Integer(string="return", compute="_compute_return")

    @api.depends('return_ids')
    def _compute_return(self):
        for rec in self:
            rec.return_count = len(rec.return_ids.ids)

    def action_view_return(self):
        return_ids = self.mapped('return_ids')
        action = self.env.ref('action_request_return_order_view	').read()[0]
        action['domain'] = [('id', 'in', return_ids.ids)]
        return action
