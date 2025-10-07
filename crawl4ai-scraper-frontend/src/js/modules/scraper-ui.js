/**
 * Crawl4AI Scraper UI Module - User interface interactions and result display
 * Handles result listing, search, pagination, and basic scraper status display
 * Adapted for crawl4ai integration
 */

class Crawl4AIScraperUI {
    constructor(apiClient = null, options = {}) {
        this.apiClient = apiClient || (window.Crawl4AIApiClient ? new window.Crawl4AIApiClient() : null);
        this.currentResultPage = 1;
        this.resultsPerPage = options.resultsPerPage || 10;
        this.currentResults = [];
        this.currentCategories = [];
        this.initialized = false;
        
        // Configuration options
        this.options = {
            autoRefresh: options.autoRefresh !== false,
            refreshInterval: options.refreshInterval || 30000,
            enableProgress: options.enableProgress !== false,
            ...options
        };
    }

    /**
     * Initialize the scraper UI component
     */
    async initialize() {
        if (this.initialized) return;
        
        if (!this.apiClient) {
            console.error('No API client provided for Crawl4AI Scraper UI');
            return;
        }
        
        try {
            // Check initial scraper health
            await this.refreshStatus();
            
            // Load categories on startup
            await this.loadCategories();
            
            // Setup auto-refresh if enabled
            if (this.options.autoRefresh) {
                this.setupAutoRefresh();
            }
            
            console.log('Crawl4AI scraper UI initialized successfully');
            this.initialized = true;
        } catch (error) {
            console.error('Failed to initialize Crawl4AI scraper UI:', error);
            this.updateStatus('Failed to initialize scraper', 'error');
        }
    }

    /**
     * Setup automatic refresh
     */
    setupAutoRefresh() {
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.refreshStatus();
            }
        }, this.options.refreshInterval);
    }

    /**
     * Refresh scraper health status
     */
    async refreshStatus() {
        try {
            const response = await this.apiClient.getScraperHealth();
            const healthIndicator = document.getElementById('scraperHealthIndicator');
            
            if (response.success && response.data) {
                const data = response.data;
                
                if (data.status === 'healthy' || data.status === 'ok') {
                    healthIndicator.textContent = '🟢';
                    healthIndicator.title = 'Scraper is healthy';
                    this.updateStatus('Scraper is healthy and ready', 'success');
                } else if (data.status === 'degraded' || data.status === 'warning') {
                    healthIndicator.textContent = '🟡';
                    healthIndicator.title = `Degraded: ${data.warning || data.message || 'Unknown issue'}`;
                    this.updateStatus(`Scraper degraded: ${data.warning || data.message}`, 'warning');
                } else {
                    healthIndicator.textContent = '🔴';
                    healthIndicator.title = `Unhealthy: ${data.error || data.message || 'Unknown error'}`;
                    this.updateStatus(`Scraper unhealthy: ${data.error || data.message}`, 'error');
                }
            } else {
                throw new Error(response.error || 'Health check failed');
            }
            
            // Also update scraper status display
            await this.checkScrapingStatus();
            
        } catch (error) {
            console.error('Failed to refresh scraper status:', error);
            const healthIndicator = document.getElementById('scraperHealthIndicator');
            if (healthIndicator) {
                healthIndicator.textContent = '🔴';
                healthIndicator.title = 'Connection failed';
            }
            this.updateStatus('Failed to connect to scraper service', 'error');
        }
    }

    /**
     * Check current scraping status
     */
    async checkScrapingStatus() {
        try {
            const response = await this.apiClient.getScrapingStatus();
            
            if (response.success && response.data) {
                this.displayScrapingStatus(response.data);
            } else {
                this.updateStatus(`Failed to get scraping status: ${response.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Failed to check scraping status:', error);
            this.updateStatus(`Error checking status: ${error.message}`, 'error');
        }
    }

    /**
     * Display scraping status information
     */
    displayScrapingStatus(statusData) {
        const scraperStatus = document.getElementById('scraperStatus');
        if (!scraperStatus) return;
        
        let statusHtml = '<h5>📊 Scraper Status</h5>';
        
        if (statusData.current_job || statusData.currentJob) {
            const job = statusData.current_job || statusData.currentJob;
            statusHtml += `
                <div class="status-section">
                    <p><strong>Current Job:</strong> #${job.job_id || job.id}</p>
                    <p><strong>Status:</strong> <span class="status-${job.status}">${job.status.toUpperCase()}</span></p>
                    <p><strong>Started:</strong> ${new Date(job.started_at || job.startedAt).toLocaleString()}</p>
            `;
            
            if (job.status === 'completed') {
                statusHtml += `
                    <p><strong>Completed:</strong> ${new Date(job.completed_at || job.completedAt).toLocaleString()}</p>
                    <p><strong>Items Processed:</strong> ${job.items_scraped || job.itemsProcessed || 0}</p>
                `;
            } else if (job.status === 'failed' && (job.error_message || job.errorMessage)) {
                statusHtml += `<p><strong>Error:</strong> ${job.error_message || job.errorMessage}</p>`;
            }
            
            statusHtml += '</div>';
        }
        
        if (statusData.last_successful_scrape || statusData.lastSuccessfulScrape) {
            const lastJob = statusData.last_successful_scrape || statusData.lastSuccessfulScrape;
            statusHtml += `
                <div class="status-section">
                    <p><strong>Last Successful Scrape:</strong></p>
                    <p>Job #${lastJob.job_id || lastJob.id} - ${new Date(lastJob.completed_at || lastJob.completedAt).toLocaleString()}</p>
                    <p>${lastJob.items_scraped || lastJob.itemsProcessed || 0} items processed</p>
                </div>
            `;
        }
        
        if (statusData.scraping_available === false || statusData.scrapingAvailable === false) {
            statusHtml += `
                <div class="status-section warning">
                    <p><strong>⚠️ Warning:</strong> Scraper module not available - functionality is limited</p>
                </div>
            `;
        }
        
        scraperStatus.innerHTML = statusHtml;
    }

    /**
     * Load and display results
     */
    async loadResults(page = 1, search = '', category = '') {
        try {
            const resultsList = document.getElementById('resultsList');
            if (resultsList) {
                resultsList.innerHTML = '<div class="status-info">Loading results...</div>';
            }
            
            const response = await this.apiClient.getScrapingResults(page, this.resultsPerPage, search, category);
            
            if (response.success && response.data) {
                this.currentResults = response.data;
                this.displayResults(response.data);
                
                // Update pagination
                this.updateResultPagination(page, response.data.length < this.resultsPerPage);
                
                this.updateStatus(`Loaded ${response.data.length} results`, 'success');
            } else {
                if (resultsList) {
                    resultsList.innerHTML = '<div class="status-info">No results found</div>';
                }
                this.updateStatus('No results available', 'info');
            }
            
        } catch (error) {
            console.error('Failed to load results:', error);
            const resultsList = document.getElementById('resultsList');
            if (resultsList) {
                resultsList.innerHTML = '<div class="status-info error">Failed to load results</div>';
            }
            this.updateStatus(`Error loading results: ${error.message}`, 'error');
        }
    }

    /**
     * Display results in the UI
     */
    displayResults(results) {
        const resultsList = document.getElementById('resultsList');
        if (!resultsList) return;
        
        if (!Array.isArray(results) || results.length === 0) {
            resultsList.innerHTML = '<div class="status-info">No results found</div>';
            return;
        }
        
        let resultsHtml = '';
        
        results.forEach(result => {
            const resultId = result.id || result.result_id || result.url;
            const title = result.title || result.name || result.url || 'Untitled';
            const description = result.description || result.content || result.summary || '';
            const url = result.url || result.source_url || '#';
            const timestamp = result.scraped_at || result.created_at || result.timestamp;
            
            resultsHtml += `
                <div class="result-item" onclick="Crawl4AIScraper.viewResultDetails('${resultId}')">
                    <div class="result-header">
                        <h6>${title}</h6>
                        <span class="result-id">${resultId}</span>
                    </div>
                    <div class="result-details">
                        <p class="result-description">${description ? description.substring(0, 150) + '...' : 'No description available'}</p>
                        <div class="result-meta">
                            <span class="result-url">🔗 <a href="${url}" target="_blank">View Source</a></span>
                            ${timestamp ? `<span class="result-updated">📅 ${new Date(timestamp).toLocaleDateString()}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        resultsList.innerHTML = resultsHtml;
        
        // Show pagination
        const pagination = document.getElementById('resultsPagination');
        if (pagination) {
            pagination.style.display = 'flex';
        }
    }

    /**
     * Load categories
     */
    async loadCategories() {
        try {
            const response = await this.apiClient.getCategories();
            
            if (response.success && response.data) {
                this.currentCategories = response.data;
                this.updateCategorySelect(response.data);
                this.updateStatus(`Loaded ${response.data.length} categories`, 'success');
            }
            
        } catch (error) {
            console.error('Failed to load categories:', error);
            this.updateStatus(`Error loading categories: ${error.message}`, 'error');
        }
    }

    /**
     * Update category select dropdown
     */
    updateCategorySelect(categories) {
        const categoryFilter = document.getElementById('categoryFilter');
        if (!categoryFilter) return;
        
        // Clear existing options except "All Categories"
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        
        categories.forEach(category => {
            const option = document.createElement('option');
            const name = category.name || category.category_name || category;
            option.value = name;
            option.textContent = name;
            categoryFilter.appendChild(option);
        });
    }

    /**
     * Search results
     */
    searchResults() {
        const searchTerm = document.getElementById('resultSearch')?.value || '';
        const category = document.getElementById('categoryFilter')?.value || '';
        this.currentResultPage = 1; // Reset to first page
        this.loadResults(1, searchTerm, category);
    }

    /**
     * Filter by category
     */
    filterByCategory() {
        const searchTerm = document.getElementById('resultSearch')?.value || '';
        const category = document.getElementById('categoryFilter')?.value || '';
        this.currentResultPage = 1; // Reset to first page
        this.loadResults(1, searchTerm, category);
    }

    /**
     * Navigate to previous result page
     */
    previousResultPage() {
        if (this.currentResultPage > 1) {
            this.currentResultPage--;
            const searchTerm = document.getElementById('resultSearch')?.value || '';
            const category = document.getElementById('categoryFilter')?.value || '';
            this.loadResults(this.currentResultPage, searchTerm, category);
        }
    }

    /**
     * Navigate to next result page
     */
    nextResultPage() {
        this.currentResultPage++;
        const searchTerm = document.getElementById('resultSearch')?.value || '';
        const category = document.getElementById('categoryFilter')?.value || '';
        this.loadResults(this.currentResultPage, searchTerm, category);
    }

    /**
     * Update result pagination controls
     */
    updateResultPagination(currentPage, isLastPage) {
        this.currentResultPage = currentPage;
        
        const pageInfo = document.getElementById('resultPageInfo');
        const prevBtn = document.getElementById('prevResultsBtn');
        const nextBtn = document.getElementById('nextResultsBtn');
        
        if (pageInfo) pageInfo.textContent = `Page ${currentPage}`;
        if (prevBtn) prevBtn.disabled = currentPage === 1;
        if (nextBtn) nextBtn.disabled = isLastPage;
    }

    /**
     * Update scraper status display
     */
    updateStatus(message, type = 'info') {
        const statusElement = document.getElementById('scraperStatusIndicator');
        
        if (statusElement) {
            statusElement.className = `status-indicator status-${type}`;
            statusElement.textContent = message;
            statusElement.style.display = 'block';
            
            // Auto-hide after 10 seconds for success/info messages
            if (type === 'success' || type === 'info') {
                setTimeout(() => {
                    statusElement.style.display = 'none';
                }, 10000);
            }
        }
        
        // Also log to console
        console.log(`Crawl4AI Scraper: ${message}`);
    }

    /**
     * View result details (override in implementation)
     */
    viewResultDetails(resultId) {
        console.log('View result details for:', resultId);
        // This should be overridden by the implementing application
        // or handled by a modal/detailed view
    }
}

// Export for both CommonJS and ES modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Crawl4AIScraperUI;
}

// Global window assignment for browser usage
if (typeof window !== 'undefined') {
    window.Crawl4AIScraperUI = Crawl4AIScraperUI;
}
