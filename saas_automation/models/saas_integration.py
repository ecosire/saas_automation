# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaasIntegration(models.Model):
    _name = 'saas.integration'
    _description = 'SaaS Integration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Integration Name', required=True, tracking=True)
    integration_type = fields.Selection([
        ('payment_gateway', 'Payment Gateway'),
        ('api', 'API'),
        ('webhook', 'Webhook'),
        ('crm', 'CRM'),
        ('accounting', 'Accounting'),
        ('custom', 'Custom'),
    ], string='Integration Type', required=True, tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    base_url = fields.Char(string='Base URL', tracking=True)
    api_key = fields.Char(string='API Key', tracking=True)
    is_active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes') 