# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaasAnalytics(models.Model):
    _name = 'saas.analytics'
    _description = 'SaaS Analytics & KPIs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Analytics Name', required=True, tracking=True)
    instance_id = fields.Many2one('saas.instance', string='SaaS Instance', tracking=True)
    date = fields.Date(string='Date', required=True, tracking=True)
    active_users = fields.Integer(string='Active Users', tracking=True)
    cpu_usage = fields.Float(string='CPU Usage (%)', tracking=True)
    memory_usage = fields.Float(string='Memory Usage (MB)', tracking=True)
    storage_usage = fields.Float(string='Storage Usage (GB)', tracking=True)
    kpi_json = fields.Text(string='KPI Data (JSON)')
    notes = fields.Text(string='Notes') 