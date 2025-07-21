# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaasDashboard(models.Model):
    _name = 'saas.dashboard'
    _description = 'SaaS Dashboard'

    name = fields.Char(string='Name', required=True)
    total_instances = fields.Integer(string='Total Instances', compute='_compute_total_instances')
    active_instances = fields.Integer(string='Active Instances', compute='_compute_active_instances')
    active_users = fields.Integer(string='Active Users', compute='_compute_active_users')
    mrr = fields.Float(string='Monthly Recurring Revenue', compute='_compute_mrr')

    def _compute_total_instances(self):
        self.total_instances = self.env['saas.instance'].search_count([])

    def _compute_active_instances(self):
        self.active_instances = self.env['saas.instance'].search_count([('state', '=', 'running')])

    def _compute_active_users(self):
        self.active_users = sum(self.env['saas.instance'].search([('state', '=', 'running')]).mapped('active_user_count'))

    def _compute_mrr(self):
        self.mrr = sum(self.env['saas.subscription'].search([('state', '=', 'active')]).mapped('price')) 