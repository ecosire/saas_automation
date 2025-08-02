# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaasDashboard(models.Model):
    _name = 'saas.dashboard'
    _description = 'SaaS Dashboard'

    name = fields.Char(string='Name', required=True)
    total_instances = fields.Integer(string='Total Instances', compute='_compute_dashboard_data', store=True)
    active_instances = fields.Integer(string='Active Instances', compute='_compute_dashboard_data', store=True)
    active_users = fields.Integer(string='Active Users', compute='_compute_dashboard_data', store=True)
    mrr = fields.Float(string='Monthly Recurring Revenue', compute='_compute_dashboard_data', store=True)

    @api.depends('name')
    def _compute_dashboard_data(self):
        """Compute all dashboard metrics."""
        for record in self:
            record.total_instances = self.env['saas.instance'].search_count([])
            record.active_instances = self.env['saas.instance'].search_count([('state', '=', 'running')])
            record.active_users = sum(self.env['saas.instance'].search([('state', '=', 'running')]).mapped('active_user_count'))
            record.mrr = sum(self.env['saas.subscription'].search([('state', '=', 'active')]).mapped('price')) 