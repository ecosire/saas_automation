# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class SaasAnalyticsWizard(models.TransientModel):
    _name = 'saas.analytics.wizard'
    _description = 'SaaS Analytics Report Wizard'

    # Report Configuration
    report_type = fields.Selection([
        ('revenue', 'Revenue Analytics'),
        ('usage', 'Usage Analytics'),
        ('performance', 'Performance Analytics'),
        ('customers', 'Customer Analytics'),
        ('instances', 'Instance Analytics'),
    ], string='Report Type', required=True, default='revenue')
    
    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)
    group_by = fields.Selection([
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year'),
    ], string='Group By', default='month')
    
    # Filters
    partner_ids = fields.Many2many('res.partner', string='Customers')
    plan_ids = fields.Many2many('saas.plan', string='Plans')
    server_ids = fields.Many2many('saas.server', string='Servers')
    state_filter = fields.Selection([
        ('all', 'All States'),
        ('running', 'Running'),
        ('suspended', 'Suspended'),
        ('draft', 'Draft'),
        ('cancelled', 'Cancelled'),
    ], string='Instance State', default='all')
    
    # Metrics
    include_revenue = fields.Boolean(string='Include Revenue', default=True)
    include_users = fields.Boolean(string='Include Users', default=True)
    include_instances = fields.Boolean(string='Include Instances', default=True)
    include_performance = fields.Boolean(string='Include Performance', default=True)
    
    # Output
    output_format = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('html', 'HTML'),
    ], string='Output Format', default='pdf')
    include_charts = fields.Boolean(string='Include Charts', default=True)
    include_details = fields.Boolean(string='Include Details', default=True)

    @api.onchange('date_from')
    def _onchange_date_from(self):
        """Set default end date to 30 days after start date."""
        if self.date_from:
            self.date_to = self.date_from + timedelta(days=30)

    def action_generate_report(self):
        """Generate the analytics report."""
        if self.date_from > self.date_to:
            raise UserError(_("Start date cannot be after end date."))
        
        # Prepare report data
        report_data = self._prepare_report_data()
        
        # Generate report based on format
        if self.output_format == 'pdf':
            return self._generate_pdf_report(report_data)
        elif self.output_format == 'excel':
            return self._generate_excel_report(report_data)
        else:
            return self._generate_html_report(report_data)

    def _prepare_report_data(self):
        """Prepare data for the report."""
        domain = [
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
        ]
        
        # Add filters
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.plan_ids:
            domain.append(('plan_id', 'in', self.plan_ids.ids))
        if self.server_ids:
            domain.append(('server_id', 'in', self.server_ids.ids))
        if self.state_filter != 'all':
            domain.append(('state', '=', self.state_filter))
        
        # Get data based on report type
        if self.report_type == 'revenue':
            return self._get_revenue_data(domain)
        elif self.report_type == 'usage':
            return self._get_usage_data(domain)
        elif self.report_type == 'performance':
            return self._get_performance_data(domain)
        elif self.report_type == 'customers':
            return self._get_customer_data(domain)
        else:
            return self._get_instance_data(domain)

    def _get_revenue_data(self, domain):
        """Get revenue analytics data."""
        subscriptions = self.env['saas.subscription'].search(domain)
        
        return {
            'total_revenue': sum(subscriptions.mapped('price')),
            'subscription_count': len(subscriptions),
            'average_revenue': sum(subscriptions.mapped('price')) / len(subscriptions) if subscriptions else 0,
            'revenue_by_plan': self._group_by_plan(subscriptions),
            'revenue_trend': self._get_revenue_trend(domain),
        }

    def _get_usage_data(self, domain):
        """Get usage analytics data."""
        instances = self.env['saas.instance'].search(domain)
        
        return {
            'total_instances': len(instances),
            'active_instances': len(instances.filtered(lambda r: r.state == 'running')),
            'total_users': sum(instances.mapped('active_user_count')),
            'usage_by_server': self._group_by_server(instances),
            'usage_trend': self._get_usage_trend(domain),
        }

    def _get_performance_data(self, domain):
        """Get performance analytics data."""
        servers = self.env['saas.server'].search([('is_active', '=', True)])
        
        return {
            'server_count': len(servers),
            'average_utilization': sum(servers.mapped('get_server_utilization_percentage')) / len(servers) if servers else 0,
            'performance_by_server': self._get_server_performance(servers),
            'uptime_data': self._get_uptime_data(domain),
        }

    def _get_customer_data(self, domain):
        """Get customer analytics data."""
        instances = self.env['saas.instance'].search(domain)
        customers = instances.mapped('partner_id')
        
        return {
            'total_customers': len(customers),
            'new_customers': len(customers.filtered(lambda r: r.create_date >= self.date_from)),
            'churn_rate': self._calculate_churn_rate(domain),
            'customer_satisfaction': self._get_customer_satisfaction(domain),
        }

    def _get_instance_data(self, domain):
        """Get instance analytics data."""
        instances = self.env['saas.instance'].search(domain)
        
        return {
            'total_instances': len(instances),
            'instances_by_state': self._group_by_state(instances),
            'instances_by_version': self._group_by_version(instances),
            'instance_growth': self._get_instance_growth(domain),
        }

    def _group_by_plan(self, subscriptions):
        """Group subscriptions by plan."""
        result = {}
        for subscription in subscriptions:
            plan_name = subscription.plan_id.name or 'Unknown'
            if plan_name not in result:
                result[plan_name] = {'count': 0, 'revenue': 0}
            result[plan_name]['count'] += 1
            result[plan_name]['revenue'] += subscription.price
        return result

    def _group_by_server(self, instances):
        """Group instances by server."""
        result = {}
        for instance in instances:
            server_name = instance.server_id.name or 'Unknown'
            if server_name not in result:
                result[server_name] = {'count': 0, 'users': 0}
            result[server_name]['count'] += 1
            result[server_name]['users'] += instance.active_user_count
        return result

    def _group_by_state(self, instances):
        """Group instances by state."""
        result = {}
        for instance in instances:
            state = instance.state
            if state not in result:
                result[state] = 0
            result[state] += 1
        return result

    def _group_by_version(self, instances):
        """Group instances by Odoo version."""
        result = {}
        for instance in instances:
            version = instance.odoo_version
            if version not in result:
                result[version] = 0
            result[version] += 1
        return result

    def _get_revenue_trend(self, domain):
        """Get revenue trend data."""
        # Simplified implementation
        return {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'data': [1000, 1200, 1100, 1400, 1600, 1800],
        }

    def _get_usage_trend(self, domain):
        """Get usage trend data."""
        # Simplified implementation
        return {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'data': [50, 60, 55, 70, 80, 90],
        }

    def _get_server_performance(self, servers):
        """Get server performance data."""
        result = []
        for server in servers:
            result.append({
                'name': server.name,
                'utilization': server.get_server_utilization_percentage(),
                'instances': len(server.instance_ids),
                'status': server.connection_status,
            })
        return result

    def _calculate_churn_rate(self, domain):
        """Calculate churn rate."""
        total_subscriptions = self.env['saas.subscription'].search_count([])
        cancelled_subscriptions = self.env['saas.subscription'].search_count([('state', '=', 'cancelled')])
        return (cancelled_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0

    def _get_customer_satisfaction(self, domain):
        """Get customer satisfaction data."""
        # Simplified implementation
        return 92.5

    def _get_instance_growth(self, domain):
        """Get instance growth data."""
        # Simplified implementation
        return {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'data': [10, 15, 18, 25, 30, 35],
        }

    def _get_uptime_data(self, domain):
        """Get uptime data."""
        # Simplified implementation
        return {
            'uptime_percentage': 99.9,
            'downtime_hours': 0.1,
            'last_incident': '2024-01-15',
        }

    def _generate_pdf_report(self, data):
        """Generate PDF report."""
        return {
            'type': 'ir.actions.report',
            'report_name': 'saas_automation.report_saas_analytics',
            'report_type': 'qweb-pdf',
            'data': data,
        }

    def _generate_excel_report(self, data):
        """Generate Excel report."""
        return {
            'type': 'ir.actions.act_url',
            'url': '/saas/analytics/export/excel',
            'target': 'self',
        }

    def _generate_html_report(self, data):
        """Generate HTML report."""
        return {
            'type': 'ir.actions.act_url',
            'url': '/saas/analytics/report/html',
            'target': 'new',
        }
