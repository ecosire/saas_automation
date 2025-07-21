# -*- coding: utf-8 -*-
import paramiko
import logging

_logger = logging.getLogger(__name__)

def get_ssh_client(server):
    """Initializes and returns an SSH client connected to the specified server."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server.host, port=server.port, username=server.ssh_user, password=server.ssh_password)
    return client

def execute_ssh_command(client, command):
    """Executes a command on the remote server and returns the output."""
    try:
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        if error:
            _logger.error(f"Error executing SSH command: {error}")
            return False, error
        return True, output
    except Exception as e:
        _logger.error(f"Failed to execute SSH command: {e}")
        return False, str(e)

def close_ssh_client(client):
    """Closes the SSH client connection."""
    client.close() 