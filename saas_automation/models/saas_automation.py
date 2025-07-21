# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaasAutomation(models.Model):
    _name = 'saas.automation'
    _description = 'SaaS Automation Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id desc'

    name = fields.Char(string='Automation Name', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    model = fields.Char(string='Target Model', required=True, tracking=True)
    trigger = fields.Selection([
        ('on_create', 'On Create'),
        ('on_write', 'On Update'),
        ('on_delete', 'On Delete'),
        ('scheduled', 'Scheduled'),
        ('manual', 'Manual'),
    ], string='Trigger', required=True, default='scheduled', tracking=True)
    condition = fields.Text(string='Condition (Domain/Python)', tracking=True)
    action = fields.Text(string='Action (Python Code)', tracking=True)
    is_active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes') 