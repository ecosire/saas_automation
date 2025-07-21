# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class SaasWebsiteController(http.Controller):

    @http.route('/saas/pricing', type='http', auth='public', website=True)
    def pricing_page(self, **kwargs):
        plans = request.env['saas.plan'].search([('is_active', '=', True)])
        return request.render('saas_automation.pricing_page_template', {'plans': plans}) 