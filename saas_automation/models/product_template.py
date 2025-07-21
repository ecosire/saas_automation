# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    saas_plan_id = fields.Many2one('saas.plan', string='SaaS Plan', tracking=True) 