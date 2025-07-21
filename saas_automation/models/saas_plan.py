# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaasPlan(models.Model):
    _name = 'saas.plan'
    _description = 'SaaS Subscription Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id desc'

    name = fields.Char(string='Plan Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    price_monthly = fields.Float(string='Monthly Price', required=True, tracking=True)
    price_yearly = fields.Float(string='Yearly Price', tracking=True)
    is_active = fields.Boolean(string='Active', default=True, tracking=True)
    max_users = fields.Integer(string='Max Users', default=1, tracking=True)
    max_instances = fields.Integer(string='Max Instances', default=1, tracking=True)
    included_modules_ids = fields.Many2many('ir.module.module', string='Included Modules')
    notes = fields.Text(string='Notes') 