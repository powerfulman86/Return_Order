# -*- coding: utf-8 -*

from odoo import models, fields, api, _


class DeliveryMethodWizard(models.TransientModel):
    _name = 'delivery.method.wizard'

    return_id = fields.Many2one(comodel_name="return.order")
    carrier_id = fields.Many2one('delivery.carrier', 'Carrier')
    cost = fields.Float(string="Cost")
    carrier_set = fields.Boolean(string="", compute='_compute_carrier_set')
    available_carrier_ids = fields.Many2many("delivery.carrier",
                                             string="Available Carriers")

    @api.depends('partner_id')
    def _compute_available_carrier(self):
        for rec in self:
            carriers = self.env['delivery.carrier'].search(
                ['|', ('company_id', '=', False), ('company_id', '=', rec.order_id.company_id.id)])

            rec.available_carrier_ids = carriers.available_carriers(
                rec.return_id.partner_id) if rec.partner_id else carriers

    @api.depends('return_id')
    def _compute_carrier_set(self):
        for rec in self:
            if rec.return_id.carrier_id:
                rec.carrier_set = True
            else:
                rec.carrier_set = False

    @api.onchange('return_id')
    def _onchange_return_id(self):
        for rec in self:
            rec.carrier_id = rec.return_id.carrier_id.id

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        for rec in self:
            rec.cost = rec.carrier_id.fixed_price

    def transfer_to_order(self):
        for rec in self:
            line = self.env['return.order.line'].create({
                'return_id': rec.return_id.id,
                'product_id': rec.carrier_id.product_id.id,
                'description': "[ " + rec.carrier_id.product_id.sku_no + "] " + rec.carrier_id.product_id.name if \
                    rec.carrier_id.product_id.sku_no else rec.carrier_id.product_id.name,
                'price_unit': rec.carrier_id.fixed_price,
                'qty': 1,
            })
            rec.return_id.return_line_ids = [(4, line.id)]
            rec.return_id.carrier_id = rec.carrier_id.id

    def update_order(self):
        for rec in self:
            for line in rec.return_id.return_line_ids:
                if line.product_id.type == 'service':
                    line.unlink()
            line = self.env['return.order.line'].create({
                'return_id': rec.return_id.id,
                'product_id': rec.carrier_id.product_id.id,
                'description': "[ " + rec.carrier_id.product_id.sku_no + "] " + rec.carrier_id.product_id.name if \
                    rec.carrier_id.product_id.sku_no else rec.carrier_id.product_id.name,
                'price_unit': rec.carrier_id.fixed_price,
                'qty': 1,
            })
            rec.return_id.return_line_ids = [(4, line.id)]
            rec.return_id.carrier_id = rec.carrier_id.id
