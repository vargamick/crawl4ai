/**
 * Crawl4AI Scraper Frontend - Main Entry Point
 * Exports all components for easy integration
 */

// Import core modules
// Note: In browser environments, these will be loaded via script tags
// In Node.js environments, adjust import paths as needed

/**
 * Main Crawl4AI Scraper class that combines all functionality
 */
class Crawl4AIScraper {
    constructor(options = {}) {
        // Initialize API client
        this.apiClient = new Crawl4AIApiClient(options);
        
        // Initialize UI components
        this.ui = new Crawl4AIScraperUI(this.apiClient, options);
        this.config = new Crawl4AIScraperConfig(options);
        this.progress = new Crawl4AIScraperProgress(this.apiClient, options);
        
        // Store options
        this.options = options;
        this.initialized = false;
    }

    /**
     * Initialize all components
     */
    async initialize() {
        if (this.initialized) return;

        try {
            // Load HTML components if container is specified
            if (this.options.container) {
                await this.loadComponents();
            }

            // Initialize all modules
            await this.ui.initialize();
            this.config.initialize();
            this.progress.initialize();

            // Setup global event handlers
            this.setupGlobalHandlers();

            console.log('Crawl4AI Scraper initialized successfully');
            this.initialized = true;
        } catch (error) {
            console.error('Failed to initialize Crawl4AI Scraper:', error);
            throw error;
        }
    }

    /**
     * Load HTML components into specified container
     */
    async loadComponents() {
        const container = document.getElementById(this.options.container) || 
                         document.querySelector(this.options.container);
        
        if (!container) {
            throw new Error(`Container not found: ${this.options.container}`);
        }

        try {
            // Load main UI component
            const uiResponse = await fetch(this.getComponentPath('scraper-ui.html'));
            const uiHTML = await uiResponse.text();
            
            // Load config modal
            const modalResponse = await fetch(this.getComponentPath('config-modal.html'));
            const modalHTML = await modalResponse.text();
            
            // Insert into container
            container.innerHTML = uiHTML + modalHTML;
            
        } catch (error) {
            console.error('Failed to load components:', error);
            // Fall back to creating basic HTML structure
            this.createBasicHTML(container);
        }
    }

    /**
     * Get component file path
     */
    getComponentPath(filename) {
        const basePath = this.options.componentsPath || 'src/components/';
        return basePath + filename;
    }

    /**
     * Create basic HTML structure if component loading fails
     */
    createBasicHTML(container) {
        container.innerHTML = `
            <div class="crawl4ai-scraper-panel">
                <div class="panel-header">
                    <div class="header-left">🕷️ Web Scraper Management</div>
                    <div class="header-right">
                        <button class="btn btn-small btn-info" onclick="Crawl4AIScraper.refreshStatus()">🔄 Refresh</button>
                        <span id="scraperHealthIndicator" class="health-indicator">⚪</span>
                    </div>
                </div>
                <div class="quick-actions">
                    <button class="btn btn-primary" onclick="Crawl4AIScraper.triggerQuickScraping()" id="quickScrapeBtn">
                        Quick Scrape
                    </button>
                    <button class="btn btn-success" onclick="Crawl4AIScraper.triggerFullScraping()" id="fullScrapeBtn">
                        Full Scrape
                    </button>
                </div>
                <div class="scraper-status" id="scraperStatus">
                    <div class="status-info">Click "Refresh" to see scraping information</div>
                </div>
                <div class="results-browser">
                    <h4>📦 Scraped Results Browser</h4>
                    <div class="results-list" id="resultsList">
                        <div class="status-info">Results will appear here</div>
                    </div>
                </div>
                <div id="scraperStatusIndicator" class="status-indicator status-info" style="display: none;"></div>
            </div>
        `;
    }

    /**
     * Setup global event handlers
     */
    setupGlobalHandlers() {
        // Make methods globally accessible for HTML onclick handlers
        window.Crawl4AIScraper = {
            refreshStatus: () => this.refreshStatus(),
            triggerQuickScraping: () => this.triggerQuickScraping(),
            triggerFullScraping: () => this.triggerFullScraping(),
            checkScrapingStatus: () => this.ui.checkScrapingStatus(),
            loadResults: (...args) => this.ui.loadResults(...args),
            loadCategories: () => this.ui.loadCategories(),
            searchResults: () => this.ui.searchResults(),
            filterByCategory: () => this.ui.filterByCategory(),
            showScraperStats: () => this.showScraperStats(),
            showConfigModal: () => this.showConfigModal(),
            closeConfigModal: () => this.closeConfigModal(),
            viewResultDetails: (id) => this.ui.viewResultDetails(id)
        };
    }

    // === Public API Methods ===

    /**
     * Refresh scraper status
     */
    async refreshStatus() {
        return this.ui.refreshStatus();
    }

    /**
     * Trigger quick scraping
     */
    async triggerQuickScraping() {
        const config = {
            max_items: 100,
            include_media: false,
            include_documents: false,
            include_metadata: true
        };
        return this.apiClient.triggerScraping(config);
    }

    /**
     * Trigger full scraping
     */
    async triggerFullScraping() {
        const config = {
            max_items: null,
            include_media: true,
            include_documents: true,
            include_metadata: true
        };
        return this.apiClient.triggerScraping(config);
    }

    /**
     * Show scraper statistics
     */
    async showScraperStats() {
        try {
            const response = await this.apiClient.getScraperStats();
            if (response.success && response.data) {
                this.displayStatsModal(response.data);
            } else {
                this.ui.updateStatus('Failed to load statistics', 'error');
            }
        } catch (error) {
            console.error('Failed to load scraper stats:', error);
            this.ui.updateStatus(`Error loading stats: ${error.message}`, 'error');
        }
    }

    /**
     * Display statistics modal
     */
    displayStatsModal(stats) {
        const modalHTML = `
            <div class="modal" id="statsModal" style="display: block;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>📊 Scraper Statistics</h3>
                        <span class="close" onclick="Crawl4AIScraper.closeStatsModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <div class="stats-grid">
                            <div class="stat-item">
                                <h4>${stats.total_results || stats.totalResults || 0}</h4>
                                <p>Total Results</p>
                            </div>
                            <div class="stat-item">
                                <h4>${stats.total_categories || stats.totalCategories || 0}</h4>
                                <p>Categories</p>
                            </div>
                            <div class="stat-item">
                                <h4>${stats.total_jobs || stats.totalJobs || 0}</h4>
                                <p>Total Jobs</p>
                            </div>
                            <div class="stat-item">
                                <h4>${stats.successful_jobs || stats.successfulJobs || 0}</h4>
                                <p>Successful Jobs</p>
                            </div>
                        </div>
                        ${stats.last_update || stats.lastUpdate ? `
                            <p class="stats-footer">
                                <strong>Last Update:</strong> ${new Date(stats.last_update || stats.lastUpdate).toLocaleString()}
                            </p>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add close stats method
        window.Crawl4AIScraper.closeStatsModal = () => {
            const modal = document.getElementById('statsModal');
            if (modal) modal.remove();
        };
    }

    /**
     * Show configuration modal
     */
    showConfigModal() {
        const modal = document.getElementById('scraperConfigModal');
        if (modal) {
            modal.style.display = 'block';
        } else {
            console.warn('Configuration modal not found. Make sure config-modal.html is loaded.');
        }
    }

    /**
     * Close configuration modal
     */
    closeConfigModal() {
        const modal = document.getElementById('scraperConfigModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Get current configuration
     */
    getConfiguration() {
        return {
            api: this.apiClient.getConfig(),
            ui: this.ui.options,
            initialized: this.initialized
        };
    }

    /**
     * Update configuration
     */
    configure(newOptions = {}) {
        // Update API client
        if (newOptions.api) {
            this.apiClient.configure(newOptions.api);
        }

        // Update options
        this.options = { ...this.options, ...newOptions };

        // Reinitialize if needed
        if (this.initialized && newOptions.reinitialize) {
            this.initialized = false;
            return this.initialize();
        }
    }
}

// Placeholder classes for modules that will be loaded separately
// These ensure the main class constructor doesn't fail
if (typeof Crawl4AIScraperConfig === 'undefined') {
    window.Crawl4AIScraperConfig = class {
        constructor() {}
        initialize() {}
    };
}

if (typeof Crawl4AIScraperProgress === 'undefined') {
    window.Crawl4AIScraperProgress = class {
        constructor() {}
        initialize() {}
    };
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Crawl4AIScraper;
}

if (typeof window !== 'undefined') {
    window.Crawl4AIScraper = Crawl4AIScraper;
}
