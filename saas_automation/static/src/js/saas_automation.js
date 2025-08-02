// Static JS file for SaaS Automation
odoo.define('saas_automation.automation', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    // SaaS Automation Widget
    var SaasAutomation = Widget.extend({
        template: 'saas_automation_template',
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.options = options || {};
        },
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initAutomation();
            });
        },
        
        _initAutomation: function () {
            this._loadAutomationRules();
            this._setupEventListeners();
        },
        
        _loadAutomationRules: function () {
            var self = this;
            this._rpc({
                route: '/saas/automation/rules',
                params: {},
            }).then(function (rules) {
                self._displayRules(rules);
            }).catch(function (error) {
                console.error('Failed to load automation rules:', error);
            });
        },
        
        _displayRules: function (rules) {
            // Display automation rules
            var $rulesContainer = this.$('.automation-rules');
            $rulesContainer.empty();
            
            rules.forEach(function (rule) {
                var $ruleElement = $(QWeb.render('saas_automation_rule', {
                    rule: rule
                }));
                $rulesContainer.append($ruleElement);
            });
        },
        
        _setupEventListeners: function () {
            var self = this;
            
            // Rule activation toggle
            this.$('.rule-toggle').on('change', function () {
                var ruleId = $(this).data('rule-id');
                var isActive = $(this).is(':checked');
                self._toggleRule(ruleId, isActive);
            });
            
            // Execute rule manually
            this.$('.execute-rule').on('click', function () {
                var ruleId = $(this).data('rule-id');
                self._executeRule(ruleId);
            });
        },
        
        _toggleRule: function (ruleId, isActive) {
            var self = this;
            this._rpc({
                route: '/saas/automation/toggle_rule',
                params: {
                    rule_id: ruleId,
                    is_active: isActive
                },
            }).then(function (result) {
                if (result.success) {
                    self._showNotification(_t('Rule updated successfully'), 'success');
                } else {
                    self._showNotification(_t('Failed to update rule'), 'danger');
                }
            }).catch(function (error) {
                console.error('Failed to toggle rule:', error);
                self._showNotification(_t('Failed to update rule'), 'danger');
            });
        },
        
        _executeRule: function (ruleId) {
            var self = this;
            this._rpc({
                route: '/saas/automation/execute_rule',
                params: {
                    rule_id: ruleId
                },
            }).then(function (result) {
                if (result.success) {
                    self._showNotification(_t('Rule executed successfully'), 'success');
                } else {
                    self._showNotification(_t('Failed to execute rule'), 'danger');
                }
            }).catch(function (error) {
                console.error('Failed to execute rule:', error);
                self._showNotification(_t('Failed to execute rule'), 'danger');
            });
        },
        
        _showNotification: function (message, type) {
            // Show notification message
            var notificationClass = type === 'success' ? 'alert-success' : 'alert-danger';
            var $notification = $('<div class="alert ' + notificationClass + ' alert-dismissible fade show" role="alert">' +
                message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                '</div>');
            
            this.$('.notifications').append($notification);
            
            // Auto-remove after 5 seconds
            setTimeout(function () {
                $notification.fadeOut(function () {
                    $(this).remove();
                });
            }, 5000);
        },
        
        // Public methods
        refreshRules: function () {
            this._loadAutomationRules();
        },
        
        addRule: function (ruleData) {
            var self = this;
            this._rpc({
                route: '/saas/automation/add_rule',
                params: ruleData,
            }).then(function (result) {
                if (result.success) {
                    self._showNotification(_t('Rule added successfully'), 'success');
                    self.refreshRules();
                } else {
                    self._showNotification(_t('Failed to add rule'), 'danger');
                }
            }).catch(function (error) {
                console.error('Failed to add rule:', error);
                self._showNotification(_t('Failed to add rule'), 'danger');
            });
        },
        
        deleteRule: function (ruleId) {
            var self = this;
            if (confirm(_t('Are you sure you want to delete this rule?'))) {
                this._rpc({
                    route: '/saas/automation/delete_rule',
                    params: {
                        rule_id: ruleId
                    },
                }).then(function (result) {
                    if (result.success) {
                        self._showNotification(_t('Rule deleted successfully'), 'success');
                        self.refreshRules();
                    } else {
                        self._showNotification(_t('Failed to delete rule'), 'danger');
                    }
                }).catch(function (error) {
                    console.error('Failed to delete rule:', error);
                    self._showNotification(_t('Failed to delete rule'), 'danger');
                });
            }
        },
    });

    // Register the widget
    core.action_registry.add('saas_automation', SaasAutomation);

    return SaasAutomation;
}); 