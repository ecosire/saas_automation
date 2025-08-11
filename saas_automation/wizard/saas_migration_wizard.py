# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class SaasMigrationWizard(models.TransientModel):
    _name = 'saas.migration.wizard'
    _description = 'SaaS Instance Migration Wizard'

    # Migration Configuration
    migration_type = fields.Selection([
        ('version_upgrade', 'Version Upgrade'),
        ('server_migration', 'Server Migration'),
        ('plan_upgrade', 'Plan Upgrade'),
        ('backup_restore', 'Backup & Restore'),
    ], string='Migration Type', required=True, default='version_upgrade')
    
    source_version = fields.Selection([
        ('16.0', 'Odoo 16'),
        ('17.0', 'Odoo 17'),
        ('18.0', 'Odoo 18'),
    ], string='Source Version')
    
    target_version = fields.Selection([
        ('16.0', 'Odoo 16'),
        ('17.0', 'Odoo 17'),
        ('18.0', 'Odoo 18'),
    ], string='Target Version')
    
    migration_date = fields.Datetime(string='Migration Date', required=True, default=fields.Datetime.now)
    backup_before_migration = fields.Boolean(string='Backup Before Migration', default=True)
    
    # Instance Selection
    instance_ids = fields.Many2many('saas.instance', string='Instances')
    server_ids = fields.Many2many('saas.server', string='Servers')
    include_suspended = fields.Boolean(string='Include Suspended Instances', default=False)
    
    # Migration Options
    auto_backup = fields.Boolean(string='Auto Backup', default=True)
    validate_migration = fields.Boolean(string='Validate Migration', default=True)
    notify_customers = fields.Boolean(string='Notify Customers', default=True)
    rollback_on_failure = fields.Boolean(string='Rollback on Failure', default=True)
    
    # Advanced Settings
    maintenance_window_start = fields.Datetime(string='Maintenance Window Start')
    maintenance_window_end = fields.Datetime(string='Maintenance Window End')
    max_downtime_hours = fields.Float(string='Max Downtime (Hours)', default=2.0)
    parallel_migrations = fields.Integer(string='Parallel Migrations', default=1)
    
    # Migration Plan
    migration_plan_ids = fields.One2many('saas.migration.wizard.line', 'wizard_id', string='Migration Plan')

    @api.onchange('migration_type')
    def _onchange_migration_type(self):
        """Update fields based on migration type."""
        if self.migration_type == 'version_upgrade':
            self.source_version = '17.0'
            self.target_version = '18.0'
        elif self.migration_type == 'server_migration':
            self.source_version = False
            self.target_version = False

    @api.onchange('instance_ids', 'server_ids', 'include_suspended')
    def _onchange_instance_selection(self):
        """Generate migration plan when instances are selected."""
        self.migration_plan_ids = [(5, 0, 0)]  # Clear existing lines
        if self.instance_ids or self.server_ids:
            self._generate_migration_plan()

    def _generate_migration_plan(self):
        """Generate migration plan based on selection."""
        lines = []
        
        # Get instances to migrate
        instances = self.instance_ids
        if not instances and self.server_ids:
            domain = [('server_id', 'in', self.server_ids.ids)]
            if not self.include_suspended:
                domain.append(('state', '!=', 'suspended'))
            instances = self.env['saas.instance'].search(domain)
        
        for instance in instances:
            risk_level = self._calculate_risk_level(instance)
            estimated_duration = self._estimate_migration_duration(instance)
            
            lines.append((0, 0, {
                'instance_id': instance.id,
                'current_version': instance.odoo_version,
                'target_version': self.target_version or instance.odoo_version,
                'estimated_duration': estimated_duration,
                'risk_level': risk_level,
                'include_in_migration': True,
            }))
        
        self.migration_plan_ids = lines

    def _calculate_risk_level(self, instance):
        """Calculate migration risk level for an instance."""
        risk_factors = 0
        
        # Check instance state
        if instance.state == 'suspended':
            risk_factors += 1
        
        # Check user count
        if instance.active_user_count > 50:
            risk_factors += 2
        elif instance.active_user_count > 20:
            risk_factors += 1
        
        # Check custom domain
        if instance.is_custom_domain_active:
            risk_factors += 1
        
        # Determine risk level
        if risk_factors >= 3:
            return 'critical'
        elif risk_factors >= 2:
            return 'warning'
        else:
            return 'low'

    def _estimate_migration_duration(self, instance):
        """Estimate migration duration for an instance."""
        base_duration = 30  # 30 minutes base
        
        # Add time based on user count
        user_factor = instance.active_user_count * 0.5
        
        # Add time based on version difference
        version_factor = 0
        if self.source_version and self.target_version:
            source_major = int(self.source_version.split('.')[0])
            target_major = int(self.target_version.split('.')[0])
            version_factor = abs(target_major - source_major) * 15
        
        total_duration = base_duration + user_factor + version_factor
        return min(total_duration, 180)  # Cap at 3 hours

    def action_validate_migration(self):
        """Validate migration plan."""
        if not self.migration_plan_ids:
            raise UserError(_("No migration plan generated. Please select instances first."))
        
        # Check for critical risks
        critical_instances = self.migration_plan_ids.filtered(lambda l: l.risk_level == 'critical')
        if critical_instances:
            warning_msg = _("Warning: The following instances have critical risk levels:\n")
            for line in critical_instances:
                warning_msg += f"- {line.instance_id.name}\n"
            warning_msg += _("\nPlease review before proceeding.")
            raise UserError(warning_msg)
        
        # Check maintenance window
        if self.maintenance_window_start and self.maintenance_window_end:
            if self.maintenance_window_start >= self.maintenance_window_end:
                raise UserError(_("Maintenance window start must be before end time."))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Migration Validated'),
                'message': _('Migration plan has been validated successfully.'),
                'type': 'success',
            }
        }

    def action_start_migration(self):
        """Start the migration process."""
        if not self.migration_plan_ids:
            raise UserError(_("No migration plan available."))
        
        # Validate first
        self.action_validate_migration()
        
        # Start migration for each instance
        migrated_instances = []
        failed_instances = []
        
        for line in self.migration_plan_ids.filtered(lambda l: l.include_in_migration):
            try:
                success = self._migrate_instance(line.instance_id)
                if success:
                    migrated_instances.append(line.instance_id.name)
                else:
                    failed_instances.append(line.instance_id.name)
            except Exception as e:
                failed_instances.append(line.instance_id.name)
                _logger.error(f"Migration failed for {line.instance_id.name}: {e}")
        
        # Show results
        message = ""
        if migrated_instances:
            message += _("Successfully migrated: %s\n") % ", ".join(migrated_instances)
        if failed_instances:
            message += _("Failed to migrate: %s") % ", ".join(failed_instances)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Migration Complete'),
                'message': message,
                'type': 'success' if not failed_instances else 'warning',
            }
        }

    def _migrate_instance(self, instance):
        """Migrate a single instance."""
        try:
            # Create backup if requested
            if self.backup_before_migration:
                self._create_backup(instance)
            
            # Perform migration based on type
            if self.migration_type == 'version_upgrade':
                return self._upgrade_version(instance)
            elif self.migration_type == 'server_migration':
                return self._migrate_server(instance)
            elif self.migration_type == 'plan_upgrade':
                return self._upgrade_plan(instance)
            elif self.migration_type == 'backup_restore':
                return self._backup_restore(instance)
            
            return True
        except Exception as e:
            _logger.error(f"Migration failed for {instance.name}: {e}")
            return False

    def _create_backup(self, instance):
        """Create backup for an instance."""
        # This would integrate with the backup/restore functionality
        backup_wizard = self.env['saas.backup.restore.wizard'].create({
            'instance_id': instance.id,
            'backup_type': 'full',
            'description': f"Pre-migration backup for {instance.name}",
        })
        backup_wizard.action_create_backup()

    def _upgrade_version(self, instance):
        """Upgrade Odoo version for an instance."""
        # Update instance version
        instance.write({
            'odoo_version': self.target_version,
        })
        
        # Notify customer if requested
        if self.notify_customers:
            self._notify_customer(instance, 'version_upgrade')
        
        return True

    def _migrate_server(self, instance):
        """Migrate instance to a different server."""
        # This would involve moving the instance to a new server
        # For now, just update the server reference
        if self.server_ids:
            new_server = self.server_ids[0]
            instance.write({
                'server_id': new_server.id,
            })
        
        return True

    def _upgrade_plan(self, instance):
        """Upgrade instance plan."""
        # This would involve changing the subscription plan
        # For now, just update the plan reference
        return True

    def _backup_restore(self, instance):
        """Perform backup and restore operation."""
        # This would use the backup/restore functionality
        return True

    def _notify_customer(self, instance, migration_type):
        """Notify customer about migration."""
        try:
            template = self.env.ref('saas_automation.email_template_migration_notification')
            if template:
                template.send_mail(instance.id, force_send=True)
        except Exception as e:
            _logger.warning(f"Failed to send migration notification: {e}")


class SaasMigrationWizardLine(models.TransientModel):
    _name = 'saas.migration.wizard.line'
    _description = 'SaaS Migration Wizard Line'

    wizard_id = fields.Many2one('saas.migration.wizard', string='Wizard')
    instance_id = fields.Many2one('saas.instance', string='Instance', required=True)
    current_version = fields.Char(string='Current Version')
    target_version = fields.Char(string='Target Version')
    estimated_duration = fields.Float(string='Estimated Duration (minutes)')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ], string='Risk Level', default='low')
    include_in_migration = fields.Boolean(string='Include in Migration', default=True)
