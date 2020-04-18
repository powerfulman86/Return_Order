# -*- coding: utf-8 -*-
from odoo import api, fields, models
from random import randint


class ReturnOrder(models.Model):
    _name = 'return.order'

    name = fields.Char(string="code", )
    eng_description = fields.Char(string="English Description", required=True)
    ara_description = fields.Char(string="Arabic Description", required=True)
    active = fields.Boolean(string="Active", )
    state = fields.Selection([
        ('draft', 'Draft RFO'),
        ('reviewed', 'Reviewed'),
        ('approve', 'return order'),
    ], 'Order Status',default='draft', copy=False, readonly=True)

    def random_number(self, n):
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        return randint(range_start, range_end)

    def check_return_code(self, code):
        return_ids = self.env['return.order'].search([('name', '=', str(code))])
        while len(return_ids) >= 1:
            code = str(self.random_number(4))
            self.check_return_code(str(code))
        return code

    @api.model
    def create(self, values):
        values['name'] = self.check_return_code(str(self.random_number(4)))
        return super(ReturnOrder, self).create(values)

    def action_reviewed(self):
        self.state = 'reviewed'

    def action_approve(self):
        self.state = 'approve'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'
