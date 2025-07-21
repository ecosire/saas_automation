# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaasSubscription(models.Model):
    _name = 'saas.subscription'
    _description = 'SaaS Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Subscription Name', required=True, tracking=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    instance_id = fields.Many2one('saas.instance', string='SaaS Instance', required=True, tracking=True)
    plan_id = fields.Many2one('saas.plan', string='Plan', required=True, tracking=True)
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    recurring_interval = fields.Integer(string='Billing Cycle', default=1, tracking=True)
    recurring_rule_type = fields.Selection([
        ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)'),
    ], string='Recurrence', default='monthly', tracking=True)
    price = fields.Float(string='Subscription Price', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes') 

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('saas.subscription') or _('New')
        result = super(SaasSubscription, self).create(vals)
        return result

    def action_activate_subscription(self):
        self.write({'state': 'active'})
        self._create_invoice()

    def action_suspend_subscription(self):
        self.write({'state': 'suspended'})

    def action_resume_subscription(self):
        self.write({'state': 'active'})

    def action_cancel_subscription(self):
        self.write({'state': 'cancelled'})

    def _create_invoice(self):
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': self.plan_id.name,
                'price_unit': self.price,
                'quantity': 1,
            })],
        }
        self.env['account.move'].create(invoice_vals)

    def _cron_expire_subscriptions(self):
        expired_subscriptions = self.search([
            ('end_date', '<', fields.Date.today()),
            ('state', 'in', ['active', 'suspended'])
        ])
        expired_subscriptions.write({'state': 'expired'}) 