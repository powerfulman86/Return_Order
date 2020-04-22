# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from random import randint


class ReturnOrder(models.Model):
    _name = 'return.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="code", )
    date = fields.Date(string="Date", default=fields.Date.context_today)
    sale_id = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=True)
    sale_date = fields.Datetime(string="Sale Order Date", related='sale_id.date_order')
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    customer_ref = fields.Char(compute="_compute_partner_code")
    delivery_id = fields.Many2one(comodel_name="stock.picking", string="delivery number", required=True, )
    delivery_date = fields.Datetime(string="Delivery Date", related='delivery_id.scheduled_date')
    reason_id = fields.Many2one(comodel_name="return.reason", string="reason to return")
    ticket_id = fields.Many2one(comodel_name="helpdesk.ticket", string="Ticket")
    return_line_ids = fields.One2many(comodel_name="return.order.line", inverse_name="return_id")
    picking_ids = fields.One2many(comodel_name="stock.picking", inverse_name="return_id")
    state = fields.Selection([
        ('draft', 'Draft RFO'),
        ('reviewed', 'Reviewed'),
        ('approve', 'return order'),
    ], 'Order Status', default='draft', copy=False, readonly=True)
    picking_count = fields.Integer(string="Picking Count", compute='_compute_picking_count')
    receipt_count = fields.Integer(string="")
    with_refund = fields.Boolean(string="Refund", )

    invoices_count = fields.Integer('Credit Notes Count', compute='_compute_credit_notes_count')
    invoice_ids = fields.Many2many('account.move', string='Credit Notes')

    def action_view_ticket(self):
        action = self.env.ref('helpdesk.helpdesk_ticket_action_main_tree').read()[0]
        action['domain'] = [('id', '=', self.ticket_id.id)]
        return action

    @api.depends('invoice_ids')
    def _compute_credit_notes_count(self):
        for return_order in self:
            return_order.invoices_count = len(return_order.invoice_ids)

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for return_order in self:
            return_order.picking_count = len(return_order.picking_ids)

    @api.depends('partner_id')
    def _compute_partner_code(self):
        for rec in self:
            rec.customer_ref = rec.partner_id.code

    @api.onchange('partner_id', 'sale_id')
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

    @api.onchange('delivery_id')
    def _onchange_delivery_id(self):
        for rec in self:
            rec.return_line_ids = [(6, 0, [])]
            for line in rec.delivery_id.move_ids_without_package:
                return_id = self.env['return.order.line'].create({
                    'product_id': line.product_id.id,
                    'delivered_qty': line.quantity_done,
                    'uom_id': line.product_uom.id,
                })
                rec.return_line_ids = [(4, return_id.id)]

    def action_reviewed(self):
        self.state = 'reviewed'

    def action_approve(self):
        for rec in self:
            location = self.env.ref('stock.stock_location_stock')
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
            picking = self.env['stock.picking'].create({
                'partner_id': rec.partner_id.id,
                'picking_type_id': picking_type_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id or location.id,
                'location_id': rec.partner_id.property_stock_supplier.id if rec.partner_id.property_stock_supplier else picking_type_id.default_location_dest_id.id,
                'origin': rec.name,
                'user_id': False,
                'date': fields.Date.today(),
                'company_id': self.env.user.company_id.id,
            })
            for line in rec.return_line_ids:
                self.env['stock.move'].create({
                    'picking_id': picking.id,
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_uom_qty': line.qty,
                    'product_uom': line.uom_id.id,
                    'location_id': line.return_id.partner_id.property_stock_supplier.id or location.id,
                    'location_dest_id': picking.picking_type_id.default_location_dest_id.id or location.id,
                    'date': fields.Date.today(),
                    'date_expected': fields.Date.today(),
                    'partner_id': line.return_id.partner_id.id,
                    'state': 'draft',
                    'purchase_line_id': False,
                    'company_id': self.env.user.company_id.id,
                    'price_unit': line.price_unit,
                    'picking_type_id': picking_type_id.id,
                    'group_id': False,
                    'origin': line.return_id.name,
                    'propagate_date': fields.Date.today(),
                    'description_picking': line.product_id._get_description(picking_type_id),
                    'route_ids': picking_type_id.warehouse_id and [
                        (6, 0, [x.id for x in picking_type_id.warehouse_id.route_ids])] or [],
                    'warehouse_id': picking_type_id.warehouse_id.id,
                })
            rec.state = 'approve'
            rec.picking_ids = [(4, picking.id)]
            picking.action_confirm()

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

    def action_picking_view(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', self.picking_ids.ids)]
        return action

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('return.order')
        return super(ReturnOrder, self).create(values)

    # @api.model
    # def create(self, values):
    #     values['name'] = self.check_order_code(str(self.random_number(4)))
    #     return super(ReturnOrder, self).create(values)


class ReturnOrderLine(models.Model):
    _name = 'return.order.line'
    return_id = fields.Many2one(comodel_name="return.order", string="Return", )
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    description = fields.Char(string="Description", )
    qty = fields.Float(string="Quantity", )
    delivered_qty = fields.Float(string="Delivered Qty", )  # compute="_onchange_product_id"
    uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", )
    price_unit = fields.Float(string="Price", )
    price_subtotal = fields.Float(string="Subtotal")

    @api.onchange('product_id')
    def change_product_id(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     product_ids = []
    #     delivery = self.return_id.delivery_id
    #     for line in delivery.move_ids_without_package:
    #         product_ids.append(line.product_id.id)
    #         if self.product_id == line.product_id:
    #             self.delivered_qty = line.quantity_done
    #     if product_ids:
    #         return {'domain': {'product_id': [('id', 'in', product_ids)]}}
    #     else:
    #         return {'domain': {'product_id': [('id', 'in', False)]}}

    # @api.onchange('qty')
    # @api.constrains('qty')
    # def _onchange_quantity(self):
    #     for rec in self:
    #         if rec.qty > rec.delivered_qty:
    #             raise ValidationError(_("Ordered Qty Must be Smaller OR Equal To Delivered Qty"))
