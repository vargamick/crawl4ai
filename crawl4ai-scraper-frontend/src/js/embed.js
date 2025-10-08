/**
 * Crawl4AI Scraper Frontend - Embeddable Entry Point
 * Single-file deployment for external application integration
 */

// Import templates as strings (webpack will handle these)
import scraperUIHTML from '../components/scraper-ui.html';
import configModalHTML from '../components/config-modal.html';
import scraperCSS from '../css/scraper-ui.css';

// Import core modules
import Crawl4AIApiClient from './core/api-client.js';
import Crawl4AIScraperUI from './modules/scraper-ui.js';

/**
 * Enhanced Crawl4AI Scraper class for embeddable deployment
 */
class EmbeddableCrawl4AIScraper {
    constructor(options = {}) {
        this.options = {
            container: null,
            apiUrl: 'http://localhost:8000',
            apiPrefix: '/api/scraper',
            theme: 'default',
            autoInit: true,
            cssPrefix: 'c4ai-',
            enableShadowDOM: false,
            ...options
        };
        
        this.initialized = false;
        this.shadowRoot = null;
        this.containerElement = null;
        this.apiClient = null;
        this.ui = null;
        
        // Generate unique instance ID for CSS scoping
        this.instanceId = `c4ai-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Static method to embed scraper in a container
     */
    static embed(containerSelector, options = {}) {
        const instance = new EmbeddableCrawl4AIScraper({
            container: containerSelector,
            ...options
        });
        
        if (options.autoInit !== false) {
            instance.initialize().catch(error => {
                console.error('Failed to initialize Crawl4AI Scraper:', error);
            });
        }
        
        return instance;
    }

    /**
     * Initialize the embeddable scraper
     */
    async initialize() {
        if (this.initialized) {
            console.warn('Crawl4AI Scraper already initialized');
            return this;
        }

        try {
            // Find container element
            this.containerElement = this.findContainer();
            if (!this.containerElement) {
                throw new Error(`Container not found: ${this.options.container}`);
            }

            // Setup DOM structure
            await this.setupDOM();
            
            // Initialize components
            this.setupComponents();
            await this.initializeComponents();
            
            // Setup global event handlers
            this.setupEventHandlers();
            
            console.log('Crawl4AI Scraper embedded successfully');
            this.initialized = true;
            
            // Trigger initialized event
            this.dispatchEvent('initialized', { instance: this });
            
            return this;
            
        } catch (error) {
            console.error('Failed to initialize Crawl4AI Scraper:', error);
            this.dispatchEvent('error', { error, phase: 'initialization' });
            throw error;
        }
    }

    /**
     * Find the container element
     */
    findContainer() {
        if (typeof this.options.container === 'string') {
            return document.querySelector(this.options.container) || 
                   document.getElementById(this.options.container.replace('#', ''));
        } else if (this.options.container instanceof HTMLElement) {
            return this.options.container;
        }
        return null;
    }

    /**
     * Setup DOM structure with scoped CSS
     */
    async setupDOM() {
        // Create container structure
        const wrapperDiv = document.createElement('div');
        wrapperDiv.className = `${this.options.cssPrefix}wrapper`;
        wrapperDiv.setAttribute('data-c4ai-instance', this.instanceId);
        
        // Use Shadow DOM if enabled and supported
        if (this.options.enableShadowDOM && this.containerElement.attachShadow) {
            this.shadowRoot = this.containerElement.attachShadow({ mode: 'open' });
            this.setupShadowDOM(wrapperDiv);
        } else {
            this.setupNormalDOM(wrapperDiv);
        }
    }

    /**
     * Setup Shadow DOM structure
     */
    setupShadowDOM(wrapperDiv) {
        // Create style element
        const styleElement = document.createElement('style');
        styleElement.textContent = this.getScopedCSS();
        
        // Add HTML content
        wrapperDiv.innerHTML = this.getEmbeddedHTML();
        
        // Append to shadow root
        this.shadowRoot.appendChild(styleElement);
        this.shadowRoot.appendChild(wrapperDiv);
        
        // Set context for component queries
        this.domContext = this.shadowRoot;
    }

    /**
     * Setup normal DOM structure with CSS scoping
     */
    setupNormalDOM(wrapperDiv) {
        // Add scoped CSS to document head if not already present
        const styleId = `${this.options.cssPrefix}styles`;
        if (!document.getElementById(styleId)) {
            const styleElement = document.createElement('style');
            styleElement.id = styleId;
            styleElement.textContent = this.getScopedCSS();
            document.head.appendChild(styleElement);
        }
        
        // Add HTML content with scoped classes
        wrapperDiv.innerHTML = this.getEmbeddedHTML();
        this.containerElement.appendChild(wrapperDiv);
        
        // Set context for component queries
        this.domContext = this.containerElement;
    }

    /**
     * Get CSS with scoping prefix
     */
    getScopedCSS() {
        const css = scraperCSS;
        const prefix = `[data-c4ai-instance="${this.instanceId}"]`;
        
        // Add scoping prefix to all CSS rules
        return css.replace(
            /(^|\})\s*([^{]+)\s*\{/g, 
            (match, closing, selector) => {
                // Skip keyframes and other special rules
                if (selector.includes('@') || selector.includes('%')) {
                    return match;
                }
                
                // Add prefix to selector
                const scopedSelector = selector
                    .split(',')
                    .map(s => `${prefix} ${s.trim()}`)
                    .join(', ');
                
                return `${closing} ${scopedSelector} {`;
            }
        );
    }

    /**
     * Get embedded HTML content
     */
    getEmbeddedHTML() {
        return scraperUIHTML + configModalHTML;
    }

    /**
     * Setup component instances
     */
    setupComponents() {
        // Initialize API client
        this.apiClient = new Crawl4AIApiClient({
            baseUrl: this.options.apiUrl,
            apiPrefix: this.options.apiPrefix,
            ...this.options.apiOptions
        });

        // Initialize UI component
        this.ui = new Crawl4AIScraperUI(this.apiClient, {
            domContext: this.domContext,
            ...this.options.uiOptions
        });
    }

    /**
     * Initialize all components
     */
    async initializeComponents() {
        await this.ui.initialize();
        
        // Override UI's DOM query methods to use our context
        this.ui.querySelector = (selector) => this.domContext.querySelector(selector);
        this.ui.querySelectorAll = (selector) => this.domContext.querySelectorAll(selector);
    }

    /**
     * Setup event handlers with scoped context
     */
    setupEventHandlers() {
        const globalMethods = {
            refreshStatus: () => this.ui.refreshStatus(),
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
            viewResultDetails: (id) => this.ui.viewResultDetails(id),
            pauseCurrentJob: () => this.pauseCurrentJob(),
            previousResultPage: () => this.ui.previousResultPage(),
            nextResultPage: () => this.ui.nextResultPage()
        };

        // Create scoped global object
        if (!window.Crawl4AIScraperInstances) {
            window.Crawl4AIScraperInstances = {};
        }
        window.Crawl4AIScraperInstances[this.instanceId] = globalMethods;

        // Update onclick handlers to use scoped methods
        this.updateEventHandlers();
    }

    /**
     * Update onclick handlers to use scoped methods
     */
    updateEventHandlers() {
        const buttons = this.domContext.querySelectorAll('[onclick*="Crawl4AIScraper"]');
        buttons.forEach(button => {
            const onclickAttr = button.getAttribute('onclick');
            if (onclickAttr) {
                const scopedHandler = onclickAttr.replace(
                    /Crawl4AIScraper\./g,
                    `Crawl4AIScraperInstances['${this.instanceId}'].`
                );
                button.setAttribute('onclick', scopedHandler);
            }
        });
    }

    // === Public API Methods ===

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
        
        try {
            const response = await this.apiClient.triggerScraping(config);
            this.dispatchEvent('scrapingStarted', { config, response });
            return response;
        } catch (error) {
            this.dispatchEvent('error', { error, action: 'quickScraping' });
            throw error;
        }
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
        
        try {
            const response = await this.apiClient.triggerScraping(config);
            this.dispatchEvent('scrapingStarted', { config, response });
            return response;
        } catch (error) {
            this.dispatchEvent('error', { error, action: 'fullScraping' });
            throw error;
        }
    }

    /**
     * Show scraper statistics
     */
    async showScraperStats() {
        try {
            const response = await this.apiClient.getScraperStats();
            if (response.success && response.data) {
                this.displayStatsModal(response.data);
                this.dispatchEvent('statsDisplayed', { stats: response.data });
            } else {
                this.ui.updateStatus('Failed to load statistics', 'error');
            }
        } catch (error) {
            console.error('Failed to load scraper stats:', error);
            this.ui.updateStatus(`Error loading stats: ${error.message}`, 'error');
            this.dispatchEvent('error', { error, action: 'showStats' });
        }
    }

    /**
     * Display statistics modal
     */
    displayStatsModal(stats) {
        // Implementation similar to original but scoped to this instance
        const existingModal = this.domContext.querySelector('#statsModal');
        if (existingModal) {
            existingModal.remove();
        }

        const modalHTML = `
            <div class="modal" id="statsModal" style="display: block;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>📊 Scraper Statistics</h3>
                        <span class="close" onclick="Crawl4AIScraperInstances['${this.instanceId}'].closeStatsModal()">&times;</span>
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
        
        // Insert into appropriate context
        if (this.shadowRoot) {
            this.shadowRoot.insertAdjacentHTML('beforeend', modalHTML);
        } else {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
        
        // Add close method to instance
        if (!window.Crawl4AIScraperInstances[this.instanceId].closeStatsModal) {
            window.Crawl4AIScraperInstances[this.instanceId].closeStatsModal = () => {
                const modal = this.domContext.querySelector('#statsModal') || 
                             document.querySelector('#statsModal');
                if (modal) modal.remove();
            };
        }
    }

    /**
     * Configuration methods
     */
    showConfigModal() {
        const modal = this.domContext.querySelector('#scraperConfigModal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    closeConfigModal() {
        const modal = this.domContext.querySelector('#scraperConfigModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Pause current job
     */
    async pauseCurrentJob() {
        // Implementation would depend on API
        console.log('Pause job functionality to be implemented');
        this.dispatchEvent('jobPaused');
    }

    // === Event System ===

    /**
     * Dispatch custom events
     */
    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(`crawl4ai:${eventName}`, {
            detail: { instance: this, ...detail },
            bubbles: true
        });
        
        if (this.containerElement) {
            this.containerElement.dispatchEvent(event);
        }
    }

    /**
     * Add event listener
     */
    addEventListener(eventName, handler) {
        if (this.containerElement) {
            this.containerElement.addEventListener(`crawl4ai:${eventName}`, handler);
        }
    }

    /**
     * Remove event listener
     */
    removeEventListener(eventName, handler) {
        if (this.containerElement) {
            this.containerElement.removeEventListener(`crawl4ai:${eventName}`, handler);
        }
    }

    // === Configuration and Control ===

    /**
     * Update configuration
     */
    configure(newOptions = {}) {
        this.options = { ...this.options, ...newOptions };
        
        if (newOptions.apiUrl || newOptions.apiPrefix) {
            this.apiClient?.configure({
                baseUrl: this.options.apiUrl,
                apiPrefix: this.options.apiPrefix
            });
        }
        
        this.dispatchEvent('configured', { options: this.options });
    }

    /**
     * Get current configuration
     */
    getConfiguration() {
        return {
            ...this.options,
            initialized: this.initialized,
            instanceId: this.instanceId
        };
    }

    /**
     * Destroy instance and cleanup
     */
    destroy() {
        if (this.containerElement && this.containerElement.firstChild) {
            this.containerElement.removeChild(this.containerElement.firstChild);
        }
        
        if (window.Crawl4AIScraperInstances) {
            delete window.Crawl4AIScraperInstances[this.instanceId];
        }
        
        this.dispatchEvent('destroyed');
        this.initialized = false;
    }
}

// Global embedding API
const Crawl4AIScraper = {
    embed: EmbeddableCrawl4AIScraper.embed,
    create: (options) => new EmbeddableCrawl4AIScraper(options),
    version: '1.0.0' // This should be dynamically injected during build
};

// Global window assignment
if (typeof window !== 'undefined') {
    window.Crawl4AIScraper = Crawl4AIScraper;
}

// Export for module systems
export default Crawl4AIScraper;
