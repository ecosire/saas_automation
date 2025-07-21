# -*- coding: utf-8 -*-
import logging
from . import ssh_utils

_logger = logging.getLogger(__name__)

def get_nginx_config(instance):
    """Generates the Nginx configuration for the specified instance."""
    return f"""
server {{
    listen 80;
    server_name {instance.custom_domain};

    location / {{
        proxy_pass http://{instance.server_id.host}:{instance.port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}
"""

def create_nginx_config(server, instance):
    """Creates a new Nginx configuration file for the specified instance on the given server."""
    ssh_client = ssh_utils.get_ssh_client(server)
    config = get_nginx_config(instance)
    config_path = f"/etc/nginx/sites-available/{instance.custom_domain}"
    command = f"echo '{config}' > {config_path}"
    ssh_utils.execute_ssh_command(ssh_client, command)
    ssh_utils.execute_ssh_command(ssh_client, f"ln -s {config_path} /etc/nginx/sites-enabled/")
    ssh_utils.execute_ssh_command(ssh_client, "systemctl reload nginx")
    ssh_utils.close_ssh_client(ssh_client)

def remove_nginx_config(server, instance):
    """Removes the Nginx configuration file for the specified instance on the given server."""
    ssh_client = ssh_utils.get_ssh_client(server)
    config_path = f"/etc/nginx/sites-available/{instance.custom_domain}"
    ssh_utils.execute_ssh_command(ssh_client, f"rm {config_path}")
    ssh_utils.execute_ssh_command(ssh_client, f"rm /etc/nginx/sites-enabled/{instance.custom_domain}")
    ssh_utils.execute_ssh_command(ssh_client, "systemctl reload nginx")
    ssh_utils.close_ssh_client(ssh_client) 