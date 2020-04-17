# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class retun__order(models.Model):
#     _name = 'retun__order.retun__order'
#     _description = 'retun__order.retun__order'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
