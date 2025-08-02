# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import os
import time
from ..models import docker_utils
from ..models import db_utils
from ..models import ssh_utils

class SaasBackupRestoreWizard(models.TransientModel):
    _name = 'saas.backup.restore.wizard'
    _description = 'SaaS Backup and Restore Wizard'

    operation_type = fields.Selection([
        ('backup', 'Create Backup'),
        ('restore', 'Restore from Backup'),
    ], string='Operation Type', required=True, default='backup')
    
    instance_id = fields.Many2one('saas.instance', string='Instance', required=True)
    backup_type = fields.Selection([
        ('database', 'Database Only'),
        ('container', 'Container Data'),
        ('full', 'Full Backup (Database + Container)'),
    ], string='Backup Type', default='full')
    
    # Backup options
    include_logs = fields.Boolean(string='Include Logs', default=True)
    compression = fields.Boolean(string='Compress Backup', default=True)
    backup_notes = fields.Text(string='Backup Notes')
    
    # Restore options
    backup_file = fields.Binary(string='Backup File')
    backup_filename = fields.Char(string='Backup Filename')
    restore_path = fields.Char(string='Backup File Path', 
                              help="Path to backup file on server (for server-side backups)")
    overwrite_existing = fields.Boolean(string='Overwrite Existing Data', default=False)
    
    # Progress tracking
    progress = fields.Float(string='Progress', default=0.0)
    status_message = fields.Text(string='Status Message', readonly=True)

    @api.onchange('operation_type')
    def _onchange_operation_type(self):
        """Reset fields based on operation type."""
        if self.operation_type == 'backup':
            self.backup_file = False
            self.backup_filename = False
            self.restore_path = False
        else:
            self.backup_type = False
            self.include_logs = False
            self.compression = False
            self.backup_notes = False

    @api.onchange('instance_id')
    def _onchange_instance_id(self):
        """Update status message based on instance."""
        if self.instance_id:
            if self.operation_type == 'backup':
                self.status_message = f"Ready to backup instance: {self.instance_id.name}"
            else:
                self.status_message = f"Ready to restore instance: {self.instance_id.name}"

    def action_execute_operation(self):
        """Execute the backup or restore operation."""
        self.ensure_one()
        
        if self.operation_type == 'backup':
            return self._execute_backup()
        else:
            return self._execute_restore()

    def _execute_backup(self):
        """Execute backup operation."""
        try:
            self.progress = 10.0
            self.status_message = "Starting backup process..."
            
            # Validate instance
            if not self.instance_id or self.instance_id.state != 'running':
                raise UserError(_("Instance must be running to create a backup"))
            
            # Create backup directory
            backup_dir = f"/backups/{self.instance_id.db_name}"
            ssh_client = ssh_utils.get_ssh_client(self.instance_id.server_id)
            if not ssh_client:
                raise UserError(_("Failed to connect to server"))
            
            ssh_utils.create_remote_directory(ssh_client, backup_dir)
            self.progress = 20.0
            self.status_message = "Backup directory created..."
            
            timestamp = int(time.time())
            backup_files = []
            
            # Database backup
            if self.backup_type in ['database', 'full']:
                self.status_message = "Creating database backup..."
                db_backup_path = f"{backup_dir}/db_backup_{timestamp}.sql"
                
                if db_utils.backup_database(self.instance_id.server_id, self.instance_id.db_name, db_backup_path):
                    backup_files.append(db_backup_path)
                    self.progress = 50.0
                else:
                    raise UserError(_("Failed to create database backup"))
            
            # Container backup
            if self.backup_type in ['container', 'full']:
                self.status_message = "Creating container backup..."
                container_backup_path = f"{backup_dir}/container_backup_{timestamp}.tar"
                
                if docker_utils.backup_container_data(self.instance_id.server_id, self.instance_id):
                    backup_files.append(container_backup_path)
                    self.progress = 70.0
                else:
                    raise UserError(_("Failed to create container backup"))
            
            # Include logs if requested
            if self.include_logs and self.backup_type in ['container', 'full']:
                self.status_message = "Including log files..."
                log_backup_path = f"{backup_dir}/logs_backup_{timestamp}.tar"
                command = f"tar -czf {log_backup_path} /var/log/odoo/{self.instance_id.db_name}"
                success, output = ssh_utils.execute_ssh_command(ssh_client, command)
                if success:
                    backup_files.append(log_backup_path)
            
            # Create backup manifest
            self.status_message = "Creating backup manifest..."
            manifest_path = f"{backup_dir}/backup_manifest_{timestamp}.json"
            manifest_content = {
                'instance_id': self.instance_id.id,
                'instance_name': self.instance_id.name,
                'backup_type': self.backup_type,
                'timestamp': timestamp,
                'backup_files': backup_files,
                'notes': self.backup_notes,
                'odoo_version': self.instance_id.odoo_version,
                'created_by': self.env.user.name,
            }
            
            # Write manifest
            import json
            manifest_json = json.dumps(manifest_content, indent=2)
            success, output = ssh_utils.execute_ssh_command(
                ssh_client, 
                f"echo '{manifest_json}' > {manifest_path}"
            )
            
            if success:
                backup_files.append(manifest_path)
                self.progress = 90.0
                self.status_message = "Backup manifest created..."
            
            # Compress if requested
            if self.compression and len(backup_files) > 1:
                self.status_message = "Compressing backup files..."
                final_backup_path = f"{backup_dir}/full_backup_{timestamp}.tar.gz"
                files_list = " ".join(backup_files)
                command = f"tar -czf {final_backup_path} -C {backup_dir} {files_list}"
                success, output = ssh_utils.execute_ssh_command(ssh_client, command)
                
                if success:
                    # Clean up individual files
                    for file_path in backup_files:
                        ssh_utils.execute_ssh_command(ssh_client, f"rm -f {file_path}")
                    backup_files = [final_backup_path]
            
            ssh_utils.close_ssh_client(ssh_client)
            self.progress = 100.0
            self.status_message = f"Backup completed successfully! Files: {', '.join(backup_files)}"
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Backup Completed'),
                    'message': _('Backup created successfully for instance %s') % self.instance_id.name,
                    'type': 'success',
                }
            }
            
        except Exception as e:
            self.status_message = f"Backup failed: {str(e)}"
            raise UserError(_("Backup failed: %s") % str(e))

    def _execute_restore(self):
        """Execute restore operation."""
        try:
            self.progress = 10.0
            self.status_message = "Starting restore process..."
            
            # Validate instance
            if not self.instance_id:
                raise UserError(_("Please select an instance to restore"))
            
            # Stop instance if running
            if self.instance_id.state == 'running':
                self.status_message = "Stopping instance..."
                self.instance_id.action_suspend_instance()
                self.progress = 20.0
            
            # Determine backup file path
            if self.backup_file and self.backup_filename:
                # Upload file to server
                self.status_message = "Uploading backup file..."
                ssh_client = ssh_utils.get_ssh_client(self.instance_id.server_id)
                if not ssh_client:
                    raise UserError(_("Failed to connect to server"))
                
                # Save uploaded file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(self.backup_file)
                    tmp_file_path = tmp_file.name
                
                remote_path = f"/backups/{self.backup_filename}"
                success, message = ssh_utils.upload_file_via_ssh(ssh_client, tmp_file_path, remote_path)
                os.unlink(tmp_file_path)  # Clean up temp file
                
                if not success:
                    raise UserError(_("Failed to upload backup file: %s") % message)
                
                backup_path = remote_path
                self.progress = 30.0
                
            elif self.restore_path:
                backup_path = self.restore_path
                ssh_client = ssh_utils.get_ssh_client(self.instance_id.server_id)
                if not ssh_client:
                    raise UserError(_("Failed to connect to server"))
            else:
                raise UserError(_("Please provide either a backup file or backup path"))
            
            # Check if backup file exists
            if not ssh_utils.check_remote_file_exists(ssh_client, backup_path):
                raise UserError(_("Backup file not found: %s") % backup_path)
            
            # Extract if compressed
            self.status_message = "Preparing backup files..."
            if backup_path.endswith('.tar.gz') or backup_path.endswith('.tgz'):
                extract_dir = f"/tmp/backup_extract_{int(time.time())}"
                ssh_utils.create_remote_directory(ssh_client, extract_dir)
                command = f"tar -xzf {backup_path} -C {extract_dir}"
                success, output = ssh_utils.execute_ssh_command(ssh_client, command)
                if not success:
                    raise UserError(_("Failed to extract backup file"))
                backup_path = extract_dir
            
            self.progress = 40.0
            
            # Restore database
            self.status_message = "Restoring database..."
            db_backup_file = None
            
            # Find database backup file
            success, output = ssh_utils.execute_ssh_command(ssh_client, f"find {backup_path} -name '*db_backup*.sql'")
            if success and output.strip():
                db_backup_file = output.strip().split('\n')[0]
            
            if db_backup_file:
                if self.overwrite_existing:
                    # Drop existing database
                    db_utils.drop_database_via_ssh(self.instance_id.server_id, self.instance_id.db_name)
                
                # Create new database and restore
                db_utils.create_database_via_ssh(self.instance_id.server_id, self.instance_id.db_name)
                success, output = ssh_utils.execute_ssh_command(
                    ssh_client, 
                    f"sudo -u postgres psql {self.instance_id.db_name} < {db_backup_file}"
                )
                
                if not success:
                    raise UserError(_("Failed to restore database: %s") % output)
                
                self.progress = 70.0
                self.status_message = "Database restored successfully..."
            
            # Restore container data if needed
            container_backup_file = None
            success, output = ssh_utils.execute_ssh_command(ssh_client, f"find {backup_path} -name '*container_backup*.tar'")
            if success and output.strip():
                container_backup_file = output.strip().split('\n')[0]
                
                self.status_message = "Restoring container data..."
                command = f"docker import {container_backup_file} {self.instance_id.db_name}:backup"
                success, output = ssh_utils.execute_ssh_command(ssh_client, command)
                
                if success:
                    self.progress = 90.0
                    self.status_message = "Container data restored..."
            
            # Clean up
            if backup_path.startswith('/tmp/'):
                ssh_utils.execute_ssh_command(ssh_client, f"rm -rf {backup_path}")
            
            ssh_utils.close_ssh_client(ssh_client)
            
            # Start instance
            self.status_message = "Starting instance..."
            self.instance_id.action_resume_instance()
            
            self.progress = 100.0
            self.status_message = "Restore completed successfully!"
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Restore Completed'),
                    'message': _('Instance %s restored successfully!') % self.instance_id.name,
                    'type': 'success',
                }
            }
            
        except Exception as e:
            self.status_message = f"Restore failed: {str(e)}"
            raise UserError(_("Restore failed: %s") % str(e))

    def action_cancel(self):
        """Cancel the wizard."""
        return {
            'type': 'ir.actions.act_window_close'
        } 