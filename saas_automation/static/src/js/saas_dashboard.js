// Static JS file for SaaS Dashboard
odoo.define('saas_automation.dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var publicWidget = require('web.public.widget');

    var QWeb = core.qweb;
    var _t = core._t;

    // SaaS Dashboard Widget
    var SaasDashboard = Widget.extend({
        template: 'saas_dashboard_template',
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.options = options || {};
        },
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initDashboard();
            });
        },
        
        _initDashboard: function () {
            // Initialize dashboard functionality
            this._updateMetrics();
            this._setupRefreshTimer();
        },
        
        _updateMetrics: function () {
            var self = this;
            // Update dashboard metrics
            this._rpc({
                route: '/saas/dashboard/metrics',
                params: {},
            }).then(function (data) {
                self._displayMetrics(data);
            }).catch(function (error) {
                console.error('Failed to update dashboard metrics:', error);
            });
        },
        
        _displayMetrics: function (data) {
            // Display metrics in the dashboard
            if (data.total_instances !== undefined) {
                this.$('.total-instances').text(data.total_instances);
            }
            if (data.active_instances !== undefined) {
                this.$('.active-instances').text(data.active_instances);
            }
            if (data.active_users !== undefined) {
                this.$('.active-users').text(data.active_users);
            }
            if (data.mrr !== undefined) {
                this.$('.mrr').text('$' + data.mrr.toFixed(2));
            }
        },
        
        _setupRefreshTimer: function () {
            // Refresh dashboard every 30 seconds
            setInterval(function () {
                this._updateMetrics();
            }.bind(this), 30000);
        },
    });

    // Register the widget
    core.action_registry.add('saas_dashboard', SaasDashboard);

    return SaasDashboard;
}); 