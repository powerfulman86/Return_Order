# -*- coding: utf-8 -*-
from odoo import api, fields, models
from random import randint


class ReturnVoucher(models.Model):
    _name = 'return.voucher'

    name = fields.Char(string="code", )
    date = fields.Date(string="Date", default=fields.Date.context_today)
    sale_id = fields.Many2one(comodel_name="sale.order", string="Sale Order")
    sale_date = fields.Datetime(string="Date", related='sale_id.date_order')
    partner_id = fields.Many2one(related='sale_id.partner_id', readonly="1")
    customer_ref = fields.Char(readonly="1")
    delivery_number = fields.Char(string="delivery number", )
    delivery_date = fields.Date(string="Date")
    reason_id = fields.Many2one(comodel_name="return.order", string="reason to return")
    state = fields.Selection([
        ('draft', 'Draft RFO'),
        ('reviewed', 'Reviewed'),
        ('approve', 'return order'),
    ], 'Order Status', default='draft', copy=False, readonly=True)

    def action_reviewed(self):
        self.state = 'reviewed'

    def action_approve(self):
        self.state = 'approve'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    @api.onchange('sale_id')
    def _onchange_sale_id(self):
        for rec in self:
            rec.customer_ref = rec.sale_id.partner_id.code

    def random_number(self, n):
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        return randint(range_start, range_end)

    def check_voucher_code(self, code):
        return_ids = self.env['return.voucher'].search([('name', '=', str(code))])
        while len(return_ids) >= 1:
            code = str(self.random_number(4))
            self.check_voucher_code(str(code))
        return code

    @api.model
    def create(self, values):
        values['name'] = self.check_voucher_code(str(self.random_number(4)))
        return super(ReturnVoucher, self).create(values)