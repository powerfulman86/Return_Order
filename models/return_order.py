# -*- coding: utf-8 -*-
from odoo import api, fields, models
from random import randint


class ReturnOrder(models.Model):
    _name = 'return.order'

    name = fields.Char(string="code", )
    date = fields.Date(string="Date", default=fields.Date.context_today)
    sale_id = fields.Many2one(comodel_name="sale.order", string="Sale Order")
    sale_date = fields.Datetime(string="Sale Order Date", related='sale_id.date_order')
    partner_id = fields.Many2one('res.partner', 'Customer')
    customer_ref = fields.Char(readonly="1")
    delivery_id = fields.Many2one(comodel_name="stock.picking", string="delivery number", required=False, )
    delivery_date = fields.Datetime(string="Delivery Date", related='delivery_id.date_done')
    reason_id = fields.Many2one(comodel_name="return.reason", string="reason to return")
    return_line_ids = fields.One2many(comodel_name="return.order.line", inverse_name="return_id")
    state = fields.Selection([
        ('draft', 'Draft RFO'),
        ('reviewed', 'Reviewed'),
        ('approve', 'return order'),
    ], 'Order Status', default='draft', copy=False, readonly=True)

    @api.onchange('partner_id','sale_id')
    def _onchange_partner_id(self):

        for rec in self:
            if rec.partner_id:
                sale_ids = self.env['sale.order'].search([('partner_id', '=', rec.partner_id.id),
                                                          ('state', 'not in', ['draft', 'cancel'])])
                if sale_ids:
                    return {'domain': {'sale_id': [('id', 'in', sale_ids.ids)]}}
                else:
                    return {'domain': {'sale_id': [('id', '=', False)]}}
            else:
                return {'domain': {'sale_id': [('id', '=', False)]}}

    @api.onchange('sale_id', 'delivery_id')
    def _onchange_sale_id(self):
        if self.sale_id:
            return {'domain': {'delivery_id': [('id', 'in', self.sale_id.picking_ids.ids)]}}
        else:
            return {'domain': {'delivery_id': [('id', 'in', False)]}}

    def action_reviewed(self):
        self.state = 'reviewed'

    def action_approve(self):
        self.state = 'approve'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def random_number(self, n):
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        return randint(range_start, range_end)

    def check_order_code(self, code):
        return_ids = self.env['return.order'].search([('name', '=', str(code))])
        while len(return_ids) >= 1:
            code = str(self.random_number(4))
            self.check_order_code(str(code))
        return code

    @api.model
    def create(self, values):
        values['name'] = self.check_order_code(str(self.random_number(4)))
        return super(ReturnOrder, self).create(values)


class ReturnOrderLine(models.Model):
    _name = 'return.order.line'
    return_id = fields.Many2one(comodel_name="return.order", string="Return", )
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    description = fields.Char(string="Description", )
    qty = fields.Float(string="Quantity", )
    uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", )
    price_unit = fields.Float(string="Price", )
    price_subtotal = fields.Float(string="Subtotal")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product_ids = []
        delivery = self.return_id.delivery_id
        for line in delivery:
            product_ids.append(line.product_id.id)
        if product_ids:
            return {'domain': {'product_id': [('id', 'in', product_ids)]}}
        else:
            return {'domain': {'product_id': [('id', 'in', False)]}}
