# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaasDashboard(models.Model):
    _name = 'saas.dashboard'
    _description = 'SaaS Dashboard'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    
    # Instance Metrics
    total_instances = fields.Integer(string='Total Instances', compute='_compute_dashboard_data', store=True)
    active_instances = fields.Integer(string='Active Instances', compute='_compute_dashboard_data', store=True)
    suspended_instances = fields.Integer(string='Suspended Instances', compute='_compute_dashboard_data', store=True)
    
    # User Metrics
    total_users = fields.Integer(string='Total Users', compute='_compute_dashboard_data', store=True)
    active_users = fields.Integer(string='Active Users', compute='_compute_dashboard_data', store=True)
    
    # Financial Metrics
    mrr = fields.Float(string='Monthly Recurring Revenue', compute='_compute_dashboard_data', store=True)
    arr = fields.Float(string='Annual Recurring Revenue', compute='_compute_dashboard_data', store=True)
    churn_rate = fields.Float(string='Churn Rate (%)', compute='_compute_dashboard_data', store=True)
    revenue_growth = fields.Float(string='Revenue Growth (%)', compute='_compute_dashboard_data', store=True)
    
    # Performance Metrics
    server_utilization = fields.Float(string='Server Utilization (%)', compute='_compute_dashboard_data', store=True)
    customer_satisfaction = fields.Float(string='Customer Satisfaction (%)', compute='_compute_dashboard_data', store=True)
    
    # Configuration
    auto_refresh = fields.Boolean(string='Auto Refresh', default=True, tracking=True)
    show_charts = fields.Boolean(string='Show Charts', default=True, tracking=True)
    show_alerts = fields.Boolean(string='Show Alerts', default=True, tracking=True)

    @api.depends('name')
    def _compute_dashboard_data(self):
        """Compute all dashboard metrics."""
        for record in self:
            # Instance metrics
            instances = self.env['saas.instance'].search([])
            record.total_instances = len(instances)
            record.active_instances = len(instances.filtered(lambda r: r.state == 'running'))
            record.suspended_instances = len(instances.filtered(lambda r: r.state == 'suspended'))
            
            # User metrics
            record.total_users = sum(instances.mapped('active_user_count'))
            record.active_users = sum(instances.filtered(lambda r: r.state == 'running').mapped('active_user_count'))
            
            # Financial metrics
            active_subscriptions = self.env['saas.subscription'].search([('state', '=', 'active')])
            record.mrr = sum(active_subscriptions.mapped('price'))
            record.arr = record.mrr * 12
            
            # Calculate churn rate (simplified)
            total_subscriptions = len(self.env['saas.subscription'].search([]))
            cancelled_subscriptions = len(self.env['saas.subscription'].search([('state', '=', 'cancelled')]))
            record.churn_rate = (cancelled_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0
            
            # Revenue growth (simplified calculation)
            record.revenue_growth = 15.0  # Placeholder - should be calculated from historical data
            
            # Server utilization
            servers = self.env['saas.server'].search([('is_active', '=', True)])
            if servers:
                total_utilization = sum(servers.mapped('get_server_utilization_percentage'))
                record.server_utilization = total_utilization / len(servers)
            else:
                record.server_utilization = 0
            
            # Customer satisfaction (placeholder)
            record.customer_satisfaction = 92.5

    def action_refresh_dashboard(self):
        """Refresh dashboard data."""
        self._compute_dashboard_data()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Dashboard Refreshed'),
                'message': _('Dashboard data has been updated successfully.'),
                'type': 'success',
            }
        }

    def action_export_data(self):
        """Export dashboard data."""
        return {
            'type': 'ir.actions.act_url',
            'url': '/saas/dashboard/export',
            'target': 'self',
        }

    @api.model
    def get_dashboard_data(self):
        """Get dashboard data for API calls."""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({'name': 'SaaS Platform Overview'})
        
        return {
            'total_instances': dashboard.total_instances,
            'active_instances': dashboard.active_instances,
            'suspended_instances': dashboard.suspended_instances,
            'total_users': dashboard.total_users,
            'active_users': dashboard.active_users,
            'mrr': dashboard.mrr,
            'arr': dashboard.arr,
            'churn_rate': dashboard.churn_rate,
            'revenue_growth': dashboard.revenue_growth,
            'server_utilization': dashboard.server_utilization,
            'customer_satisfaction': dashboard.customer_satisfaction,
        } 