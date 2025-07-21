# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaasBilling(models.Model):
    _name = 'saas.billing'
    _description = 'SaaS Billing & Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Billing Reference', required=True, tracking=True)
    subscription_id = fields.Many2one('saas.subscription', string='Subscription', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    invoice_date = fields.Date(string='Invoice Date', required=True, tracking=True)
    amount_total = fields.Float(string='Total Amount', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    ], string='Status', default='draft', tracking=True)
    payment_date = fields.Date(string='Payment Date', tracking=True)
    notes = fields.Text(string='Notes') 