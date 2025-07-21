# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from . import docker_utils
from . import nginx_utils

class SaasInstance(models.Model):
    _name = 'saas.instance'
    _description = 'SaaS Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Instance Name', required=True, tracking=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    subdomain = fields.Char(string='Subdomain', required=True, tracking=True)
    domain = fields.Char(string='Domain', tracking=True)
    url = fields.Char(string='URL', compute='_compute_url', store=True)
    db_name = fields.Char(string='Database Name', required=True, tracking=True)
    odoo_version = fields.Selection([
        ('16.0', 'Odoo 16'),
        ('17.0', 'Odoo 17'),
        ('18.0', 'Odoo 18'),
    ], string='Odoo Version', required=True, default='18.0', tracking=True)
    server_id = fields.Many2one('saas.server', string='Server', required=True, tracking=True)
    plan_id = fields.Many2one('saas.plan', string='Subscription Plan', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('deploying', 'Deploying'),
        ('running', 'Running'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    active_user_count = fields.Integer(string='Active Users', default=1, tracking=True)
    expiration_date = fields.Date(string='Expiration Date', tracking=True)
    is_trial = fields.Boolean(string='Trial', default=False, tracking=True)
    custom_domain = fields.Char(string='Custom Domain', tracking=True)
    is_custom_domain_active = fields.Boolean(string='Custom Domain Active', default=False, tracking=True)
    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('saas.instance') or _('New')
        result = super(SaasInstance, self).create(vals)
        return result

    @api.depends('subdomain', 'domain', 'custom_domain', 'is_custom_domain_active')
    def _compute_url(self):
        for rec in self:
            if rec.is_custom_domain_active and rec.custom_domain:
                rec.url = f"https://{rec.custom_domain}"
            elif rec.domain:
                rec.url = f"https://{rec.subdomain}.{rec.domain}"
            else:
                rec.url = False

    def action_activate_custom_domain(self):
        self.write({'is_custom_domain_active': True})
        nginx_utils.create_nginx_config(self.server_id, self)

    def action_deactivate_custom_domain(self):
        self.write({'is_custom_domain_active': False})
        nginx_utils.remove_nginx_config(self.server_id, self)

    def action_deploy_instance(self):
        self.write({'state': 'deploying'})
        docker_utils.create_odoo_container(self.server_id, self)
        self.write({'state': 'running'})

    def action_suspend_instance(self):
        self.write({'state': 'suspended'})
        docker_utils.stop_odoo_container(self.server_id, self)

    def action_resume_instance(self):
        self.write({'state': 'running'})
        docker_utils.start_odoo_container(self.server_id, self)

    def action_cancel_instance(self):
        self.write({'state': 'cancelled'})
        docker_utils.remove_odoo_container(self.server_id, self) 