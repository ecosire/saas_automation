# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class SaasBillingWizard(models.TransientModel):
    _name = 'saas.billing.wizard'
    _description = 'SaaS Billing Operations Wizard'

    # Billing Configuration
    billing_type = fields.Selection([
        ('subscription', 'Subscription Billing'),
        ('usage', 'Usage-based Billing'),
        ('one_time', 'One-time Charges'),
        ('adjustment', 'Billing Adjustments'),
    ], string='Billing Type', required=True, default='subscription')
    
    billing_date = fields.Date(string='Billing Date', required=True, default=fields.Date.today)
    due_date = fields.Date(string='Due Date', required=True)
    payment_terms_id = fields.Many2one('account.payment.term', string='Payment Terms')
    
    # Customer Selection
    partner_ids = fields.Many2many('res.partner', string='Customers')
    subscription_ids = fields.Many2many('saas.subscription', string='Subscriptions')
    include_trials = fields.Boolean(string='Include Trial Instances', default=False)
    
    # Invoice Options
    auto_confirm = fields.Boolean(string='Auto Confirm Invoices', default=True)
    send_email = fields.Boolean(string='Send Email Notifications', default=True)
    include_usage_details = fields.Boolean(string='Include Usage Details', default=True)
    apply_discounts = fields.Boolean(string='Apply Discounts', default=False)
    
    # Advanced Options
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', '=', 'sale')])
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Preview Lines
    preview_line_ids = fields.One2many('saas.billing.wizard.line', 'wizard_id', string='Preview Lines')

    @api.onchange('billing_date')
    def _onchange_billing_date(self):
        """Set default due date to 30 days after billing date."""
        if self.billing_date:
            self.due_date = self.billing_date + timedelta(days=30)

    @api.onchange('billing_type', 'partner_ids', 'subscription_ids', 'include_trials')
    def _onchange_billing_selection(self):
        """Update preview lines when billing selection changes."""
        self.preview_line_ids = [(5, 0, 0)]  # Clear existing lines
        if self.billing_type and (self.partner_ids or self.subscription_ids):
            self._generate_preview_lines()

    def _generate_preview_lines(self):
        """Generate preview lines based on selection."""
        lines = []
        
        if self.billing_type == 'subscription':
            lines = self._get_subscription_lines()
        elif self.billing_type == 'usage':
            lines = self._get_usage_lines()
        elif self.billing_type == 'one_time':
            lines = self._get_one_time_lines()
        elif self.billing_type == 'adjustment':
            lines = self._get_adjustment_lines()
        
        self.preview_line_ids = lines

    def _get_subscription_lines(self):
        """Get subscription billing lines."""
        lines = []
        subscriptions = self.subscription_ids or self.env['saas.subscription'].search([
            ('state', '=', 'active'),
            ('partner_id', 'in', self.partner_ids.ids) if self.partner_ids else True,
        ])
        
        for subscription in subscriptions:
            lines.append((0, 0, {
                'partner_id': subscription.partner_id.id,
                'subscription_id': subscription.id,
                'amount': subscription.price,
                'description': f"Subscription: {subscription.plan_id.name}",
                'include_invoice': True,
            }))
        
        return lines

    def _get_usage_lines(self):
        """Get usage-based billing lines."""
        lines = []
        instances = self.env['saas.instance'].search([
            ('state', '=', 'running'),
            ('partner_id', 'in', self.partner_ids.ids) if self.partner_ids else True,
        ])
        
        for instance in instances:
            # Calculate usage-based charges (simplified)
            usage_amount = instance.active_user_count * 5.0  # $5 per user
            lines.append((0, 0, {
                'partner_id': instance.partner_id.id,
                'subscription_id': False,
                'amount': usage_amount,
                'description': f"Usage charges for {instance.name}",
                'include_invoice': True,
            }))
        
        return lines

    def _get_one_time_lines(self):
        """Get one-time charge lines."""
        lines = []
        # This would typically come from a separate model for one-time charges
        # For now, we'll create placeholder lines
        for partner in self.partner_ids:
            lines.append((0, 0, {
                'partner_id': partner.id,
                'subscription_id': False,
                'amount': 100.0,  # Placeholder amount
                'description': 'One-time setup fee',
                'include_invoice': True,
            }))
        
        return lines

    def _get_adjustment_lines(self):
        """Get billing adjustment lines."""
        lines = []
        # This would typically come from a separate model for adjustments
        # For now, we'll create placeholder lines
        for partner in self.partner_ids:
            lines.append((0, 0, {
                'partner_id': partner.id,
                'subscription_id': False,
                'amount': -50.0,  # Negative for credits
                'description': 'Billing adjustment',
                'include_invoice': True,
            }))
        
        return lines

    def action_preview_billing(self):
        """Preview billing lines."""
        self._generate_preview_lines()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'saas.billing.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_generate_invoices(self):
        """Generate invoices for selected lines."""
        if not self.preview_line_ids:
            raise UserError(_("No billing lines to process."))
        
        invoices_created = []
        for line in self.preview_line_ids.filtered(lambda l: l.include_invoice):
            invoice = self._create_invoice(line)
            if invoice:
                invoices_created.append(invoice)
        
        if invoices_created:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Invoices Created'),
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', [inv.id for inv in invoices_created])],
                'context': {'create': False},
            }
        else:
            raise UserError(_("No invoices were created."))

    def _create_invoice(self, line):
        """Create invoice for a billing line."""
        invoice_vals = {
            'partner_id': line.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.billing_date,
            'invoice_due_date': self.due_date,
            'currency_id': self.currency_id.id,
            'fiscal_position_id': self.fiscal_position_id.id if self.fiscal_position_id else False,
            'journal_id': self.journal_id.id if self.journal_id else False,
            'company_id': self.company_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': line.description,
                'price_unit': abs(line.amount),
                'quantity': 1,
                'account_id': self._get_default_account(),
            })],
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        if self.auto_confirm:
            invoice.action_post()
        
        if self.send_email:
            self._send_invoice_email(invoice)
        
        return invoice

    def _get_default_account(self):
        """Get default account for invoice lines."""
        return self.env['account.account'].search([
            ('company_id', '=', self.company_id.id),
            ('account_type', '=', 'income'),
        ], limit=1).id

    def _send_invoice_email(self, invoice):
        """Send invoice email to customer."""
        try:
            template = self.env.ref('account.email_template_edi_invoice')
            if template:
                template.send_mail(invoice.id, force_send=True)
        except Exception as e:
            # Log error but don't fail the process
            _logger.warning(f"Failed to send invoice email: {e}")


class SaasBillingWizardLine(models.TransientModel):
    _name = 'saas.billing.wizard.line'
    _description = 'SaaS Billing Wizard Line'

    wizard_id = fields.Many2one('saas.billing.wizard', string='Wizard')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    subscription_id = fields.Many2one('saas.subscription', string='Subscription')
    amount = fields.Float(string='Amount', required=True)
    description = fields.Char(string='Description', required=True)
    include_invoice = fields.Boolean(string='Include in Invoice', default=True)
