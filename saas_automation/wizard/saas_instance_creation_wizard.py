# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaasInstanceCreationWizard(models.TransientModel):
    _name = 'saas.instance.creation.wizard'
    _description = 'SaaS Instance Creation Wizard'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    plan_id = fields.Many2one('saas.plan', string='Plan', required=True)
    subdomain = fields.Char(string='Subdomain', required=True)

    def action_create_instance(self):
        instance_vals = {
            'partner_id': self.partner_id.id,
            'plan_id': self.plan_id.id,
            'subdomain': self.subdomain,
            'db_name': f"{self.subdomain.replace('.', '-')}-{self.plan_id.name.lower().replace(' ', '-')}",
        }
        instance = self.env['saas.instance'].create(instance_vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'saas.instance',
            'res_id': instance.id,
            'view_mode': 'form',
            'target': 'current',
        } 