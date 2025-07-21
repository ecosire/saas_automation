# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class CustomerPortal(CustomerPortal):

    @http.route(['/my/saas'], type='http', auth="user", website=True)
    def portal_my_saas(self, **kwargs):
        instances = request.env['saas.instance'].search([('partner_id', '=', request.env.user.partner_id.id)])
        return request.render("saas_automation.portal_my_saas_template", {'instances': instances}) 