# -*- coding: utf-8 -*-
import odoo
from odoo.service import db
import logging
import os
import tempfile

_logger = logging.getLogger(__name__)

def backup_db(db_name):
    """Creates a backup of the specified database and returns the path to the backup file."""
    try:
        tmp_dir = tempfile.gettempdir()
        backup_path = os.path.join(tmp_dir, f"{db_name}.zip")
        with open(backup_path, 'wb') as backup_file:
            db.dump_db(db_name, backup_file)
        _logger.info(f"Successfully created backup for database '{db_name}' at '{backup_path}'")
        return backup_path
    except Exception as e:
        _logger.error(f"Failed to create backup for database '{db_name}': {e}")
        return False

def restore_db(db_name, backup_path):
    """Restores a database from the specified backup file."""
    try:
        db.restore_db(db_name, backup_path, copy=True)
        _logger.info(f"Successfully restored database '{db_name}' from '{backup_path}'")
        return True
    except Exception as e:
        _logger.error(f"Failed to restore database '{db_name}' from '{backup_path}': {e}")
        return False 