# -*- coding: utf-8 -*

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    return_id = fields.Many2one(comodel_name="return.order", string="Return Order")
    return_sale_order_id = fields.Many2one('sale.order', related="return_id.sale_id", string='Sales Order')

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()
        if self.return_id:
            reverse_move = self.env['account.move'].browse(res.get('res_id'))
            self.return_id.invoice_ids |= reverse_move
        return res

    @api.onchange('return_id','return_sale_order_id')
    def _onchange_return_id(self):
        for rec in self:
            if rec.return_id:
                if rec.return_id.sale_id:
                    return {'domain': {'move_id': [('id', 'in', rec.return_id.sale_id.invoice_ids.ids)]}}
            rec.reason = 'Return Order ' + rec.return_id.name
