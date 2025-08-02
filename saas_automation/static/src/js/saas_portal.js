// Static JS file for SaaS Portal
odoo.define('saas_automation.portal', function (require) {
    "use strict";

    var core = require('web.core');
    var publicWidget = require('web.public.widget');

    var QWeb = core.qweb;
    var _t = core._t;

    // SaaS Portal Widget
    var SaasPortal = publicWidget.Widget.extend({
        template: 'saas_portal_template',
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.options = options || {};
        },
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initPortal();
            });
        },
        
        _initPortal: function () {
            this._loadInstances();
            this._loadSubscriptions();
            this._setupEventListeners();
        },
        
        _loadInstances: function () {
            var self = this;
            this._rpc({
                route: '/my/saas/instances',
                params: {},
            }).then(function (instances) {
                self._displayInstances(instances);
            }).catch(function (error) {
                console.error('Failed to load instances:', error);
            });
        },
        
        _loadSubscriptions: function () {
            var self = this;
            this._rpc({
                route: '/my/saas/subscriptions',
                params: {},
            }).then(function (subscriptions) {
                self._displaySubscriptions(subscriptions);
            }).catch(function (error) {
                console.error('Failed to load subscriptions:', error);
            });
        },
        
        _displayInstances: function (instances) {
            var $instancesContainer = this.$('.saas-instances');
            $instancesContainer.empty();
            
            if (instances.length === 0) {
                $instancesContainer.append('<p class="text-muted">No instances found.</p>');
                return;
            }
            
            instances.forEach(function (instance) {
                var $instanceElement = $(QWeb.render('saas_instance_card', {
                    instance: instance
                }));
                $instancesContainer.append($instanceElement);
            });
        },
        
        _displaySubscriptions: function (subscriptions) {
            var $subscriptionsContainer = this.$('.saas-subscriptions');
            $subscriptionsContainer.empty();
            
            if (subscriptions.length === 0) {
                $subscriptionsContainer.append('<p class="text-muted">No subscriptions found.</p>');
                return;
            }
            
            subscriptions.forEach(function (subscription) {
                var $subscriptionElement = $(QWeb.render('saas_subscription_card', {
                    subscription: subscription
                }));
                $subscriptionsContainer.append($subscriptionElement);
            });
        },
        
        _setupEventListeners: function () {
            var self = this;
            
            // Instance actions
            this.$('.instance-action').on('click', function (e) {
                e.preventDefault();
                var action = $(this).data('action');
                var instanceId = $(this).data('instance-id');
                self._performInstanceAction(action, instanceId);
            });
            
            // Subscription actions
            this.$('.subscription-action').on('click', function (e) {
                e.preventDefault();
                var action = $(this).data('action');
                var subscriptionId = $(this).data('subscription-id');
                self._performSubscriptionAction(action, subscriptionId);
            });
            
            // Refresh button
            this.$('.refresh-data').on('click', function (e) {
                e.preventDefault();
                self._refreshData();
            });
        },
        
        _performInstanceAction: function (action, instanceId) {
            var self = this;
            this._rpc({
                route: '/my/saas/instance/action',
                params: {
                    action: action,
                    instance_id: instanceId
                },
            }).then(function (result) {
                if (result.success) {
                    self._showMessage(_t('Action performed successfully'), 'success');
                    self._refreshData();
                } else {
                    self._showMessage(_t('Failed to perform action'), 'error');
                }
            }).catch(function (error) {
                console.error('Failed to perform instance action:', error);
                self._showMessage(_t('Failed to perform action'), 'error');
            });
        },
        
        _performSubscriptionAction: function (action, subscriptionId) {
            var self = this;
            this._rpc({
                route: '/my/saas/subscription/action',
                params: {
                    action: action,
                    subscription_id: subscriptionId
                },
            }).then(function (result) {
                if (result.success) {
                    self._showMessage(_t('Action performed successfully'), 'success');
                    self._refreshData();
                } else {
                    self._showMessage(_t('Failed to perform action'), 'error');
                }
            }).catch(function (error) {
                console.error('Failed to perform subscription action:', error);
                self._showMessage(_t('Failed to perform action'), 'error');
            });
        },
        
        _refreshData: function () {
            this._loadInstances();
            this._loadSubscriptions();
        },
        
        _showMessage: function (message, type) {
            var alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
            var $alert = $('<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
                message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                '</div>');
            
            this.$('.portal-messages').append($alert);
            
            // Auto-remove after 5 seconds
            setTimeout(function () {
                $alert.fadeOut(function () {
                    $(this).remove();
                });
            }, 5000);
        },
        
        // Public methods
        refreshInstances: function () {
            this._loadInstances();
        },
        
        refreshSubscriptions: function () {
            this._loadSubscriptions();
        },
        
        showInstanceDetails: function (instanceId) {
            var self = this;
            this._rpc({
                route: '/my/saas/instance/details',
                params: {
                    instance_id: instanceId
                },
            }).then(function (details) {
                self._showInstanceModal(details);
            }).catch(function (error) {
                console.error('Failed to load instance details:', error);
            });
        },
        
        _showInstanceModal: function (details) {
            var $modal = $(QWeb.render('saas_instance_modal', {
                details: details
            }));
            $('body').append($modal);
            $modal.modal('show');
            
            $modal.on('hidden.bs.modal', function () {
                $modal.remove();
            });
        },
    });

    // Register the widget
    publicWidget.registry.saasPortal = SaasPortal;

    return SaasPortal;
}); 