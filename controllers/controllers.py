# -*- coding: utf-8 -*-
# from odoo import http


# class RetunOrder(http.Controller):
#     @http.route('/retun__order/retun__order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/retun__order/retun__order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('retun__order.listing', {
#             'root': '/retun__order/retun__order',
#             'objects': http.request.env['retun__order.retun__order'].search([]),
#         })

#     @http.route('/retun__order/retun__order/objects/<model("retun__order.retun__order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('retun__order.object', {
#             'object': obj
#         })
