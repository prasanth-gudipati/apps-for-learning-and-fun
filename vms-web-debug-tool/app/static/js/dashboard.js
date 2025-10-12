// VMS Debug Tool Dashboard JavaScript

class VMSDebugTool {
    constructor() {
        this.socket = null;
        this.connectionId = null;
        this.isConnected = false;
        this.progressModal = null;
        this.connectionModal = null;

        this.init();
    }

    init() {
        // Initialize Socket.IO
        this.socket = io();
        this.setupSocketHandlers();

        // Initialize Bootstrap modals
        this.progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
        this.connectionModal = new bootstrap.Modal(document.getElementById('connectionModal'));

        // Load initial data
        this.loadSystemOverview();
        this.loadQuickStats();

        // Set up periodic updates
        setInterval(() => {
            if (this.isConnected) {
                this.loadSystemOverview();
                this.loadQuickStats();
            }
        }, 30000); // Update every 30 seconds
    }

    setupSocketHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });

        this.socket.on('progress_update', (data) => {
            this.updateProgress(data.message, data.progress || 0);
        });

        this.socket.on('operation_complete', (data) => {
            this.operationComplete(data);
        });

        this.socket.on('operation_error', (data) => {
            this.operationError(data);
        });
    }

    // Connection Management
    showConnectionModal() {
        this.connectionModal.show();
    }

    async connectSSH() {
        const form = document.getElementById('connection-form');
        const formData = new FormData(form);

        const connectionData = {
            hostname: formData.get('hostname'),
            username: formData.get('username'),
            password: formData.get('password'),
            port: parseInt(formData.get('port')) || 22
        };

        try {
            const response = await fetch('/api/ssh/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(connectionData)
            });

            const result = await response.json();

            if (result.success) {
                this.connectionId = result.connection_id;
                this.isConnected = true;
                this.updateConnectionStatus(true, connectionData.hostname);
                this.connectionModal.hide();
                this.addActivityLog('success', `Connected to ${connectionData.hostname}`);
                this.loadSystemOverview();
            } else {
                this.showError('Connection failed: ' + result.error);
            }
        } catch (error) {
            this.showError('Connection error: ' + error.message);
        }
    }

    async disconnect() {
        if (!this.connectionId) return;

        try {
            await fetch(`/api/ssh/disconnect/${this.connectionId}`, {
                method: 'POST'
            });

            this.connectionId = null;
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.addActivityLog('info', 'Disconnected from server');
            this.clearSystemOverview();
        } catch (error) {
            console.error('Disconnect error:', error);
        }
    }

    updateConnectionStatus(connected, hostname = '') {
        const statusElement = document.getElementById('connection-status');
        const connectionInfo = document.getElementById('connection-info');

        if (connected) {
            statusElement.innerHTML = `<span class="connection-indicator connected"></span>Connected`;
            connectionInfo.textContent = hostname;
        } else {
            statusElement.innerHTML = `<span class="connection-indicator disconnected"></span>Not Connected`;
            connectionInfo.textContent = 'None';
        }
    }

    // System Overview
    async loadSystemOverview() {
        if (!this.isConnected || !this.connectionId) {
            this.clearSystemOverview();
            return;
        }

        try {
            const response = await fetch(`/api/vms/system-overview/${this.connectionId}`);
            const data = await response.json();

            if (data.success) {
                document.getElementById('namespace-count').textContent = data.data.namespace_count;
                document.getElementById('pod-count').textContent = data.data.pod_count;
                document.getElementById('service-count').textContent = data.data.service_count;
                document.getElementById('pv-count').textContent = data.data.pv_count;
            }
        } catch (error) {
            console.error('Load system overview error:', error);
        }
    }

    clearSystemOverview() {
        document.getElementById('namespace-count').textContent = '-';
        document.getElementById('pod-count').textContent = '-';
        document.getElementById('service-count').textContent = '-';
        document.getElementById('pv-count').textContent = '-';
    }

    // Quick Stats
    async loadQuickStats() {
        try {
            const response = await fetch('/api/tenant/stats');
            const data = await response.json();

            if (data.success) {
                document.getElementById('tenant-total').textContent = data.data.tenant_count;
                document.getElementById('redis-keys-total').textContent = data.data.redis_keys_count;

                if (data.data.last_scan) {
                    const lastScan = new Date(data.data.last_scan).toLocaleString();
                    document.getElementById('last-scan').textContent = lastScan;
                }
            }
        } catch (error) {
            console.error('Load quick stats error:', error);
        }
    }

    // Operations
    async runStatusCheck() {
        if (!this.isConnected || !this.connectionId) {
            this.showError('Please connect to a VMS server first');
            return;
        }

        this.showProgressModal('VMS Status Check', 'Initializing status check...');
        this.disableButton('status-check-btn');

        try {
            const response = await fetch(`/api/vms/status-check/${this.connectionId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.addActivityLog('success', 'VMS status check completed');
            } else {
                this.addActivityLog('error', 'VMS status check failed: ' + result.error);
            }
        } catch (error) {
            this.addActivityLog('error', 'Status check error: ' + error.message);
        } finally {
            this.enableButton('status-check-btn');
        }
    }

    async collectTenantData() {
        if (!this.isConnected || !this.connectionId) {
            this.showError('Please connect to a VMS server first');
            return;
        }

        const includeRedisKeys = document.getElementById('include-redis-keys').checked;

        this.showProgressModal('Tenant Data Collection', 'Starting tenant data collection...');
        this.disableButton('tenant-data-btn');

        try {
            const response = await fetch(`/api/vms/collect-tenant-data/${this.connectionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    include_redis_keys: includeRedisKeys
                })
            });

            const result = await response.json();

            if (result.success) {
                this.addActivityLog('success', `Tenant data collection completed. Found ${result.data.tenant_count} tenants`);
                this.loadQuickStats();
            } else {
                this.addActivityLog('error', 'Tenant data collection failed: ' + result.error);
            }
        } catch (error) {
            this.addActivityLog('error', 'Tenant data collection error: ' + error.message);
        } finally {
            this.enableButton('tenant-data-btn');
        }
    }

    async exportConfigMaps() {
        if (!this.isConnected || !this.connectionId) {
            this.showError('Please connect to a VMS server first');
            return;
        }

        this.showProgressModal('ConfigMaps Export', 'Starting ConfigMaps export...');
        this.disableButton('configmaps-btn');

        try {
            const response = await fetch(`/api/vms/export-configmaps/${this.connectionId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.addActivityLog('success', 'ConfigMaps export completed');
            } else {
                this.addActivityLog('error', 'ConfigMaps export failed: ' + result.error);
            }
        } catch (error) {
            this.addActivityLog('error', 'ConfigMaps export error: ' + error.message);
        } finally {
            this.enableButton('configmaps-btn');
        }
    }

    // Progress Modal
    showProgressModal(title, message) {
        document.getElementById('progress-title').textContent = title;
        document.getElementById('progress-message').textContent = message;
        document.getElementById('progress-bar').style.width = '0%';
        document.getElementById('progress-log').innerHTML = '';
        document.getElementById('progress-close-btn').style.display = 'none';
        this.progressModal.show();
    }

    updateProgress(message, progress) {
        document.getElementById('progress-message').textContent = message;

        if (progress > 0) {
            document.getElementById('progress-bar').style.width = progress + '%';
        }

        // Add to progress log
        const progressLog = document.getElementById('progress-log');
        const logItem = document.createElement('div');
        logItem.className = 'progress-log-item';
        logItem.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        progressLog.appendChild(logItem);
        progressLog.scrollTop = progressLog.scrollHeight;
    }

    operationComplete(data) {
        document.getElementById('progress-bar').style.width = '100%';
        document.getElementById('progress-message').textContent = 'Operation completed successfully';
        document.getElementById('progress-close-btn').style.display = 'block';

        setTimeout(() => {
            this.progressModal.hide();
        }, 2000);
    }

    operationError(data) {
        document.getElementById('progress-message').textContent = 'Operation failed: ' + data.error;
        document.getElementById('progress-close-btn').style.display = 'block';
    }

    // Activity Log
    addActivityLog(type, message) {
        const activityLog = document.getElementById('activity-log');
        const timestamp = new Date().toLocaleTimeString();

        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';

        let iconClass = 'fas fa-info-circle text-info';
        if (type === 'success') iconClass = 'fas fa-check-circle text-success';
        else if (type === 'error') iconClass = 'fas fa-exclamation-circle text-danger';
        else if (type === 'warning') iconClass = 'fas fa-exclamation-triangle text-warning';

        activityItem.innerHTML = `
            <div class="activity-timestamp">${timestamp}</div>
            <div class="activity-message">
                <i class="${iconClass}"></i> ${message}
            </div>
        `;

        // Insert at the top
        activityLog.insertBefore(activityItem, activityLog.firstChild);

        // Remove oldest items if more than 50
        while (activityLog.children.length > 50) {
            activityLog.removeChild(activityLog.lastChild);
        }
    }

    // Utility Methods
    disableButton(buttonId) {
        const button = document.getElementById(buttonId);
        button.disabled = true;
        button.innerHTML = button.innerHTML.replace('fa-play', 'fa-spinner fa-spin');
    }

    enableButton(buttonId) {
        const button = document.getElementById(buttonId);
        button.disabled = false;
        button.innerHTML = button.innerHTML.replace('fa-spinner fa-spin', 'fa-play');
    }

    showError(message) {
        this.addActivityLog('error', message);

        // Show toast notification if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            // Create and show toast
            const toastHtml = `
                <div class="toast align-items-center text-white bg-danger border-0" role="alert">
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class="fas fa-exclamation-circle me-2"></i>${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;

            // Add toast to container (create if doesn't exist)
            let toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'toast-container';
                toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
                document.body.appendChild(toastContainer);
            }

            toastContainer.insertAdjacentHTML('beforeend', toastHtml);
            const toastElement = toastContainer.lastElementChild;
            const toast = new bootstrap.Toast(toastElement);
            toast.show();

            // Remove from DOM after hiding
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
        }
    }

    showSuccess(message) {
        this.addActivityLog('success', message);
    }
}

// Global functions for HTML onclick handlers
let vmsApp;

window.onload = function () {
    vmsApp = new VMSDebugTool();
};

function showConnectionModal() {
    vmsApp.showConnectionModal();
}

function connectSSH() {
    vmsApp.connectSSH();
}

function disconnect() {
    vmsApp.disconnect();
}

function runStatusCheck() {
    vmsApp.runStatusCheck();
}

function collectTenantData() {
    vmsApp.collectTenantData();
}

function exportConfigMaps() {
    vmsApp.exportConfigMaps();
}