# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from random import randint


class ReturnOrder(models.Model):
    _name = 'return.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Return Order"

    name = fields.Char(string="code", track_visibility='always')
    date = fields.Datetime(string="", required=False, default=fields.Datetime.now)
    sale_id = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=True, track_visibility='always')
    sale_date = fields.Datetime(string="Sale Order Date", related='sale_id.date_order')
    receipt_date = fields.Datetime(string="Receipt Date")
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    customer_ref = fields.Char(compute="_compute_partner_code")
    delivery_id = fields.Many2one(comodel_name="stock.picking", string="delivery number", required=True,
                                  track_visibility='always')
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Warehouse receipt", required= True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    delivery_date = fields.Datetime(string="Delivery Date", related='delivery_id.scheduled_date')
    reason_id = fields.Many2one(comodel_name="return.reason", string="reason to return", track_visibility='always')
    ticket_id = fields.Many2one(comodel_name="helpdesk.ticket", string="Ticket", track_visibility='always')
    return_line_ids = fields.One2many(comodel_name="return.order.line", inverse_name="return_id",
                                      track_visibility='always')
    picking_ids = fields.One2many(comodel_name="stock.picking", inverse_name="return_id", track_visibility='always')
    state = fields.Selection([
        ('draft', 'Draft RFO'),
        ('approved', 'Approved'),
        ('on_delivery', 'on-delivery'),
        ('reschedule', 'Reschedule'),
        ('under_inspection', 'Under Inspection'),
        ('inspected', 'Inspected'),
        ('received', 'Received'),
        ('cancel', 'Cancel'),
        ('done', 'Done'),
    ], 'Order Status', default='draft', copy=False, readonly=True, track_visibility='always')
    picking_count = fields.Integer(string="Picking Count", compute='_compute_picking_count')
    receipt_count = fields.Integer(string="")
    with_refund = fields.Boolean(string="Refund", )
    invoices_count = fields.Integer('Credit Notes Count', compute='_compute_credit_notes_count')
    invoice_ids = fields.Many2many('account.move', string='Credit Notes')
    is_all_service = fields.Boolean(string="all services", compute="_count_service_product")
    carrier_id = fields.Many2one('delivery.carrier', 'Carrier')
    partner_shipping_id = fields.Many2one(comodel_name="res.partner", string="Pick UP Address")

    @api.depends('return_line_ids')
    def _count_service_product(self):
        for rec in self:
            count = 0
            for line in rec.return_line_ids:
                if line.product_id.type == 'service':
                    count += 1
            if count > 0:
                rec.is_all_service = True
            else:
                rec.is_all_service = False
                rec.carrier_id = False

    def action_view_ticket(self):
        action = self.env.ref('helpdesk.helpdesk_ticket_action_main_tree').read()[0]
        action['domain'] = [('id', '=', self.ticket_id.id)]
        return action

    def action_view_invoice_ids(self):
        action = self.env.ref('account.action_move_out_refund_type').read()[0]
        action['domain'] = [('id', 'in', self.invoice_ids.ids)]
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
            addr = rec.partner_id.address_get(['delivery'])
            rec.partner_shipping_id = addr and addr.get('delivery')

            rec.delivery_id = False
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
            rec.carrier_id = False
            for line in rec.delivery_id.move_ids_without_package:
                return_id = self.env['return.order.line'].create({
                    'product_id': line.product_id.id,
                    'delivered_qty': line.quantity_done,
                    'uom_id': line.product_uom.id,
                })
                rec.return_line_ids = [(4, return_id.id)]
            for line in rec.sale_id.order_line:
                for delivery in rec.return_line_ids:
                    if line.product_id == delivery.product_id:
                        delivery.celebrity_id = line.celebrity_id.id
                        delivery.price_unit = line.price_unit

    def action_approve(self):
        for rec in self:
            if not rec.env['ir.config_parameter'].sudo().get_param('base_setup.expense_account_id'):
                raise ValidationError(_("Please Enter Celebrity Expense Account in settings"))
            # if not rec.env['ir.config_parameter'].sudo().get_param('base_setup.receipt_warehouse_id'):
            #     raise ValidationError(_("Please Enter Warehouse receipt in settings"))
            picking_type_id = self.env['stock.picking.type'].search([('warehouse_id', '=', rec.warehouse_id.id),
                                                                     ('code', '=', 'incoming')], limit=1)
            location = self.env.ref('stock.stock_location_stock')
            # picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
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
                if line.product_id.type != 'service':
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
            rec.picking_ids = [(4, picking.id)]
            picking.action_confirm()
            journal_id = self.env['account.journal'].browse(
                int(self.env['ir.config_parameter'].sudo().get_param('base_setup.so_journal_id')))
            create_move = 0
            for line in rec.return_line_ids:
                if line.product_id.type == 'service':
                    create_move = 1
                    break
            if create_move == 1:
                move_id = self.env['account.move'].create({
                    'journal_id': journal_id.id,
                    'partner_id': self.partner_id.id,
                    'ref': "shipping for return , " + self.name,
                })
                for line in rec.return_line_ids:
                    if line.product_id.type == 'service':
                        self.env['account.move.line'].with_context(check_move_validity=False).create({
                            'move_id': move_id.id,
                            'name': line.product_id.name,
                            'account_id': line.product_id.property_account_income_id.id if line.product_id.property_account_income_id else line.product_id.categ_id.property_account_income_categ_id.id,
                            'credit': line.price_subtotal,
                            'debit': 0.0,
                        })
                        self.env['account.move.line'].with_context(check_move_validity=False).create({
                            'move_id': move_id.id,
                            'name': 'Expenses Account',
                            'account_id': int(
                                rec.env['ir.config_parameter'].sudo().get_param('base_setup.expense_account_id')),
                            'credit': 0.0,
                            'debit': line.price_subtotal,
                        })
                move_id.post()
            rec.state = 'approved'

    def action_on_delivery(self):
        self.state = 'on_delivery'

    def action_reschedule(self):
        self.state = 'reschedule'

    def action_under_inspection(self):
        for rec in self:
            journal_id = self.env['account.journal'].browse(
                int(self.env['ir.config_parameter'].sudo().get_param('base_setup.so_journal_id')))
            move_id = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'partner_id': self.partner_id.id,
                'ref': "Stock for return , " + self.name,
            })
            for line in rec.return_line_ids:
                if line.product_id.type == 'product':
                    if not line.product_id.categ_id.quarantine_store_account_id:
                        raise ValidationError(
                            _("Quarantine store Account not set in category for product %s !!" % line.product_id.name))

                    self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id': move_id.id,
                        'name': line.product_id.name,
                        'account_id': line.product_id.categ_id.quarantine_store_account_id.id,
                        'credit': line.product_id.standard_price,
                        'debit': 0.0,
                    })
                    self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id': move_id.id,
                        'name': line.product_id.name,
                        'account_id': line.product_id.categ_id.property_stock_account_output_categ_id.id,
                        'credit': 0.0,
                        'debit': line.product_id.standard_price,
                    })
            move_id.post()
        self.state = 'under_inspection'

    def action_inspected(self):
        for rec in self:
            for pick in rec.picking_ids:
                for line in pick.move_ids_without_package:
                    line.quantity_done = line.product_uom_qty
                pick.action_assign()
                pick.button_validate()
        self.state = 'inspected'

    def action_received(self):
        for rec in self:
            journal_id = self.env['account.journal'].browse(
                int(self.env['ir.config_parameter'].sudo().get_param('base_setup.so_journal_id')))
            all_commission = 0.0
            for line in rec.return_line_ids:
                if line.celebrity_id.is_sales_channel is True and line.celebrity_id.channel_type == "2" and line.product_id.type == "product":
                    all_commission += (line.celebrity_id.rate / 100) * line.price_subtotal
                    related_partner_id = self.env['partner.related.partners'].search(
                        [('related_partner_id', '=', line.celebrity_id.id)], limit=1)
                    if related_partner_id:
                        all_commission += (related_partner_id.commission / 100) * line.price_subtotal
            if all_commission > 0:
                mv2 = self.env['account.move'].create({
                    'journal_id': journal_id.id,
                    'type': 'entry',
                    'partner_id': rec.partner_id.id,
                    'ref': "Commission return, " + rec.name,
                })
                c= self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id': mv2.id,
                    'name': "Commission Liability",
                    'account_id': int(
                        self.env['ir.config_parameter'].sudo().get_param('base_setup.liability_account_id')),
                    'credit': all_commission,
                    'debit': 0.0,
                })
                for line in self.return_line_ids:
                    if line.celebrity_id.is_sales_channel is True and line.celebrity_id.channel_type == "2" and line.product_id.type == "product":
                        x = self.env['account.move.line'].with_context(check_move_validity=False).create({
                            'move_id': mv2.id,
                            'name': "distribute Commission for " + line.celebrity_id.name,
                            'account_id': line.celebrity_id.liability_account_id.id,
                            'credit': 0.0,
                            'debit': (line.celebrity_id.rate / 100) * line.price_subtotal,
                        })
                        related_partner_id = self.env['partner.related.partners'].search(
                            [('related_partner_id', '=', line.celebrity_id.id)], limit=1)
                        if related_partner_id:
                            y = self.env['account.move.line'].with_context(check_move_validity=False).create({
                                'move_id': mv2.id,
                                'name': "distribute Commission for " + related_partner_id.partner_id.name,
                                'account_id': related_partner_id.partner_id.liability_account_id.id,
                                'credit': 0.0,
                                'debit': (related_partner_id.commission / 100) * line.price_subtotal,
                            })
                mv2.post()
        self.state = 'received'

    def action_cancel(self):
        for rec in self:
            journal_id = self.env['account.journal'].browse(
                int(self.env['ir.config_parameter'].sudo().get_param('base_setup.so_journal_id')))
            move_id = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'partner_id': self.partner_id.id,
                'ref': "Cancel return , " + self.name,
            })
            for line in rec.return_line_ids:
                if line.product_id.type == 'service':
                    self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id': move_id.id,
                        'name': line.product_id.name,
                        'account_id': line.product_id.property_account_income_id.id if line.product_id.property_account_income_id else line.product_id.categ_id.property_account_income_categ_id.id,
                        'debit': line.price_subtotal,
                        'credit': 0.0,
                    })
                    self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id': move_id.id,
                        'name': 'Expenses Account',
                        'account_id': int(
                            rec.env['ir.config_parameter'].sudo().get_param('base_setup.expense_account_id')),
                        'debit': 0.0,
                        'credit': line.price_subtotal,
                    })
            move_id.post()
        self.state = 'cancel'

    def action_done(self):
        self.state = 'done'

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


class ReturnOrderLine(models.Model):
    _name = 'return.order.line'
    _description = "Return Order Lines"

    return_id = fields.Many2one(comodel_name="return.order", string="Return", )
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    celebrity_id = fields.Many2one("res.partner", string="Celebrity", )
    description = fields.Char(string="Description", )
    qty = fields.Float(string="Quantity", default=1)
    delivered_qty = fields.Float(string="Delivered Qty", )  # compute="_onchange_product_id"
    uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", )
    price_unit = fields.Float(string="Price", )
    price_subtotal = fields.Float(string="Subtotal", compute='_compute_price_subtotal')

    @api.depends('qty', 'price_unit')
    def _compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.qty * rec.price_unit

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
