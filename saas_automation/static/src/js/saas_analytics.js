// Static JS file for SaaS Analytics
odoo.define('saas_automation.analytics', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    // SaaS Analytics Widget
    var SaasAnalytics = Widget.extend({
        template: 'saas_analytics_template',
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.options = options || {};
        },
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initAnalytics();
            });
        },
        
        _initAnalytics: function () {
            this._loadAnalyticsData();
            this._setupCharts();
        },
        
        _loadAnalyticsData: function () {
            var self = this;
            this._rpc({
                route: '/saas/analytics/data',
                params: {},
            }).then(function (data) {
                self._displayAnalytics(data);
            }).catch(function (error) {
                console.error('Failed to load analytics data:', error);
            });
        },
        
        _displayAnalytics: function (data) {
            // Display analytics data
            if (data.mrr_trend) {
                this._updateMRRChart(data.mrr_trend);
            }
            if (data.instance_growth) {
                this._updateInstanceChart(data.instance_growth);
            }
            if (data.churn_rate) {
                this.$('.churn-rate').text(data.churn_rate.toFixed(2) + '%');
            }
        },
        
        _setupCharts: function () {
            // Initialize charts if Chart.js is available
            if (typeof Chart !== 'undefined') {
                this._createMRRChart();
                this._createInstanceChart();
            }
        },
        
        _createMRRChart: function () {
            var ctx = this.$('.mrr-chart')[0];
            if (ctx) {
                this.mrrChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'MRR',
                            data: [],
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        },
        
        _createInstanceChart: function () {
            var ctx = this.$('.instance-chart')[0];
            if (ctx) {
                this.instanceChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Instances',
                            data: [],
                            backgroundColor: '#764ba2'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        },
        
        _updateMRRChart: function (data) {
            if (this.mrrChart) {
                this.mrrChart.data.labels = data.labels;
                this.mrrChart.data.datasets[0].data = data.values;
                this.mrrChart.update();
            }
        },
        
        _updateInstanceChart: function (data) {
            if (this.instanceChart) {
                this.instanceChart.data.labels = data.labels;
                this.instanceChart.data.datasets[0].data = data.values;
                this.instanceChart.update();
            }
        },
    });

    // Register the widget
    core.action_registry.add('saas_analytics', SaasAnalytics);

    return SaasAnalytics;
}); 