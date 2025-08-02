# -*- coding: utf-8 -*-
import logging
import time

_logger = logging.getLogger(__name__)

# Optional imports - handle gracefully if not available
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    _logger.warning("Docker package not installed. Install with: pip install docker")

from . import ssh_utils
from . import db_utils

def get_docker_client(server):
    """Initializes and returns a Docker client connected to the specified server."""
    if not DOCKER_AVAILABLE:
        _logger.warning("Docker package not available. Using SSH fallback.")
        return None
        
    try:
        if server.server_type == 'docker':
            return docker.DockerClient(base_url=f"tcp://{server.host}:2375")
        elif server.server_type == 'kubernetes':
            # Kubernetes support is optional - return None for now
            _logger.warning("Kubernetes support is not implemented yet. Using SSH fallback.")
            return None
        else:
            return None
    except Exception as e:
        _logger.error(f"Failed to create Docker client for server {server.name}: {e}")
        return None

def create_odoo_container(server, instance):
    """Creates and starts a new Odoo container for the given instance on the specified server."""
    try:
        if server.server_type == 'docker':
            client = get_docker_client(server)
            if client:
                # Create database first
                db_utils.create_database(server, instance.db_name)
                
                # Create and start container
                container = client.containers.run(
                    image=f"odoo:{instance.odoo_version}",
                    name=instance.db_name,
                    detach=True,
                    environment={
                        'HOST': server.host,
                        'USER': 'odoo',
                        'PASSWORD': 'odoo',
                        'DB_HOST': server.host,
                        'DB_PORT': '5432',
                        'DB_NAME': instance.db_name,
                    },
                    ports={'8069/tcp': None},
                    volumes={
                        f'/var/lib/odoo/{instance.db_name}': {'bind': '/var/lib/odoo', 'mode': 'rw'},
                        f'/var/log/odoo/{instance.db_name}': {'bind': '/var/log/odoo', 'mode': 'rw'},
                    },
                    restart_policy={"Name": "unless-stopped"},
                )
                _logger.info(f"Created Odoo container {instance.db_name} on server {server.name}")
                return True
            else:
                # Fallback to SSH
                return _create_container_via_ssh(server, instance)
        else:
            return _create_container_via_ssh(server, instance)
    except Exception as e:
        _logger.error(f"Failed to create Odoo container {instance.db_name}: {e}")
        return False

def _create_container_via_ssh(server, instance):
    """Create container using SSH as fallback method."""
    try:
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return False
            
        # Create database
        db_utils.create_database_via_ssh(server, instance.db_name)
        
        # Create container
        command = f"""
        docker run -d \
            --name {instance.db_name} \
            -p 8069:8069 \
            -e HOST={server.host} \
            -e USER=odoo \
            -e PASSWORD=odoo \
            -e DB_HOST={server.host} \
            -e DB_PORT=5432 \
            -e DB_NAME={instance.db_name} \
            -v /var/lib/odoo/{instance.db_name}:/var/lib/odoo \
            -v /var/log/odoo/{instance.db_name}:/var/log/odoo \
            --restart unless-stopped \
            odoo:{instance.odoo_version}
        """
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success:
            _logger.info(f"Created Odoo container {instance.db_name} via SSH on server {server.name}")
            return True
        else:
            _logger.error(f"Failed to create container via SSH: {output}")
            return False
    except Exception as e:
        _logger.error(f"SSH container creation failed: {e}")
        return False

def stop_odoo_container(server, instance):
    """Stops the Odoo container for the given instance on the specified server."""
    try:
        if server.server_type == 'docker':
            client = get_docker_client(server)
            if client:
                try:
                    container = client.containers.get(instance.db_name)
                    container.stop(timeout=30)
                    _logger.info(f"Stopped Odoo container {instance.db_name}")
                    return True
                except docker.errors.NotFound:
                    _logger.warning(f"Container {instance.db_name} not found")
                    return True
            else:
                return _stop_container_via_ssh(server, instance)
        else:
            return _stop_container_via_ssh(server, instance)
    except Exception as e:
        _logger.error(f"Failed to stop Odoo container {instance.db_name}: {e}")
        return False

def _stop_container_via_ssh(server, instance):
    """Stop container using SSH as fallback method."""
    try:
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return False
            
        command = f"docker stop {instance.db_name}"
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success:
            _logger.info(f"Stopped Odoo container {instance.db_name} via SSH")
            return True
        else:
            _logger.error(f"Failed to stop container via SSH: {output}")
            return False
    except Exception as e:
        _logger.error(f"SSH container stop failed: {e}")
        return False

def start_odoo_container(server, instance):
    """Starts the Odoo container for the given instance on the specified server."""
    try:
        if server.server_type == 'docker':
            client = get_docker_client(server)
            if client:
                try:
                    container = client.containers.get(instance.db_name)
                    container.start()
                    _logger.info(f"Started Odoo container {instance.db_name}")
                    return True
                except docker.errors.NotFound:
                    _logger.warning(f"Container {instance.db_name} not found")
                    return False
            else:
                return _start_container_via_ssh(server, instance)
        else:
            return _start_container_via_ssh(server, instance)
    except Exception as e:
        _logger.error(f"Failed to start Odoo container {instance.db_name}: {e}")
        return False

def _start_container_via_ssh(server, instance):
    """Start container using SSH as fallback method."""
    try:
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return False
            
        command = f"docker start {instance.db_name}"
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success:
            _logger.info(f"Started Odoo container {instance.db_name} via SSH")
            return True
        else:
            _logger.error(f"Failed to start container via SSH: {output}")
            return False
    except Exception as e:
        _logger.error(f"SSH container start failed: {e}")
        return False

def remove_odoo_container(server, instance):
    """Removes the Odoo container for the given instance on the specified server."""
    try:
        if server.server_type == 'docker':
            client = get_docker_client(server)
            if client:
                try:
                    container = client.containers.get(instance.db_name)
                    container.remove(force=True)
                    _logger.info(f"Removed Odoo container {instance.db_name}")
                    return True
                except docker.errors.NotFound:
                    _logger.warning(f"Container {instance.db_name} not found")
                    return True
            else:
                return _remove_container_via_ssh(server, instance)
        else:
            return _remove_container_via_ssh(server, instance)
    except Exception as e:
        _logger.error(f"Failed to remove Odoo container {instance.db_name}: {e}")
        return False

def _remove_container_via_ssh(server, instance):
    """Remove container using SSH as fallback method."""
    try:
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return False
            
        command = f"docker rm -f {instance.db_name}"
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success:
            _logger.info(f"Removed Odoo container {instance.db_name} via SSH")
            return True
        else:
            _logger.error(f"Failed to remove container via SSH: {output}")
            return False
    except Exception as e:
        _logger.error(f"SSH container removal failed: {e}")
        return False

def get_container_status(server, instance):
    """Get the status of an Odoo container."""
    try:
        if server.server_type == 'docker':
            client = get_docker_client(server)
            if client:
                try:
                    container = client.containers.get(instance.db_name)
                    return container.status
                except docker.errors.NotFound:
                    return 'not_found'
            else:
                return _get_container_status_via_ssh(server, instance)
        else:
            return _get_container_status_via_ssh(server, instance)
    except Exception as e:
        _logger.error(f"Failed to get container status for {instance.db_name}: {e}")
        return 'error'

def _get_container_status_via_ssh(server, instance):
    """Get container status using SSH as fallback method."""
    try:
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return 'error'
            
        command = f"docker ps -a --filter name={instance.db_name} --format '{{{{.Status}}}}'"
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success and output.strip():
            if 'Up' in output:
                return 'running'
            elif 'Exited' in output:
                return 'exited'
            else:
                return 'unknown'
        else:
            return 'not_found'
    except Exception as e:
        _logger.error(f"SSH container status check failed: {e}")
        return 'error'

def backup_container_data(server, instance):
    """Create a backup of the container data."""
    try:
        ssh_client = ssh_utils.get_ssh_client(server)
        if not ssh_client:
            return False
            
        backup_path = f"/backups/{instance.db_name}_{int(time.time())}.tar"
        command = f"docker export {instance.db_name} > {backup_path}"
        success, output = ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)
        
        if success:
            _logger.info(f"Created backup for container {instance.db_name}: {backup_path}")
            return True
        else:
            _logger.error(f"Failed to create backup: {output}")
            return False
    except Exception as e:
        _logger.error(f"Container backup failed: {e}")
        return False 