# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import re

class SaasInstanceCreationWizard(models.TransientModel):
    _name = 'saas.instance.creation.wizard'
    _description = 'SaaS Instance Creation Wizard'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    plan_id = fields.Many2one('saas.plan', string='Plan', required=True)
    subdomain = fields.Char(string='Subdomain', required=True, help="Enter subdomain (e.g., 'mycompany' for mycompany.yourdomain.com)")
    server_id = fields.Many2one('saas.server', string='Server', required=True, 
                               domain=[('is_active', '=', True), ('connection_status', '=', 'connected')])
    odoo_version = fields.Selection([
        ('16.0', 'Odoo 16'),
        ('17.0', 'Odoo 17'),
        ('18.0', 'Odoo 18'),
    ], string='Odoo Version', required=True, default='18.0')
    custom_domain = fields.Char(string='Custom Domain (Optional)', 
                               help="Enter custom domain (e.g., 'mycompany.com')")
    is_trial = fields.Boolean(string='Trial Instance', default=False)
    notes = fields.Text(string='Notes')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Set default subdomain based on partner name."""
        if self.partner_id and not self.subdomain:
            # Create a clean subdomain from partner name
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', self.partner_id.name.lower())
            self.subdomain = clean_name[:20]  # Limit to 20 characters

    @api.onchange('server_id')
    def _onchange_server_id(self):
        """Check server availability."""
        if self.server_id and not self.server_id.can_host_instance():
            return {
                'warning': {
                    'title': _('Server Unavailable'),
                    'message': _('Selected server cannot host new instances. Please choose another server.')
                }
            }

    @api.constrains('subdomain')
    def _check_subdomain(self):
        """Validate subdomain format."""
        for wizard in self:
            if wizard.subdomain:
                # Check if subdomain is valid
                if not re.match(r'^[a-z0-9-]+$', wizard.subdomain):
                    raise ValidationError(_("Subdomain can only contain lowercase letters, numbers, and hyphens"))
                
                if len(wizard.subdomain) < 3:
                    raise ValidationError(_("Subdomain must be at least 3 characters long"))
                
                if len(wizard.subdomain) > 63:
                    raise ValidationError(_("Subdomain cannot exceed 63 characters"))
                
                # Check if subdomain already exists
                existing_instance = self.env['saas.instance'].search([
                    ('subdomain', '=', wizard.subdomain)
                ], limit=1)
                
                if existing_instance:
                    raise ValidationError(_("Subdomain '%s' is already in use") % wizard.subdomain)

    @api.constrains('custom_domain')
    def _check_custom_domain(self):
        """Validate custom domain format."""
        for wizard in self:
            if wizard.custom_domain:
                # Basic domain validation
                domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
                if not re.match(domain_pattern, wizard.custom_domain):
                    raise ValidationError(_("Invalid custom domain format"))

    def action_create_instance(self):
        """Create the SaaS instance."""
        self.ensure_one()
        
        # Validate server availability
        if not self.server_id.can_host_instance():
            raise UserError(_("Selected server cannot host new instances. Please choose another server."))
        
        # Generate database name
        db_name = self._generate_db_name()
        
        # Check if database name already exists
        if self.env['saas.instance'].search([('db_name', '=', db_name)], limit=1):
            raise UserError(_("Database name '%s' already exists. Please try a different subdomain.") % db_name)
        
        try:
            # Create instance
            instance_vals = {
                'partner_id': self.partner_id.id,
                'plan_id': self.plan_id.id,
                'server_id': self.server_id.id,
                'subdomain': self.subdomain,
                'db_name': db_name,
                'odoo_version': self.odoo_version,
                'custom_domain': self.custom_domain,
                'is_trial': self.is_trial,
                'notes': self.notes,
                'state': 'draft',
            }
            
            instance = self.env['saas.instance'].create(instance_vals)
            
            # Create subscription if plan is provided
            if self.plan_id:
                subscription_vals = {
                    'partner_id': self.partner_id.id,
                    'instance_id': instance.id,
                    'plan_id': self.plan_id.id,
                    'start_date': fields.Date.today(),
                    'price': self.plan_id.price_monthly if not self.is_trial else 0.0,
                    'state': 'draft',
                }
                self.env['saas.subscription'].create(subscription_vals)
            
            # Return to instance form
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'saas.instance',
                'res_id': instance.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {'default_partner_id': self.partner_id.id},
            }
            
        except Exception as e:
            raise UserError(_("Failed to create instance: %s") % str(e))

    def _generate_db_name(self):
        """Generate a unique database name."""
        base_name = f"{self.subdomain.replace('.', '-')}-{self.plan_id.name.lower().replace(' ', '-')}"
        base_name = re.sub(r'[^a-zA-Z0-9-]', '', base_name)
        
        # Ensure database name is unique
        db_name = base_name
        counter = 1
        while self.env['saas.instance'].search([('db_name', '=', db_name)], limit=1):
            db_name = f"{base_name}-{counter}"
            counter += 1
        
        return db_name

    def action_deploy_instance(self):
        """Create and deploy the instance."""
        self.ensure_one()
        
        # First create the instance
        result = self.action_create_instance()
        
        if result and result.get('res_id'):
            instance = self.env['saas.instance'].browse(result['res_id'])
            
            # Deploy the instance
            try:
                instance.action_deploy_instance()
                
                # Activate subscription if not trial
                if not self.is_trial and instance.subscription_ids:
                    instance.subscription_ids[0].action_activate_subscription()
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Instance Deployed'),
                        'message': _('Instance "%s" has been successfully deployed!') % instance.name,
                        'type': 'success',
                    }
                }
                
            except Exception as e:
                raise UserError(_("Failed to deploy instance: %s") % str(e))
        
        return result 