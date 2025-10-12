// System Logs JavaScript

class SystemLogsManager {
    constructor() {
        this.allLogs = [];
        this.filteredLogs = [];
        this.currentPage = 1;
        this.logsPerPage = 20;
        this.currentLog = null;
        this.logDetailModal = null;
        this.autoRefreshInterval = null;
        this.autoRefreshEnabled = false;

        this.init();
    }

    init() {
        // Initialize modal
        this.logDetailModal = new bootstrap.Modal(document.getElementById('logDetailModal'));

        // Load system logs
        this.loadSystemLogs();

        // Set today's date as default filter
        document.getElementById('date-filter').valueAsDate = new Date();
    }

    async loadSystemLogs() {
        try {
            const response = await fetch('/api/logs/system');
            const result = await response.json();

            if (result.success) {
                this.allLogs = result.data;
                this.filteredLogs = [...this.allLogs];
                this.populateFilters();
                this.renderLogs();
                this.updateStatistics();
            } else {
                this.showError('Failed to load system logs: ' + result.error);
            }
        } catch (error) {
            this.showError('Error loading system logs: ' + error.message);
        }
    }

    populateFilters() {
        // Populate command filter
        const commands = [...new Set(this.allLogs.map(log => log.command))].sort();
        const commandFilter = document.getElementById('command-filter');

        // Clear existing options except "All Commands"
        while (commandFilter.children.length > 1) {
            commandFilter.removeChild(commandFilter.lastChild);
        }

        // Add command options
        commands.forEach(command => {
            const option = document.createElement('option');
            option.value = command;
            option.textContent = command;
            commandFilter.appendChild(option);
        });
    }

    renderLogs() {
        const container = document.getElementById('logs-container');
        const totalLogs = this.filteredLogs.length;

        if (totalLogs === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-file-alt fa-3x text-muted mb-3"></i>
                    <h5>No log entries found</h5>
                    <p class="text-muted">No logs match your current filter criteria.</p>
                </div>
            `;
            this.hidePagination();
            return;
        }

        // Calculate pagination
        const totalPages = Math.ceil(totalLogs / this.logsPerPage);
        const startIndex = (this.currentPage - 1) * this.logsPerPage;
        const endIndex = Math.min(startIndex + this.logsPerPage, totalLogs);
        const pageLogs = this.filteredLogs.slice(startIndex, endIndex);

        // Render logs
        const logsHtml = pageLogs.map(log => this.createLogCard(log)).join('');
        container.innerHTML = logsHtml;

        // Update pagination
        this.updatePagination(totalPages);

        // Update counts
        document.getElementById('logs-count').textContent = totalLogs;
    }

    createLogCard(log) {
        const timestamp = new Date(log.timestamp).toLocaleString();
        const outputPreview = this.truncateOutput(log.output, 200);
        const hasError = log.metadata && log.metadata.error;

        return `
            <div class="card mb-3 ${hasError ? 'border-danger' : ''}" onclick="viewLogDetails('${log._id}')">
                <div class="card-header d-flex justify-content-between align-items-center ${hasError ? 'bg-danger text-white' : ''}">
                    <div>
                        <strong>${log.command}</strong>
                        ${hasError ? '<i class="fas fa-exclamation-triangle ms-2"></i>' : ''}
                    </div>
                    <small class="${hasError ? 'text-white-50' : 'text-muted'}">${timestamp}</small>
                </div>
                <div class="card-body">
                    ${log.metadata && log.metadata.description ? `
                        <p class="text-muted mb-2">${log.metadata.description}</p>
                    ` : ''}
                    
                    <div class="code-block" style="max-height: 150px; cursor: pointer;">
                        ${outputPreview}
                    </div>
                    
                    <div class="mt-2 d-flex justify-content-between align-items-center">
                        <div>
                            ${log.metadata && log.metadata.output_lines ? `
                                <small class="text-muted">
                                    <i class="fas fa-list"></i> ${log.metadata.output_lines} lines
                                </small>
                            ` : ''}
                            ${log.metadata && log.metadata.export_type ? `
                                <span class="badge bg-info ms-2">${log.metadata.export_type}</span>
                            ` : ''}
                        </div>
                        <small class="text-muted">Click to view full details</small>
                    </div>
                </div>
            </div>
        `;
    }

    async viewLogDetails(logId) {
        const log = this.allLogs.find(l => l._id === logId);
        if (!log) return;

        this.currentLog = log;
        this.renderLogDetailModal();
        this.logDetailModal.show();
    }

    renderLogDetailModal() {
        if (!this.currentLog) return;

        // Set modal title
        document.getElementById('modal-log-title').textContent = this.currentLog.command;

        // Render log info
        const timestamp = new Date(this.currentLog.timestamp).toLocaleString();
        const hasError = this.currentLog.metadata && this.currentLog.metadata.error;

        const logInfo = `
            <div class="card">
                <div class="card-body p-3">
                    <div class="mb-2">
                        <strong>Command:</strong><br>
                        <code>${this.currentLog.command}</code>
                    </div>
                    <div class="mb-2">
                        <strong>Timestamp:</strong> ${timestamp}
                    </div>
                    <div class="mb-2">
                        <strong>Status:</strong> 
                        <span class="badge ${hasError ? 'bg-danger' : 'bg-success'}">
                            ${hasError ? 'Error' : 'Success'}
                        </span>
                    </div>
                    ${this.currentLog.metadata && this.currentLog.metadata.description ? `
                        <div class="mb-2">
                            <strong>Description:</strong><br>
                            ${this.currentLog.metadata.description}
                        </div>
                    ` : ''}
                    ${this.currentLog.metadata && this.currentLog.metadata.output_lines ? `
                        <div class="mb-2">
                            <strong>Output Lines:</strong> ${this.currentLog.metadata.output_lines}
                        </div>
                    ` : ''}
                    ${this.currentLog.metadata && this.currentLog.metadata.output_size ? `
                        <div class="mb-2">
                            <strong>Output Size:</strong> ${this.formatSize(this.currentLog.metadata.output_size)}
                        </div>
                    ` : ''}
                    ${this.currentLog.metadata && this.currentLog.metadata.export_type ? `
                        <div>
                            <strong>Export Type:</strong> 
                            <span class="badge bg-info">${this.currentLog.metadata.export_type}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        document.getElementById('modal-log-info').innerHTML = logInfo;

        // Render log output
        const formattedOutput = this.formatLogOutput(this.currentLog.output);
        document.getElementById('modal-log-output').innerHTML = `
            <div class="code-block" style="max-height: 600px;">
                ${formattedOutput}
            </div>
        `;
    }

    formatLogOutput(output) {
        if (!output) return '<em class="text-muted">No output</em>';

        // Escape HTML and preserve formatting
        const escaped = output
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        return escaped;
    }

    filterLogs() {
        const searchTerm = document.getElementById('log-search').value.toLowerCase();
        const commandFilter = document.getElementById('command-filter').value;
        const dateFilter = document.getElementById('date-filter').value;

        this.filteredLogs = this.allLogs.filter(log => {
            // Text search (command and output)
            const matchesSearch = !searchTerm ||
                log.command.toLowerCase().includes(searchTerm) ||
                (log.output && log.output.toLowerCase().includes(searchTerm));

            // Command filter
            const matchesCommand = !commandFilter || log.command === commandFilter;

            // Date filter
            let matchesDate = true;
            if (dateFilter) {
                const logDate = new Date(log.timestamp).toDateString();
                const filterDate = new Date(dateFilter).toDateString();
                matchesDate = logDate === filterDate;
            }

            return matchesSearch && matchesCommand && matchesDate;
        });

        this.currentPage = 1; // Reset to first page
        this.renderLogs();
        this.updateStatistics();
    }

    sortLogs() {
        const sortBy = document.getElementById('sort-logs').value;

        this.filteredLogs.sort((a, b) => {
            switch (sortBy) {
                case 'newest':
                    return new Date(b.timestamp) - new Date(a.timestamp);
                case 'oldest':
                    return new Date(a.timestamp) - new Date(b.timestamp);
                case 'command':
                    return a.command.localeCompare(b.command);
                default:
                    return 0;
            }
        });

        this.renderLogs();
    }

    updateStatistics() {
        const totalLogs = this.allLogs.length;
        const uniqueCommands = new Set(this.allLogs.map(log => log.command)).size;
        const filteredLogs = this.filteredLogs.length;

        // Find latest run time
        let latestRun = 'Never';
        if (this.allLogs.length > 0) {
            const latest = new Date(Math.max(...this.allLogs.map(log => new Date(log.timestamp))));
            latestRun = latest.toLocaleDateString();
        }

        document.getElementById('total-logs').textContent = totalLogs;
        document.getElementById('unique-commands').textContent = uniqueCommands;
        document.getElementById('filtered-logs').textContent = filteredLogs;
        document.getElementById('latest-run').textContent = latestRun;
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
        prevLi.innerHTML = `<a class="page-link" href="#" onclick="systemLogsManager.goToPage(${this.currentPage - 1})">Previous</a>`;
        paginationList.appendChild(prevLi);

        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#" onclick="systemLogsManager.goToPage(${i})">${i}</a>`;
            paginationList.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#" onclick="systemLogsManager.goToPage(${this.currentPage + 1})">Next</a>`;
        paginationList.appendChild(nextLi);

        paginationNav.style.display = 'block';
    }

    hidePagination() {
        document.getElementById('pagination-nav').style.display = 'none';
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredLogs.length / this.logsPerPage);

        if (page < 1 || page > totalPages) return;

        this.currentPage = page;
        this.renderLogs();
    }

    toggleAutoRefresh() {
        if (this.autoRefreshEnabled) {
            // Stop auto refresh
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshEnabled = false;
            document.getElementById('auto-refresh-icon').className = 'fas fa-play';
            document.getElementById('auto-refresh-text').textContent = 'Auto Refresh';
        } else {
            // Start auto refresh
            this.autoRefreshInterval = setInterval(() => {
                this.loadSystemLogs();
            }, 30000); // Refresh every 30 seconds

            this.autoRefreshEnabled = true;
            document.getElementById('auto-refresh-icon').className = 'fas fa-pause';
            document.getElementById('auto-refresh-text').textContent = 'Auto Refresh (On)';
        }
    }

    async refreshLogs() {
        document.getElementById('logs-container').innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Refreshing system logs...</p>
            </div>
        `;

        await this.loadSystemLogs();
    }

    async exportLogs() {
        try {
            const response = await fetch('/api/logs/export', {
                method: 'POST'
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `system-logs-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                this.showError('Failed to export logs');
            }
        } catch (error) {
            this.showError('Error exporting logs: ' + error.message);
        }
    }

    async clearLogs() {
        if (!confirm('Are you sure you want to clear all system logs? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch('/api/logs/clear', {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('All system logs cleared successfully');
                await this.loadSystemLogs();
            } else {
                this.showError('Failed to clear logs: ' + result.error);
            }
        } catch (error) {
            this.showError('Error clearing logs: ' + error.message);
        }
    }

    copyLogOutput() {
        if (!this.currentLog || !this.currentLog.output) return;

        navigator.clipboard.writeText(this.currentLog.output).then(() => {
            this.showSuccess('Log output copied to clipboard');
        }).catch(() => {
            this.showError('Failed to copy log output');
        });
    }

    exportLogEntry() {
        if (!this.currentLog) return;

        const dataStr = JSON.stringify(this.currentLog, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        const timestamp = new Date(this.currentLog.timestamp).toISOString().split('T')[0];
        const command = this.currentLog.command.replace(/[^a-zA-Z0-9]/g, '_');
        a.download = `log-${timestamp}-${command}.json`;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    // Utility methods
    truncateOutput(output, maxLength) {
        if (!output) return 'No output';
        return output.length > maxLength ? output.substring(0, maxLength) + '...' : output;
    }

    formatSize(size) {
        if (!size) return 'Unknown';
        if (size < 1024) return `${size} B`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
        return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    }

    showError(message) {
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
let systemLogsManager;

window.onload = function () {
    systemLogsManager = new SystemLogsManager();
};

function filterLogs() {
    systemLogsManager.filterLogs();
}

function sortLogs() {
    systemLogsManager.sortLogs();
}

function viewLogDetails(logId) {
    systemLogsManager.viewLogDetails(logId);
}

function toggleAutoRefresh() {
    systemLogsManager.toggleAutoRefresh();
}

function refreshLogs() {
    systemLogsManager.refreshLogs();
}

function exportLogs() {
    systemLogsManager.exportLogs();
}

function clearLogs() {
    systemLogsManager.clearLogs();
}

function copyLogOutput() {
    systemLogsManager.copyLogOutput();
}

function exportLogEntry() {
    systemLogsManager.exportLogEntry();
}