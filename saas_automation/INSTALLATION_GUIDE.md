# SaaS Automation Module - Installation & Setup Guide

## Prerequisites

### System Requirements
- Odoo 18.0 or later
- Python 3.8+
- PostgreSQL 12+
- Docker (for container management)
- SSH access to target servers

### Python Dependencies
Install the required Python packages:

```bash
# Core dependencies
pip install docker>=6.0.0
pip install paramiko>=3.0.0
pip install psycopg2-binary>=2.9.0
pip install cryptography>=3.4.0

# Optional dependencies (for advanced features)
pip install kubernetes>=26.0.0
pip install redis>=4.0.0
pip install celery>=5.0.0
pip install requests>=2.28.0
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

## Installation Steps

### 1. Module Installation
1. Copy the `saas_automation` folder to your Odoo addons directory
2. Update the addons path in your Odoo configuration
3. Restart Odoo server
4. Go to Apps menu and search for "SaaS Automation"
5. Click Install

### 2. Initial Configuration

#### Security Groups
The module automatically creates the following security groups:
- **SaaS Manager**: Full access to all SaaS features
- **SaaS User**: Basic access to SaaS features
- **SaaS Administrator**: Administrative access

#### Default Data
The module installs with:
- Default subscription plans (Basic, Standard, Premium)
- Sequence configurations for instances and subscriptions
- Cron jobs for automated tasks

### 3. Server Configuration

#### Docker Server Setup
1. Ensure Docker is installed and running on target servers
2. Configure Docker daemon to accept remote connections (optional)
3. Set up SSH access to the server

#### SSH Configuration
1. Generate SSH key pair (recommended) or use password authentication
2. Configure SSH user with sudo privileges
3. Test SSH connectivity

### 4. Database Configuration
1. Ensure PostgreSQL is running on target servers
2. Create database user with appropriate permissions
3. Configure database connection parameters

## Configuration

### 1. Server Management
1. Go to **SaaS > Configuration > Servers**
2. Click **Create** to add a new server
3. Fill in server details:
   - **Server Name**: Descriptive name
   - **Server Type**: Docker (recommended)
   - **Host Address**: IP or hostname
   - **SSH User**: Username for SSH access
   - **SSH Password/Key**: Authentication credentials
   - **Max Instances**: Maximum number of instances
4. Click **Test Connection** to verify setup
5. Save the server configuration

### 2. Subscription Plans
1. Go to **SaaS > Configuration > Plans**
2. Review default plans or create custom plans
3. Configure pricing, user limits, and included modules

### 3. Domain Configuration
1. Configure your domain for subdomain routing
2. Set up DNS records for subdomains
3. Configure Nginx reverse proxy (optional)

## Usage

### Creating Instances
1. Go to **SaaS > Instances > Create**
2. Select customer, plan, and server
3. Enter subdomain name
4. Choose Odoo version
5. Click **Create Instance**

### Managing Instances
- **Deploy**: Start the instance
- **Suspend**: Stop the instance
- **Resume**: Restart the instance
- **Cancel**: Remove the instance

### Backup and Restore
1. Go to **SaaS > Instances > Backup & Restore**
2. Select instance and operation type
3. Configure backup options
4. Execute backup or restore

## Troubleshooting

### Common Issues

#### SSH Connection Failed
- Verify SSH credentials
- Check firewall settings
- Ensure SSH service is running
- Test connection manually

#### Docker Issues
- Verify Docker is installed and running
- Check Docker daemon configuration
- Ensure user has Docker permissions

#### Database Issues
- Verify PostgreSQL is running
- Check database user permissions
- Ensure database exists and is accessible

#### Import Errors
- Install missing Python packages
- Check Python version compatibility
- Verify module dependencies

### Logs and Debugging
- Check Odoo server logs
- Review Docker container logs
- Monitor SSH connection logs
- Use debug mode for detailed error messages

## Security Considerations

### SSH Security
- Use SSH key authentication instead of passwords
- Restrict SSH access to specific IPs
- Use non-standard SSH ports
- Regularly update SSH keys

### Docker Security
- Run containers with minimal privileges
- Use read-only filesystems where possible
- Regularly update Docker images
- Monitor container resource usage

### Database Security
- Use strong database passwords
- Restrict database access to necessary IPs
- Regularly backup databases
- Monitor database connections

## Performance Optimization

### Server Optimization
- Monitor server resource usage
- Scale servers based on demand
- Use load balancing for multiple servers
- Optimize Docker container configurations

### Database Optimization
- Regular database maintenance (VACUUM, ANALYZE)
- Monitor database performance
- Optimize queries and indexes
- Use connection pooling

## Support

For technical support and questions:
- **Email**: info@ecosire.com
- **Website**: https://www.ecosire.com
- **Documentation**: Check the module documentation

## License

This module is developed by ECOSIRE (PRIVATE) LIMITED.
All rights reserved. 