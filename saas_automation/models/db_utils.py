# -*- coding: utf-8 -*-
import logging
import time

_logger = logging.getLogger(__name__)

# Optional imports - handle gracefully if not available
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    _logger.warning("Psycopg2 package not installed. Install with: pip install psycopg2-binary")

from . import ssh_utils

def create_database(server, db_name):
    """Creates a new PostgreSQL database for the Odoo instance."""
    if not PSYCOPG2_AVAILABLE:
        _logger.error("Psycopg2 package not available. Cannot create database.")
        return False
        
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=server.host,
            port=5432,
            database='postgres',
            user='odoo',
            password='odoo'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if cursor.fetchone():
            _logger.warning(f"Database {db_name} already exists")
            return True
        
        # Create database
        cursor.execute(f"CREATE DATABASE {db_name}")
        _logger.info(f"Created database {db_name}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        _logger.error(f"Failed to create database {db_name}: {e}")
        return False

def create_database_via_ssh(server, db_name):
    """Creates a new PostgreSQL database via SSH."""
    try:
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return False
        
        # Create database using psql
        command = f"sudo -u postgres createdb {db_name}"
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success:
            _logger.info(f"Created database {db_name} via SSH")
            return True
        else:
            _logger.error(f"Failed to create database via SSH: {output}")
            return False
    except Exception as e:
        _logger.error(f"SSH database creation failed: {e}")
        return False

def drop_database(server, db_name):
    """Drops a PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=server.host,
            port=5432,
            database='postgres',
            user='odoo',
            password='odoo'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Terminate all connections to the database
        cursor.execute(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
        """)
        
        # Drop database
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        _logger.info(f"Dropped database {db_name}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        _logger.error(f"Failed to drop database {db_name}: {e}")
        return False

def drop_database_via_ssh(server, db_name):
    """Drops a PostgreSQL database via SSH."""
    try:
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return False
        
        # Drop database using psql
        command = f"sudo -u postgres dropdb {db_name}"
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success:
            _logger.info(f"Dropped database {db_name} via SSH")
            return True
        else:
            _logger.error(f"Failed to drop database via SSH: {output}")
            return False
    except Exception as e:
        _logger.error(f"SSH database drop failed: {e}")
        return False

def backup_database(server, db_name, backup_path=None):
    """Creates a backup of the database."""
    try:
        if not backup_path:
            backup_path = f"/backups/{db_name}_{int(time.time())}.sql"
        
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return False
        
        # Create backup using pg_dump
        command = f"sudo -u postgres pg_dump {db_name} > {backup_path}"
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success:
            _logger.info(f"Created database backup: {backup_path}")
            return True
        else:
            _logger.error(f"Failed to create database backup: {output}")
            return False
    except Exception as e:
        _logger.error(f"Database backup failed: {e}")
        return False

def restore_database(server, db_name, backup_path):
    """Restores a database from backup."""
    try:
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return False
        
        # Drop existing database if it exists
        drop_database_via_ssh(server, db_name)
        
        # Create new database
        create_database_via_ssh(server, db_name)
        
        # Restore from backup
        command = f"sudo -u postgres psql {db_name} < {backup_path}"
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success:
            _logger.info(f"Restored database {db_name} from {backup_path}")
            return True
        else:
            _logger.error(f"Failed to restore database: {output}")
            return False
    except Exception as e:
        _logger.error(f"Database restore failed: {e}")
        return False

def check_database_exists(server, db_name):
    """Checks if a database exists."""
    try:
        conn = psycopg2.connect(
            host=server.host,
            port=5432,
            database='postgres',
            user='odoo',
            password='odoo'
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        _logger.error(f"Failed to check database existence: {e}")
        return False

def get_database_size(server, db_name):
    """Gets the size of a database in bytes."""
    try:
        conn = psycopg2.connect(
            host=server.host,
            port=5432,
            database=db_name,
            user='odoo',
            password='odoo'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pg_database_size(%s)
        """, (db_name,))
        
        size = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return size
    except Exception as e:
        _logger.error(f"Failed to get database size: {e}")
        return 0

def get_database_tables(server, db_name):
    """Gets list of tables in the database."""
    try:
        conn = psycopg2.connect(
            host=server.host,
            port=5432,
            database=db_name,
            user='odoo',
            password='odoo'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return tables
    except Exception as e:
        _logger.error(f"Failed to get database tables: {e}")
        return []

def optimize_database(server, db_name):
    """Optimizes the database by running VACUUM and ANALYZE."""
    try:
        conn = psycopg2.connect(
            host=server.host,
            port=5432,
            database=db_name,
            user='odoo',
            password='odoo'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Run VACUUM
        cursor.execute("VACUUM")
        _logger.info(f"VACUUM completed for database {db_name}")
        
        # Run ANALYZE
        cursor.execute("ANALYZE")
        _logger.info(f"ANALYZE completed for database {db_name}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        _logger.error(f"Failed to optimize database {db_name}: {e}")
        return False 