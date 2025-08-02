# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from . import ssh_utils

class SaasServer(models.Model):
    _name = 'saas.server'
    _description = 'SaaS Server'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Server Name', required=True, tracking=True)
    server_type = fields.Selection([
        ('docker', 'Docker'),
        ('kubernetes', 'Kubernetes'),
        ('vm', 'Virtual Machine'),
        ('baremetal', 'Bare Metal'),
    ], string='Server Type', required=True, default='docker', tracking=True)
    host = fields.Char(string='Host Address', required=True, tracking=True)
    port = fields.Integer(string='SSH Port', default=22, tracking=True)
    ssh_user = fields.Char(string='SSH User', required=True, tracking=True)
    ssh_password = fields.Char(string='SSH Password', tracking=True)
    ssh_private_key_path = fields.Char(string='SSH Private Key Path', tracking=True, 
                                      help="Path to SSH private key file (e.g., ~/.ssh/id_rsa)")
    max_clients = fields.Integer(string='Max Instances', default=10, tracking=True)
    is_active = fields.Boolean(string='Active', default=True, tracking=True)
    connection_status = fields.Selection([
        ('unknown', 'Unknown'),
        ('connected', 'Connected'),
        ('failed', 'Connection Failed'),
    ], string='Connection Status', default='unknown', tracking=True)
    last_connection_test = fields.Datetime(string='Last Connection Test', tracking=True)
    notes = fields.Text(string='Notes')
    
    # Relationship fields
    instance_ids = fields.One2many('saas.instance', 'server_id', string='Instances')
    
    # Computed fields with proper dependencies
    total_clients = fields.Integer(string='Total Instances', compute='_compute_total_clients', store=True)
    available_slots = fields.Integer(string='Available Slots', compute='_compute_available_slots', store=True)
    
    # Server information fields
    os_info = fields.Text(string='Operating System', readonly=True)
    memory_info = fields.Text(string='Memory Info', readonly=True)
    disk_info = fields.Text(string='Disk Info', readonly=True)
    docker_info = fields.Text(string='Docker Info', readonly=True)

    @api.model
    def create(self, vals):
        """Override create to set default values and test connection."""
        result = super(SaasServer, self).create(vals)
        if result.is_active:
            result.test_connection()
        return result

    @api.depends('instance_ids.state')
    def _compute_total_clients(self):
        """Compute total number of active instances on this server."""
        for server in self:
            server.total_clients = len(server.instance_ids.filtered(lambda r: r.state in ['running', 'deploying']))

    @api.depends('max_clients', 'total_clients')
    def _compute_available_slots(self):
        """Compute available slots for new instances."""
        for server in self:
            server.available_slots = max(0, server.max_clients - server.total_clients)

    @api.constrains('host', 'port')
    def _check_host_port(self):
        """Validate host and port configuration."""
        for server in self:
            if server.host:
                # Basic host validation
                if not server.host.strip():
                    raise ValidationError(_("Host address cannot be empty"))
            
            if server.port:
                # Port validation
                if not (1 <= server.port <= 65535):
                    raise ValidationError(_("Port must be between 1 and 65535"))

    @api.constrains('ssh_user')
    def _check_ssh_user(self):
        """Validate SSH user configuration."""
        for server in self:
            if server.ssh_user and not server.ssh_user.strip():
                raise ValidationError(_("SSH user cannot be empty"))

    def test_connection(self):
        """Test SSH connection to the server."""
        for server in self:
            try:
                success, message = ssh_utils.test_ssh_connection(server)
                if success:
                    server.write({
                        'connection_status': 'connected',
                        'last_connection_test': fields.Datetime.now(),
                    })
                    # Get server information
                    server_info = ssh_utils.get_server_info(server)
                    if server_info:
                        server.write({
                            'os_info': server_info.get('os', ''),
                            'memory_info': server_info.get('memory', ''),
                            'disk_info': server_info.get('disk', ''),
                            'docker_info': server_info.get('docker', ''),
                        })
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Connection Test'),
                            'message': _('SSH connection successful!'),
                            'type': 'success',
                        }
                    }
                else:
                    server.write({
                        'connection_status': 'failed',
                        'last_connection_test': fields.Datetime.now(),
                    })
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Connection Test'),
                            'message': _('SSH connection failed: %s') % message,
                            'type': 'danger',
                        }
                    }
            except Exception as e:
                server.write({
                    'connection_status': 'failed',
                    'last_connection_test': fields.Datetime.now(),
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Test'),
                        'message': _('Connection test error: %s') % str(e),
                        'type': 'danger',
                    }
                }

    def action_refresh_server_info(self):
        """Refresh server information."""
        for server in self:
            server_info = ssh_utils.get_server_info(server)
            if server_info:
                server.write({
                    'os_info': server_info.get('os', ''),
                    'memory_info': server_info.get('memory', ''),
                    'disk_info': server_info.get('disk', ''),
                    'docker_info': server_info.get('docker', ''),
                })

    def get_available_server(self):
        """Get an available server with free slots."""
        return self.search([
            ('is_active', '=', True),
            ('connection_status', '=', 'connected'),
        ], order='available_slots desc', limit=1).filtered(lambda r: r.available_slots > 0)

    def can_host_instance(self):
        """Check if server can host a new instance."""
        return self.is_active and self.connection_status == 'connected' and self.available_slots > 0

    def get_running_instances(self):
        """Get all running instances on this server."""
        return self.instance_ids.filtered(lambda r: r.state == 'running')

    def get_instance_count_by_state(self, state):
        """Get count of instances by state."""
        return len(self.instance_ids.filtered(lambda r: r.state == state))

    def get_server_utilization_percentage(self):
        """Get server utilization percentage."""
        if self.max_clients == 0:
            return 0
        return (self.total_clients / self.max_clients) * 100

    @api.model
    def get_least_utilized_server(self):
        """Get the server with the lowest utilization percentage."""
        servers = self.search([
            ('is_active', '=', True),
            ('connection_status', '=', 'connected'),
        ])
        if not servers:
            return False
        return min(servers, key=lambda s: s.get_server_utilization_percentage())

    @api.model
    def assign_instance_to_best_server(self, instance_vals):
        """Assign a new instance to the best available server."""
        # First try to get a server with available slots
        available_server = self.get_available_server()
        if available_server:
            instance_vals['server_id'] = available_server.id
            return available_server
        
        # If no server with available slots, get the least utilized server
        least_utilized = self.get_least_utilized_server()
        if least_utilized:
            instance_vals['server_id'] = least_utilized.id
            return least_utilized
        
        return False

    def action_recompute_available_slots(self):
        """Manually recompute available slots for all servers."""
        for server in self:
            server._compute_total_clients()
            server._compute_available_slots() 