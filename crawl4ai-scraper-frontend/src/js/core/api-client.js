/**
 * Crawl4AI Scraper API Client Module - Centralized API communication
 * Handles all REST API calls with consistent error handling and response formatting
 * Adapted for integration with crawl4ai projects
 */

class Crawl4AIApiClient {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || this.getApiBaseUrl();
        this.apiPrefix = options.apiPrefix || '/api/scraper';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        // Allow custom endpoint mappings for different API structures
        this.endpoints = {
            health: options.endpoints?.health || '/health',
            trigger: options.endpoints?.trigger || '/trigger',
            status: options.endpoints?.status || '/status',
            results: options.endpoints?.results || '/results',
            stats: options.endpoints?.stats || '/stats',
            categories: options.endpoints?.categories || '/categories',
            search: options.endpoints?.search || '/search'
        };
    }

    /**
     * Get API base URL from current page or configuration
     */
    getApiBaseUrl() {
        if (window.location) {
            const currentHost = window.location.hostname;
            const currentPort = window.location.port;
            const portPart = currentPort ? `:${currentPort}` : '';
            return `${window.location.protocol}//${currentHost}${portPart}`;
        }
        return 'http://localhost:8000'; // Default fallback
    }

    /**
     * Make a generic API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${this.apiPrefix}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            let data;
            
            try {
                data = await response.json();
            } catch (parseError) {
                // Handle non-JSON responses
                const text = await response.text();
                data = { message: text };
            }
            
            return {
                success: response.ok,
                data: data,
                status: response.status,
                statusText: response.statusText,
                error: !response.ok ? (data.error || data.message || response.statusText) : null
            };
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            return {
                success: false,
                error: error.message,
                status: 0,
                statusText: 'Network Error'
            };
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data = null) {
        const options = { method: 'POST' };
        if (data) {
            options.body = JSON.stringify(data);
        }
        return this.request(endpoint, options);
    }

    /**
     * PUT request
     */
    async put(endpoint, data = null) {
        const options = { method: 'PUT' };
        if (data) {
            options.body = JSON.stringify(data);
        }
        return this.request(endpoint, options);
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // === Scraper API Methods ===

    /**
     * Get scraper health status
     */
    async getScraperHealth() {
        return this.get(this.endpoints.health);
    }

    /**
     * Trigger scraping job
     */
    async triggerScraping(config = {}) {
        return this.post(this.endpoints.trigger, config);
    }

    /**
     * Get scraping status
     */
    async getScrapingStatus() {
        return this.get(this.endpoints.status);
    }

    /**
     * Get scraping results with filtering
     */
    async getScrapingResults(page = 1, limit = 20, search = '', category = '') {
        const params = { page, limit };
        if (search) params.search = search;
        if (category) params.category = category;
        return this.get(this.endpoints.results, params);
    }

    /**
     * Get result details
     */
    async getResultDetails(resultId) {
        return this.get(`${this.endpoints.results}/${resultId}`);
    }

    /**
     * Get categories
     */
    async getCategories() {
        return this.get(this.endpoints.categories);
    }

    /**
     * Get scraper statistics
     */
    async getScraperStats() {
        return this.get(this.endpoints.stats);
    }

    /**
     * Search results
     */
    async searchResults(query, category = '', page = 1, limit = 20) {
        const params = { q: query, page, limit };
        if (category) params.category = category;
        return this.get(this.endpoints.search, params);
    }

    /**
     * Pause scraping job
     */
    async pauseJob(jobId) {
        return this.post('/jobs/pause', { job_id: jobId });
    }

    /**
     * Resume scraping job
     */
    async resumeJob(jobId) {
        return this.post('/jobs/resume', { job_id: jobId });
    }

    /**
     * Cancel scraping job
     */
    async cancelJob(jobId) {
        return this.post('/jobs/cancel', { job_id: jobId });
    }

    /**
     * Get job history
     */
    async getJobHistory(page = 1, limit = 10) {
        return this.get('/jobs/history', { page, limit });
    }

    // === Configuration Methods ===

    /**
     * Update API configuration
     */
    configure(options = {}) {
        if (options.baseUrl) this.baseUrl = options.baseUrl;
        if (options.apiPrefix) this.apiPrefix = options.apiPrefix;
        if (options.headers) {
            this.defaultHeaders = { ...this.defaultHeaders, ...options.headers };
        }
        if (options.endpoints) {
            this.endpoints = { ...this.endpoints, ...options.endpoints };
        }
    }

    /**
     * Get current configuration
     */
    getConfig() {
        return {
            baseUrl: this.baseUrl,
            apiPrefix: this.apiPrefix,
            headers: this.defaultHeaders,
            endpoints: this.endpoints
        };
    }
}

// Export for both CommonJS and ES modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Crawl4AIApiClient;
}

// Global window assignment for browser usage
if (typeof window !== 'undefined') {
    window.Crawl4AIApiClient = Crawl4AIApiClient;
}
