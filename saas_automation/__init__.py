# -*- coding: utf-8 -*-

from . import models
from . import controllers
from . import wizard

def _saas_pre_init_hook(cr):
    """
    Pre-installation hook to clean up any conflicts
    """
    # Skip pre-installation cleanup for now to avoid compatibility issues
    pass

def _saas_post_init_hook(env):
    """
    Post-installation hook to set up the module
    """
    try:
        # Ensure the SaaS Manager group exists and is properly configured
        saas_manager_group = env['res.groups'].search([
            ('name', '=', 'SaaS Manager')
        ], limit=1)
        
        if not saas_manager_group:
            # Create the group if it doesn't exist
            saas_manager_group = env['res.groups'].create({
                'name': 'SaaS Manager',
                'category_id': env.ref('base.module_category_services').id,
            })
        
        # Assign the group to admin user
        admin_user = env.ref('base.user_admin')
        if admin_user and saas_manager_group not in admin_user.groups_id:
            admin_user.write({'groups_id': [(4, saas_manager_group.id)]})
        
        # Set up default configurations
        _setup_default_configurations(env)
    except Exception as e:
        # Log the error but don't fail the installation
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning(f"SaaS Automation post_init_hook failed: {str(e)}")
        pass

def _saas_uninstall_hook(env):
    """
    Uninstall hook to clean up when the module is removed
    """
    try:
        # Remove the SaaS Manager group if it's not used by other modules
        saas_manager_group = env['res.groups'].search([
            ('name', '=', 'SaaS Manager')
        ], limit=1)
        
        if saas_manager_group:
            # Check if any users are using this group
            users_with_group = env['res.users'].search([
                ('groups_id', 'in', saas_manager_group.id)
            ])
            
            if not users_with_group:
                saas_manager_group.unlink()
    except Exception as e:
        # Log the error but don't fail the uninstallation
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning(f"SaaS Automation uninstall_hook failed: {str(e)}")
        pass

def _setup_default_configurations(env):
    """
    Set up default configurations for the SaaS automation module
    """
    # Note: Default configurations will be set up when the corresponding models are created
    # For now, we'll skip this to avoid errors with non-existent models
    pass 