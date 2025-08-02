# -*- coding: utf-8 -*-
import logging
import os

_logger = logging.getLogger(__name__)

# Optional imports - handle gracefully if not available
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    _logger.warning("Paramiko package not installed. Install with: pip install paramiko")

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    _logger.warning("Cryptography package not installed. Install with: pip install cryptography")

def get_ssh_client(server):
    """Initializes and returns an SSH client connected to the specified server."""
    if not PARAMIKO_AVAILABLE:
        _logger.error("Paramiko package not available. Cannot establish SSH connection.")
        return None
        
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Try SSH key first, then password
        ssh_key_path = server.ssh_private_key_path or '~/.ssh/id_rsa'
        ssh_key_path = os.path.expanduser(ssh_key_path)
        
        if os.path.exists(ssh_key_path):
            try:
                private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
                client.connect(
                    server.host, 
                    port=server.port, 
                    username=server.ssh_user, 
                    pkey=private_key,
                    timeout=30
                )
                _logger.info(f"SSH connection established using key for {server.name}")
                return client
            except Exception as e:
                _logger.warning(f"SSH key authentication failed for {server.name}: {e}")
        
        # Fallback to password authentication
        if server.ssh_password:
            client.connect(
                server.host, 
                port=server.port, 
                username=server.ssh_user, 
                password=server.ssh_password,
                timeout=30
            )
            _logger.info(f"SSH connection established using password for {server.name}")
            return client
        else:
            _logger.error(f"No SSH credentials provided for server {server.name}")
            return None
            
    except Exception as e:
        _logger.error(f"Failed to establish SSH connection to {server.name}: {e}")
        return None

def execute_ssh_command(client, command, timeout=60):
    """Executes a command on the remote server and returns the output."""
    try:
        if not client:
            return False, "No SSH client provided"
        
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        
        # Wait for command to complete
        exit_status = stdout.channel.recv_exit_status()
        
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        
        if exit_status != 0:
            _logger.error(f"SSH command failed with exit status {exit_status}: {error}")
            return False, error
        
        if error and not output:
            _logger.warning(f"SSH command produced stderr: {error}")
            return False, error
        
        return True, output
    except Exception as e:
        _logger.error(f"Failed to execute SSH command: {e}")
        return False, str(e)

def execute_ssh_command_with_sudo(client, command, password=None, timeout=60):
    """Executes a command with sudo privileges."""
    try:
        if not client:
            return False, "No SSH client provided"
        
        if password:
            sudo_command = f"echo '{password}' | sudo -S {command}"
        else:
            sudo_command = f"sudo {command}"
        
        return execute_ssh_command(client, sudo_command, timeout)
    except Exception as e:
        _logger.error(f"Failed to execute sudo SSH command: {e}")
        return False, str(e)

def upload_file_via_ssh(client, local_path, remote_path):
    """Uploads a file to the remote server via SCP."""
    try:
        if not client:
            return False, "No SSH client provided"
        
        sftp = client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        
        _logger.info(f"Uploaded {local_path} to {remote_path}")
        return True, "File uploaded successfully"
    except Exception as e:
        _logger.error(f"Failed to upload file: {e}")
        return False, str(e)

def download_file_via_ssh(client, remote_path, local_path):
    """Downloads a file from the remote server via SCP."""
    try:
        if not client:
            return False, "No SSH client provided"
        
        sftp = client.open_sftp()
        sftp.get(remote_path, local_path)
        sftp.close()
        
        _logger.info(f"Downloaded {remote_path} to {local_path}")
        return True, "File downloaded successfully"
    except Exception as e:
        _logger.error(f"Failed to download file: {e}")
        return False, str(e)

def close_ssh_client(client):
    """Closes the SSH client connection."""
    try:
        if client:
            client.close()
            _logger.debug("SSH client connection closed")
    except Exception as e:
        _logger.error(f"Error closing SSH client: {e}")

def test_ssh_connection(server):
    """Tests SSH connection to the server."""
    try:
        client = get_ssh_client(server)
        if not client:
            return False, "Failed to establish SSH connection"
        
        success, output = execute_ssh_command(client, "echo 'SSH connection test successful'")
        close_ssh_client(client)
        
        if success:
            return True, "SSH connection test successful"
        else:
            return False, f"SSH command execution failed: {output}"
    except Exception as e:
        return False, f"SSH connection test failed: {e}"

def get_server_info(server):
    """Gets basic server information via SSH."""
    try:
        client = get_ssh_client(server)
        if not client:
            return None
        
        info = {}
        
        # Get OS information
        success, output = execute_ssh_command(client, "cat /etc/os-release")
        if success:
            info['os'] = output
        
        # Get memory information
        success, output = execute_ssh_command(client, "free -h")
        if success:
            info['memory'] = output
        
        # Get disk information
        success, output = execute_ssh_command(client, "df -h")
        if success:
            info['disk'] = output
        
        # Get Docker information
        success, output = execute_ssh_command(client, "docker --version")
        if success:
            info['docker'] = output
        
        close_ssh_client(client)
        return info
    except Exception as e:
        _logger.error(f"Failed to get server info: {e}")
        return None

def create_remote_directory(client, directory_path):
    """Creates a directory on the remote server."""
    try:
        if not client:
            return False, "No SSH client provided"
        
        success, output = execute_ssh_command(client, f"mkdir -p {directory_path}")
        if success:
            _logger.info(f"Created remote directory: {directory_path}")
            return True, "Directory created successfully"
        else:
            return False, f"Failed to create directory: {output}"
    except Exception as e:
        _logger.error(f"Failed to create remote directory: {e}")
        return False, str(e)

def check_remote_file_exists(client, file_path):
    """Checks if a file exists on the remote server."""
    try:
        if not client:
            return False
        
        success, output = execute_ssh_command(client, f"test -f {file_path} && echo 'exists'")
        return success and 'exists' in output
    except Exception as e:
        _logger.error(f"Failed to check remote file existence: {e}")
        return False 