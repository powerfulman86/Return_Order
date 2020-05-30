# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class ReturnReport(models.Model):
    _name = "return.report"
    _description = "Return Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    @api.model
    def _get_done_states(self):
        return ['sale', 'done', 'paid']

    name = fields.Char(string="code", track_visibility='always')
    date = fields.Date(string="Date", default=fields.Date.context_today)
    sale_id = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=True, track_visibility='always')
    sale_date = fields.Datetime(string="Sale Order Date", related='sale_id.date_order')
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    customer_ref = fields.Char(compute="_compute_partner_code")
    delivery_id = fields.Many2one(comodel_name="stock.picking", string="delivery number", required=True,
                                  track_visibility='always')
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    delivery_date = fields.Datetime(string="Delivery Date", related='delivery_id.scheduled_date')
    reason_id = fields.Many2one(comodel_name="return.reason", string="reason to return", track_visibility='always')
    ticket_id = fields.Many2one(comodel_name="helpdesk.ticket", string="Ticket", track_visibility='always')
    return_line_ids = fields.One2many(comodel_name="return.order.line", inverse_name="return_id",
                                      track_visibility='always')
    picking_ids = fields.One2many(comodel_name="stock.picking", inverse_name="return_id", track_visibility='always')
    state = fields.Selection([
        ('draft', 'Draft RFO'),
        ('reviewed', 'Reviewed'),
        ('approve', 'return order'),
    ], 'Order Status', default='draft', copy=False, readonly=True, track_visibility='always')
    picking_count = fields.Integer(string="Picking Count", compute='_compute_picking_count')
    receipt_count = fields.Integer(string="")
    with_refund = fields.Boolean(string="Refund", )

    invoices_count = fields.Integer('Credit Notes Count', compute='_compute_credit_notes_count')
    invoice_ids = fields.Many2many('account.move', string='Credit Notes')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(l.id) as id,
            l.product_id as product_id,
            t.uom_id as product_uom,
            sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
            sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
            sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
            sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
            sum(l.price_total / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_total,
            sum(l.price_subtotal / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_subtotal,
            sum(l.untaxed_amount_to_invoice / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_to_invoice,
            sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_invoiced,
            count(*) as nbr,
            s.name as name,
            s.date_order as date,
            s.state as state,
            s.partner_id as partner_id,
            s.user_id as user_id,
            p.product_tmpl_id,
            partner.country_id as country_id,
            s.id as return_id
        """

        for field in fields.values():
            select_ += field

        from_ = """
                return_order_line l
                      join return_order s on (l.return_id=s.id) 
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u on (u.id=l.uom_id)  
                %s
        """ % from_clause

        groupby_ = """
            l.product_id,
            l.return_id,
            l.uom_id, 
            s.name,
            s.date,
            s.sale_id,
            s.sale_date,
            s.partner_id,
            s.customer_ref,
            s.delivery_id,
            s.user_id,
            s.delivery_date,
            s.reason_id,
            s.ticket_id,
            s.return_line_ids,
            p.picking_ids,
            p.state,
            p.picking_count,
            p.receipt_count,
            p.with_refund,
            p.invoices_count,
            p.invoice_ids,  
            s.id %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s WHERE l.product_id IS NOT NULL GROUP BY %s)' % (with_, select_, from_, groupby_)

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))


class ReturnOrderReportProforma(models.AbstractModel):
    _name = 'report.return.report_saleproforma'
    _description = 'Proforma Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['return.order'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'return.order',
            'docs': docs,
            'proforma': True
        }
