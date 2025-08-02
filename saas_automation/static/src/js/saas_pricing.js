// Static JS file for SaaS Pricing Page
odoo.define('saas_automation.pricing', function (require) {
    "use strict";

    var core = require('web.core');
    var publicWidget = require('web.public.widget');

    var QWeb = core.qweb;
    var _t = core._t;

    // SaaS Pricing Widget
    var SaasPricing = publicWidget.Widget.extend({
        template: 'saas_pricing_template',
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.options = options || {};
        },
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initPricing();
            });
        },
        
        _initPricing: function () {
            this._loadPricingPlans();
            this._setupEventListeners();
        },
        
        _loadPricingPlans: function () {
            var self = this;
            this._rpc({
                route: '/saas/pricing/plans',
                params: {},
            }).then(function (plans) {
                self._displayPlans(plans);
            }).catch(function (error) {
                console.error('Failed to load pricing plans:', error);
            });
        },
        
        _displayPlans: function (plans) {
            var $plansContainer = this.$('.saas-pricing-plans');
            $plansContainer.empty();
            
            plans.forEach(function (plan) {
                var $planElement = $(QWeb.render('saas_pricing_plan', {
                    plan: plan
                }));
                $plansContainer.append($planElement);
            });
        },
        
        _setupEventListeners: function () {
            var self = this;
            
            // Plan selection
            this.$('.saas-plan-button').on('click', function (e) {
                e.preventDefault();
                var planId = $(this).data('plan-id');
                self._selectPlan(planId);
            });
            
            // Billing cycle toggle
            this.$('.billing-toggle').on('change', function () {
                var isYearly = $(this).is(':checked');
                self._toggleBillingCycle(isYearly);
            });
        },
        
        _selectPlan: function (planId) {
            var self = this;
            this._rpc({
                route: '/saas/pricing/select_plan',
                params: {
                    plan_id: planId
                },
            }).then(function (result) {
                if (result.success) {
                    // Redirect to checkout or show success message
                    if (result.redirect_url) {
                        window.location.href = result.redirect_url;
                    } else {
                        self._showMessage(_t('Plan selected successfully!'), 'success');
                    }
                } else {
                    self._showMessage(_t('Failed to select plan'), 'error');
                }
            }).catch(function (error) {
                console.error('Failed to select plan:', error);
                self._showMessage(_t('Failed to select plan'), 'error');
            });
        },
        
        _toggleBillingCycle: function (isYearly) {
            var $plans = this.$('.saas-pricing-plan');
            $plans.each(function () {
                var $plan = $(this);
                var monthlyPrice = $plan.data('monthly-price');
                var yearlyPrice = $plan.data('yearly-price');
                var $priceElement = $plan.find('.saas-plan-price');
                
                if (isYearly) {
                    $priceElement.html('<span class="currency">$</span>' + yearlyPrice + '<span class="period">/year</span>');
                } else {
                    $priceElement.html('<span class="currency">$</span>' + monthlyPrice + '<span class="period">/month</span>');
                }
            });
        },
        
        _showMessage: function (message, type) {
            var alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
            var $alert = $('<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
                message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                '</div>');
            
            this.$('.pricing-messages').append($alert);
            
            // Auto-remove after 5 seconds
            setTimeout(function () {
                $alert.fadeOut(function () {
                    $(this).remove();
                });
            }, 5000);
        },
        
        // Public methods
        refreshPlans: function () {
            this._loadPricingPlans();
        },
        
        highlightPlan: function (planId) {
            this.$('.saas-pricing-plan').removeClass('featured');
            this.$('.saas-pricing-plan[data-plan-id="' + planId + '"]').addClass('featured');
        },
    });

    // Register the widget
    publicWidget.registry.saasPricing = SaasPricing;

    return SaasPricing;
}); 