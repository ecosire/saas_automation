# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestSaasInstance(TransactionCase):
    
    def setUp(self):
        super(TestSaasInstance, self).setUp()
        # Create test data
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
        })
        
        self.server = self.env['saas.server'].create({
            'name': 'Test Server',
            'host': 'localhost',
            'ssh_user': 'test',
            'server_type': 'docker',
        })
        
        self.plan = self.env['saas.plan'].create({
            'name': 'Test Plan',
            'price_monthly': 29.99,
            'max_users': 10,
            'max_instances': 1,
        })

    def test_create_instance(self):
        """Test creating a SaaS instance"""
        instance = self.env['saas.instance'].create({
            'partner_id': self.partner.id,
            'server_id': self.server.id,
            'plan_id': self.plan.id,
            'subdomain': 'testinstance',
            'db_name': 'test_db',
            'odoo_version': '18.0',
        })
        
        self.assertEqual(instance.name, 'New')
        self.assertEqual(instance.state, 'draft')
        self.assertEqual(instance.subdomain, 'testinstance')
        self.assertEqual(instance.db_name, 'test_db')

    def test_compute_url(self):
        """Test URL computation"""
        instance = self.env['saas.instance'].create({
            'partner_id': self.partner.id,
            'server_id': self.server.id,
            'plan_id': self.plan.id,
            'subdomain': 'testinstance',
            'db_name': 'test_db',
            'odoo_version': '18.0',
            'domain': 'example.com',
        })
        
        # Test subdomain URL
        instance._compute_url()
        self.assertEqual(instance.url, 'https://testinstance.example.com')
        
        # Test custom domain
        instance.custom_domain = 'custom.example.com'
        instance.is_custom_domain_active = True
        instance._compute_url()
        self.assertEqual(instance.url, 'https://custom.example.com') 