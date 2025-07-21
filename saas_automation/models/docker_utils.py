# -*- coding: utf-8 -*-
import docker
from . import ssh_utils

def get_docker_client(server):
    """Initializes and returns a Docker client connected to the specified server."""
    if server.server_type == 'docker':
        return docker.DockerClient(base_url=f"tcp://{server.host}:2375") # Default docker port
    elif server.server_type == 'kubernetes':
        # Placeholder for Kubernetes client
        return None

def create_odoo_container(server, instance):
    """Creates and starts a new Odoo container for the given instance on the specified server."""
    if server.server_type == 'docker':
        client = get_docker_client(server)
        client.containers.run(
            image=f"odoo:{instance.odoo_version}",
            name=instance.db_name,
            detach=True,
            environment={
                'HOST': 'db',
                'USER': 'odoo',
                'PASSWORD': 'odoo',
            },
            ports={'8069/tcp': None},
        )
    else:
        ssh_client = ssh_utils.get_ssh_client(server)
        command = f"docker run -d --name {instance.db_name} -p 8069:8069 -e HOST=db -e USER=odoo -e PASSWORD=odoo odoo:{instance.odoo_version}"
        ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)

def stop_odoo_container(server, instance):
    """Stops the Odoo container for the given instance on the specified server."""
    if server.server_type == 'docker':
        client = get_docker_client(server)
        try:
            container = client.containers.get(instance.db_name)
            container.stop()
        except docker.errors.NotFound:
            pass
    else:
        ssh_client = ssh_utils.get_ssh_client(server)
        command = f"docker stop {instance.db_name}"
        ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)

def start_odoo_container(server, instance):
    """Starts the Odoo container for the given instance on the specified server."""
    if server.server_type == 'docker':
        client = get_docker_client(server)
        try:
            container = client.containers.get(instance.db_name)
            container.start()
        except docker.errors.NotFound:
            pass
    else:
        ssh_client = ssh_utils.get_ssh_client(server)
        command = f"docker start {instance.db_name}"
        ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client)

def remove_odoo_container(server, instance):
    """Removes the Odoo container for the given instance on the specified server."""
    if server.server_type == 'docker':
        client = get_docker_client(server)
        try:
            container = client.containers.get(instance.db_name)
            container.remove(force=True)
        except docker.errors.NotFound:
            pass
    else:
        ssh_client = ssh_utils.get_ssh_client(server)
        command = f"docker rm -f {instance.db_name}"
        ssh_utils.execute_ssh_command(ssh_client, command)
        ssh_utils.close_ssh_client(ssh_client) 