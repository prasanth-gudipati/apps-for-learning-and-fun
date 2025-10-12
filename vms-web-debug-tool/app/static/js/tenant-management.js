// Tenant Management JavaScript

class TenantManager {
    constructor() {
        this.tenants = [];
        this.filteredTenants = [];
        this.currentTenant = null;
        this.tenantDetailModal = null;

        this.init();
    }

    init() {
        // Initialize modal
        this.tenantDetailModal = new bootstrap.Modal(document.getElementById('tenantDetailModal'));

        // Load tenant data
        this.loadTenantData();
    }

    async loadTenantData() {
        try {
            const response = await fetch('/api/tenant/list');
            const result = await response.json();

            if (result.success) {
                this.tenants = result.data;
                this.filteredTenants = [...this.tenants];
                this.renderTenants();
                this.updateStatistics();
            } else {
                this.showError('Failed to load tenant data: ' + result.error);
            }
        } catch (error) {
            this.showError('Error loading tenant data: ' + error.message);
        }
    }

    renderTenants() {
        const container = document.getElementById('tenant-container');

        if (this.filteredTenants.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <h5>No tenants found</h5>
                    <p class="text-muted">No tenants match your current filter criteria.</p>
                </div>
            `;
            return;
        }

        const tenantsHtml = this.filteredTenants.map(tenant => this.createTenantCard(tenant)).join('');
        container.innerHTML = tenantsHtml;
    }

    createTenantCard(tenant) {
        const hasRedis = tenant.redis_info && tenant.redis_info.cluster_ip;
        const keyCount = hasRedis && tenant.redis_info.keys ? tenant.redis_info.keys.length : 0;
        const serviceCount = tenant.services ? tenant.services.length : 0;

        return `
            <div class="card tenant-card" onclick="viewTenantDetails('${tenant.name}')">
                <div class="tenant-header">
                    <div>
                        <div class="tenant-name">${tenant.name}</div>
                        <div class="tenant-info">
                            ${serviceCount} service${serviceCount !== 1 ? 's' : ''}
                            ${hasRedis ? ` • ${keyCount} Redis key${keyCount !== 1 ? 's' : ''}` : ' • No Redis'}
                        </div>
                    </div>
                    <div>
                        ${hasRedis ? '<i class="fas fa-database text-success"></i>' : '<i class="fas fa-database text-muted"></i>'}
                    </div>
                </div>
                <div class="tenant-body">
                    <div class="mb-3">
                        <strong>Services:</strong><br>
                        ${tenant.services ? tenant.services.map(service =>
            `<span class="service-badge">${service}</span>`
        ).join('') : '<span class="text-muted">No services</span>'}
                    </div>
                    
                    ${hasRedis ? `
                        <div class="mb-3">
                            <strong>Redis Information:</strong><br>
                            <small class="text-muted">
                                <i class="fas fa-server"></i> ${tenant.redis_info.cluster_ip}
                                ${tenant.redis_info.ports ? ` • Port: ${tenant.redis_info.ports}` : ''}
                            </small>
                        </div>
                        
                        ${keyCount > 0 ? `
                            <div>
                                <strong>Redis Keys (${keyCount}):</strong><br>
                                <div class="redis-keys-preview">
                                    ${tenant.redis_info.keys.slice(0, 3).map(key =>
            `<code class="me-2">${key}</code>`
        ).join('')}
                                    ${keyCount > 3 ? `<small class="text-muted">... and ${keyCount - 3} more</small>` : ''}
                                </div>
                            </div>
                        ` : ''}
                    ` : ''}
                </div>
            </div>
        `;
    }

    async viewTenantDetails(tenantName) {
        const tenant = this.tenants.find(t => t.name === tenantName);
        if (!tenant) return;

        this.currentTenant = tenant;

        // Set modal title
        document.getElementById('modal-tenant-name').textContent = tenant.name;

        // Render services
        const servicesHtml = tenant.services && tenant.services.length > 0
            ? tenant.services.map(service => `<span class="service-badge d-block mb-1">${service}</span>`).join('')
            : '<span class="text-muted">No services</span>';
        document.getElementById('modal-services').innerHTML = servicesHtml;

        // Render Redis info
        if (tenant.redis_info && tenant.redis_info.cluster_ip) {
            const redisInfoHtml = `
                <div class="card">
                    <div class="card-body p-3">
                        <div class="mb-2">
                            <strong>Service:</strong> ${tenant.redis_info.service_name || 'N/A'}
                        </div>
                        <div class="mb-2">
                            <strong>Type:</strong> ${tenant.redis_info.service_type || 'N/A'}
                        </div>
                        <div class="mb-2">
                            <strong>Cluster IP:</strong> 
                            <code>${tenant.redis_info.cluster_ip}</code>
                        </div>
                        <div class="mb-2">
                            <strong>External IP:</strong> ${tenant.redis_info.external_ip || 'N/A'}
                        </div>
                        <div class="mb-2">
                            <strong>Ports:</strong> ${tenant.redis_info.ports || 'N/A'}
                        </div>
                        <div>
                            <strong>Age:</strong> ${tenant.redis_info.age || 'N/A'}
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('modal-redis-info').innerHTML = redisInfoHtml;
        } else {
            document.getElementById('modal-redis-info').innerHTML = '<span class="text-muted">No Redis service found</span>';
        }

        // Render Redis keys
        if (tenant.redis_info && tenant.redis_info.keys && tenant.redis_info.keys.length > 0) {
            const keysHtml = `
                <div style="max-height: 400px; overflow-y: auto;">
                    ${tenant.redis_info.keys.map(key => `
                        <div class="redis-key-item" onclick="viewRedisKey('${tenant.name}', '${key}')">
                            <div class="redis-key-name">${key}</div>
                        </div>
                    `).join('')}
                </div>
                <div class="mt-2">
                    <small class="text-muted">Total: ${tenant.redis_info.keys.length} keys</small>
                </div>
            `;
            document.getElementById('modal-redis-keys').innerHTML = keysHtml;
        } else {
            document.getElementById('modal-redis-keys').innerHTML = '<span class="text-muted">No Redis keys found</span>';
        }

        // Show modal
        this.tenantDetailModal.show();
    }

    async viewRedisKey(tenantName, keyName) {
        try {
            const response = await fetch(`/api/redis/key-value/${encodeURIComponent(keyName)}?tenant=${encodeURIComponent(tenantName)}`);
            const result = await response.json();

            if (result.success) {
                // Show key value in a new modal or expand in place
                this.showKeyValueModal(keyName, result.data);
            } else {
                this.showError('Failed to load key value: ' + result.error);
            }
        } catch (error) {
            this.showError('Error loading key value: ' + error.message);
        }
    }

    showKeyValueModal(keyName, keyData) {
        // Create and show a modal for key value
        const modalHtml = `
            <div class="modal fade" id="keyValueModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-key"></i> Redis Key Details
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <strong>Key:</strong> <code>${keyName}</code>
                            </div>
                            <div class="mb-3">
                                <strong>Type:</strong> <span class="badge bg-primary">${keyData.type || 'string'}</span>
                            </div>
                            <div class="mb-3">
                                <strong>Value:</strong>
                                <div class="redis-key-value">${this.formatKeyValue(keyData.value)}</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('keyValueModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const keyValueModal = new bootstrap.Modal(document.getElementById('keyValueModal'));
        keyValueModal.show();

        // Clean up modal after hiding
        document.getElementById('keyValueModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    }

    formatKeyValue(value) {
        if (typeof value === 'string') {
            try {
                // Try to parse as JSON for pretty printing
                const jsonValue = JSON.parse(value);
                return JSON.stringify(jsonValue, null, 2);
            } catch (e) {
                // Not JSON, return as is
                return value;
            }
        } else if (typeof value === 'object') {
            return JSON.stringify(value, null, 2);
        }
        return String(value);
    }

    filterTenants() {
        const searchTerm = document.getElementById('tenant-search').value.toLowerCase();
        const serviceFilter = document.getElementById('service-filter').value;

        this.filteredTenants = this.tenants.filter(tenant => {
            // Name filter
            const matchesName = tenant.name.toLowerCase().includes(searchTerm);

            // Service filter
            let matchesService = true;
            if (serviceFilter === 'redis') {
                matchesService = tenant.redis_info && tenant.redis_info.cluster_ip;
            } else if (serviceFilter === 'no-redis') {
                matchesService = !tenant.redis_info || !tenant.redis_info.cluster_ip;
            }

            return matchesName && matchesService;
        });

        this.renderTenants();
        this.updateStatistics();
    }

    sortTenants() {
        const sortBy = document.getElementById('sort-by').value;

        this.filteredTenants.sort((a, b) => {
            switch (sortBy) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'services':
                    const aServices = a.services ? a.services.length : 0;
                    const bServices = b.services ? b.services.length : 0;
                    return bServices - aServices;
                case 'keys':
                    const aKeys = a.redis_info && a.redis_info.keys ? a.redis_info.keys.length : 0;
                    const bKeys = b.redis_info && b.redis_info.keys ? b.redis_info.keys.length : 0;
                    return bKeys - aKeys;
                default:
                    return 0;
            }
        });

        this.renderTenants();
    }

    updateStatistics() {
        const totalTenants = this.filteredTenants.length;
        const redisTenants = this.filteredTenants.filter(t => t.redis_info && t.redis_info.cluster_ip).length;
        const totalServices = this.filteredTenants.reduce((sum, t) => sum + (t.services ? t.services.length : 0), 0);
        const totalKeys = this.filteredTenants.reduce((sum, t) =>
            sum + (t.redis_info && t.redis_info.keys ? t.redis_info.keys.length : 0), 0);

        document.getElementById('total-tenants').textContent = totalTenants;
        document.getElementById('redis-tenants').textContent = redisTenants;
        document.getElementById('total-services').textContent = totalServices;
        document.getElementById('total-keys').textContent = totalKeys;
    }

    async refreshTenantData() {
        document.getElementById('tenant-container').innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Refreshing tenant data...</p>
            </div>
        `;

        await this.loadTenantData();
    }

    async exportTenantData() {
        try {
            const response = await fetch('/api/tenant/export', {
                method: 'POST'
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `tenant-data-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                this.showError('Failed to export tenant data');
            }
        } catch (error) {
            this.showError('Error exporting tenant data: ' + error.message);
        }
    }

    async exportTenantDetails() {
        if (!this.currentTenant) return;

        const dataStr = JSON.stringify(this.currentTenant, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentTenant.name}-details.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    showError(message) {
        // Show error toast
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

        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Global variables and functions
let tenantManager;

window.onload = function () {
    tenantManager = new TenantManager();
};

function filterTenants() {
    tenantManager.filterTenants();
}

function sortTenants() {
    tenantManager.sortTenants();
}

function viewTenantDetails(tenantName) {
    tenantManager.viewTenantDetails(tenantName);
}

function refreshTenantData() {
    tenantManager.refreshTenantData();
}

function exportTenantData() {
    tenantManager.exportTenantData();
}

function exportTenantDetails() {
    tenantManager.exportTenantDetails();
}