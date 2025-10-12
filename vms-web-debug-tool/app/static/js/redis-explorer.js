// Redis Explorer JavaScript

class RedisExplorer {
    constructor() {
        this.allKeys = [];
        this.filteredKeys = [];
        this.currentPage = 1;
        this.keysPerPage = 50;
        this.currentKey = null;
        this.keyDetailModal = null;
        this.keyAnalysisModal = null;

        this.init();
    }

    init() {
        // Initialize modals
        this.keyDetailModal = new bootstrap.Modal(document.getElementById('keyDetailModal'));
        this.keyAnalysisModal = new bootstrap.Modal(document.getElementById('keyAnalysisModal'));

        // Load Redis data
        this.loadRedisKeys();
    }

    async loadRedisKeys() {
        try {
            const response = await fetch('/api/redis/keys');
            const result = await response.json();

            if (result.success) {
                this.allKeys = result.data;
                this.filteredKeys = [...this.allKeys];
                this.populateFilters();
                this.renderKeys();
                this.updateStatistics();
            } else {
                this.showError('Failed to load Redis keys: ' + result.error);
            }
        } catch (error) {
            this.showError('Error loading Redis keys: ' + error.message);
        }
    }

    populateFilters() {
        // Populate tenant filter
        const tenants = [...new Set(this.allKeys.map(key => key.tenant))].sort();
        const tenantFilter = document.getElementById('tenant-filter');

        // Clear existing options except "All Tenants"
        while (tenantFilter.children.length > 1) {
            tenantFilter.removeChild(tenantFilter.lastChild);
        }

        // Add tenant options
        tenants.forEach(tenant => {
            const option = document.createElement('option');
            option.value = tenant;
            option.textContent = tenant;
            tenantFilter.appendChild(option);
        });
    }

    renderKeys() {
        const container = document.getElementById('redis-keys-container');
        const totalKeys = this.filteredKeys.length;

        if (totalKeys === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-key fa-3x text-muted mb-3"></i>
                    <h5>No Redis keys found</h5>
                    <p class="text-muted">No keys match your current filter criteria.</p>
                </div>
            `;
            this.hidePagination();
            return;
        }

        // Calculate pagination
        const totalPages = Math.ceil(totalKeys / this.keysPerPage);
        const startIndex = (this.currentPage - 1) * this.keysPerPage;
        const endIndex = Math.min(startIndex + this.keysPerPage, totalKeys);
        const pageKeys = this.filteredKeys.slice(startIndex, endIndex);

        // Render keys
        const keysHtml = pageKeys.map(key => this.createKeyCard(key)).join('');
        container.innerHTML = `
            <div class="row">
                ${keysHtml}
            </div>
        `;

        // Update pagination
        this.updatePagination(totalPages);

        // Update counts
        document.getElementById('keys-count').textContent = totalKeys;
    }

    createKeyCard(key) {
        return `
            <div class="col-lg-4 col-md-6 mb-3">
                <div class="redis-key-item" onclick="viewKeyDetails('${key.tenant}', '${key.name}')">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="redis-key-name">${key.name}</div>
                        <span class="redis-key-type">${key.type || 'string'}</span>
                    </div>
                    <div class="mb-2">
                        <small class="text-muted">
                            <i class="fas fa-user"></i> ${key.tenant}
                        </small>
                    </div>
                    ${key.preview_value ? `
                        <div class="redis-key-value">
                            ${this.truncateValue(key.preview_value, 100)}
                        </div>
                    ` : ''}
                    <div class="mt-2">
                        <small class="text-muted">
                            ${key.size ? `Size: ${this.formatSize(key.size)} • ` : ''}
                            ${key.ttl ? `TTL: ${key.ttl}s` : 'No TTL'}
                        </small>
                    </div>
                </div>
            </div>
        `;
    }

    async viewKeyDetails(tenant, keyName) {
        try {
            const response = await fetch(`/api/redis/key-value/${encodeURIComponent(keyName)}?tenant=${encodeURIComponent(tenant)}`);
            const result = await response.json();

            if (result.success) {
                this.currentKey = { tenant, name: keyName, ...result.data };
                this.renderKeyDetailModal();
                this.keyDetailModal.show();
            } else {
                this.showError('Failed to load key details: ' + result.error);
            }
        } catch (error) {
            this.showError('Error loading key details: ' + error.message);
        }
    }

    renderKeyDetailModal() {
        if (!this.currentKey) return;

        // Set modal title
        document.getElementById('modal-key-name').textContent = this.currentKey.name;

        // Render key info
        const keyInfo = `
            <div class="card">
                <div class="card-body p-3">
                    <div class="mb-2">
                        <strong>Tenant:</strong> ${this.currentKey.tenant}
                    </div>
                    <div class="mb-2">
                        <strong>Type:</strong> 
                        <span class="badge bg-primary">${this.currentKey.type || 'string'}</span>
                    </div>
                    <div class="mb-2">
                        <strong>Size:</strong> ${this.formatSize(this.currentKey.size) || 'Unknown'}
                    </div>
                    <div class="mb-2">
                        <strong>TTL:</strong> ${this.currentKey.ttl ? `${this.currentKey.ttl}s` : 'No expiration'}
                    </div>
                    <div>
                        <strong>Encoding:</strong> ${this.currentKey.encoding || 'Unknown'}
                    </div>
                </div>
            </div>
        `;
        document.getElementById('modal-key-info').innerHTML = keyInfo;

        // Render key value
        const formattedValue = this.formatKeyValue(this.currentKey.value, this.currentKey.type);
        document.getElementById('modal-key-value').innerHTML = `
            <div class="redis-key-value" style="max-height: 500px;">${formattedValue}</div>
        `;
    }

    formatKeyValue(value, type) {
        if (!value) return '<em class="text-muted">No value</em>';

        switch (type) {
            case 'hash':
                if (typeof value === 'object') {
                    return Object.entries(value)
                        .map(([field, val]) => `<strong>${field}:</strong> ${val}`)
                        .join('<br>');
                }
                break;
            case 'list':
                if (Array.isArray(value)) {
                    return value
                        .map((item, index) => `<strong>[${index}]:</strong> ${item}`)
                        .join('<br>');
                }
                break;
            case 'set':
                if (Array.isArray(value)) {
                    return value
                        .map(item => `• ${item}`)
                        .join('<br>');
                }
                break;
            case 'zset':
                if (Array.isArray(value)) {
                    return value
                        .map(item => `<strong>${item.score}:</strong> ${item.member}`)
                        .join('<br>');
                }
                break;
        }

        // Default formatting for strings and other types
        if (typeof value === 'string') {
            try {
                // Try to parse as JSON for pretty printing
                const jsonValue = JSON.parse(value);
                return JSON.stringify(jsonValue, null, 2);
            } catch (e) {
                // Not JSON, return as is with HTML escaping
                return value.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            }
        } else if (typeof value === 'object') {
            return JSON.stringify(value, null, 2);
        }

        return String(value);
    }

    filterKeys() {
        const searchTerm = document.getElementById('key-search').value.toLowerCase();
        const tenantFilter = document.getElementById('tenant-filter').value;
        const typeFilter = document.getElementById('type-filter').value;

        this.filteredKeys = this.allKeys.filter(key => {
            // Name filter
            const matchesName = key.name.toLowerCase().includes(searchTerm);

            // Tenant filter
            const matchesTenant = !tenantFilter || key.tenant === tenantFilter;

            // Type filter
            const matchesType = !typeFilter || key.type === typeFilter;

            return matchesName && matchesTenant && matchesType;
        });

        this.currentPage = 1; // Reset to first page
        this.renderKeys();
        this.updateStatistics();
    }

    sortKeys() {
        const sortBy = document.getElementById('sort-keys').value;

        this.filteredKeys.sort((a, b) => {
            switch (sortBy) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'tenant':
                    return a.tenant.localeCompare(b.tenant);
                case 'type':
                    return (a.type || 'string').localeCompare(b.type || 'string');
                default:
                    return 0;
            }
        });

        this.renderKeys();
    }

    updateStatistics() {
        const totalKeys = this.allKeys.length;
        const uniqueTenants = new Set(this.allKeys.map(key => key.tenant)).size;
        const filteredKeys = this.filteredKeys.length;
        const uniqueTypes = new Set(this.allKeys.map(key => key.type || 'string')).size;

        document.getElementById('total-keys').textContent = totalKeys;
        document.getElementById('unique-tenants').textContent = uniqueTenants;
        document.getElementById('filtered-keys').textContent = filteredKeys;
        document.getElementById('key-types').textContent = uniqueTypes;
    }

    updatePagination(totalPages) {
        if (totalPages <= 1) {
            this.hidePagination();
            return;
        }

        const paginationNav = document.getElementById('pagination-nav');
        const paginationList = document.getElementById('pagination-list');

        // Clear existing pagination
        paginationList.innerHTML = '';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#" onclick="redisExplorer.goToPage(${this.currentPage - 1})">Previous</a>`;
        paginationList.appendChild(prevLi);

        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        if (startPage > 1) {
            const firstLi = document.createElement('li');
            firstLi.className = 'page-item';
            firstLi.innerHTML = `<a class="page-link" href="#" onclick="redisExplorer.goToPage(1)">1</a>`;
            paginationList.appendChild(firstLi);

            if (startPage > 2) {
                const ellipsisLi = document.createElement('li');
                ellipsisLi.className = 'page-item disabled';
                ellipsisLi.innerHTML = '<span class="page-link">...</span>';
                paginationList.appendChild(ellipsisLi);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#" onclick="redisExplorer.goToPage(${i})">${i}</a>`;
            paginationList.appendChild(pageLi);
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsisLi = document.createElement('li');
                ellipsisLi.className = 'page-item disabled';
                ellipsisLi.innerHTML = '<span class="page-link">...</span>';
                paginationList.appendChild(ellipsisLi);
            }

            const lastLi = document.createElement('li');
            lastLi.className = 'page-item';
            lastLi.innerHTML = `<a class="page-link" href="#" onclick="redisExplorer.goToPage(${totalPages})">${totalPages}</a>`;
            paginationList.appendChild(lastLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#" onclick="redisExplorer.goToPage(${this.currentPage + 1})">Next</a>`;
        paginationList.appendChild(nextLi);

        paginationNav.style.display = 'block';
    }

    hidePagination() {
        document.getElementById('pagination-nav').style.display = 'none';
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredKeys.length / this.keysPerPage);

        if (page < 1 || page > totalPages) return;

        this.currentPage = page;
        this.renderKeys();
    }

    async refreshRedisData() {
        document.getElementById('redis-keys-container').innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Refreshing Redis data...</p>
            </div>
        `;

        await this.loadRedisKeys();
    }

    async exportRedisData() {
        try {
            const response = await fetch('/api/redis/export', {
                method: 'POST'
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `redis-keys-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                this.showError('Failed to export Redis data');
            }
        } catch (error) {
            this.showError('Error exporting Redis data: ' + error.message);
        }
    }

    copyKeyValue() {
        if (!this.currentKey || !this.currentKey.value) return;

        const value = typeof this.currentKey.value === 'string'
            ? this.currentKey.value
            : JSON.stringify(this.currentKey.value, null, 2);

        navigator.clipboard.writeText(value).then(() => {
            this.showSuccess('Key value copied to clipboard');
        }).catch(() => {
            this.showError('Failed to copy key value');
        });
    }

    exportKeyData() {
        if (!this.currentKey) return;

        const dataStr = JSON.stringify(this.currentKey, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `redis-key-${this.currentKey.name.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    // Utility methods
    truncateValue(value, maxLength) {
        if (!value) return '';
        const str = typeof value === 'string' ? value : JSON.stringify(value);
        return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
    }

    formatSize(size) {
        if (!size) return 'Unknown';
        if (size < 1024) return `${size} B`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
        return `${(size / (1024 * 1024)).toFixed(1)} MB`;
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

        this.showToast(toastHtml);
    }

    showSuccess(message) {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-success border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas fa-check-circle me-2"></i>${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        this.showToast(toastHtml);
    }

    showToast(toastHtml) {
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
let redisExplorer;

window.onload = function () {
    redisExplorer = new RedisExplorer();
};

function filterKeys() {
    redisExplorer.filterKeys();
}

function sortKeys() {
    redisExplorer.sortKeys();
}

function viewKeyDetails(tenant, keyName) {
    redisExplorer.viewKeyDetails(tenant, keyName);
}

function refreshRedisData() {
    redisExplorer.refreshRedisData();
}

function exportRedisData() {
    redisExplorer.exportRedisData();
}

function copyKeyValue() {
    redisExplorer.copyKeyValue();
}

function exportKeyData() {
    redisExplorer.exportKeyData();
}