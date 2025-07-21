# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..models import db_utils
import base64
import os

class SaasBackupRestoreWizard(models.TransientModel):
    _name = 'saas.backup.restore.wizard'
    _description = 'SaaS Backup/Restore Wizard'

    instance_id = fields.Many2one('saas.instance', string='Instance', required=True)
    backup_file = fields.Binary(string='Backup File', attachment=True)
    backup_file_name = fields.Char(string='Backup File Name')

    def action_backup_instance(self):
        self.ensure_one()
        backup_path = db_utils.backup_db(self.instance_id.db_name)
        if backup_path:
            with open(backup_path, 'rb') as f:
                self.backup_file = base64.b64encode(f.read())
            self.backup_file_name = f"{self.instance_id.db_name}.zip"
            os.remove(backup_path)
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'saas.backup.restore.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            raise UserError(_("Failed to create backup."))

    def action_restore_instance(self):
        self.ensure_one()
        if not self.backup_file:
            raise UserError(_("Please upload a backup file."))
        
        with open(self.backup_file_name, 'wb') as f:
            f.write(base64.b64decode(self.backup_file))
        
        if db_utils.restore_db(self.instance_id.db_name, self.backup_file_name):
            return {'type': 'ir.actions.act_window_close'}
        else:
            raise UserError(_("Failed to restore database.")) 