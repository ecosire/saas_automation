# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

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
    port = fields.Integer(string='Port', default=22, tracking=True)
    ssh_user = fields.Char(string='SSH User', tracking=True)
    ssh_password = fields.Char(string='SSH Password', tracking=True)
    max_clients = fields.Integer(string='Max Instances', default=10, tracking=True)
    is_active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes')
    total_clients = fields.Integer(string='Total Instances', compute='_compute_total_clients', store=True)

    @api.depends('id')
    def _compute_total_clients(self):
        for server in self:
            server.total_clients = self.env['saas.instance'].sudo().search_count([('server_id', '=', server.id)]) 