# -*- coding: utf-8 -*-
from odoo import api, fields, models
from random import randint


class ReturnReason(models.Model):
    _name = 'return.reason'
    _rec_name = 'eng_description'

    name = fields.Char(string="code", )
    eng_description = fields.Char(string="English Description", required=True)
    ara_description = fields.Char(string="Arabic Description", required=True)
    active = fields.Boolean(string="Active", )


    def random_number(self, n):
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        return randint(range_start, range_end)

    def check_return_code(self, code):
        return_ids = self.env['return.reason'].search([('name', '=', str(code))])
        while len(return_ids) >= 1:
            code = str(self.random_number(4))
            self.check_return_code(str(code))
        return code

    @api.model
    def create(self, values):
        values['name'] = self.check_return_code(str(self.random_number(4)))
        return super(ReturnReason, self).create(values)










