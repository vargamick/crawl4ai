#!/usr/bin/env node

/**
 * Simple Mock API Server for Testing Crawl4AI Frontend
 * Run with: node mock-api-server.js
 */

const http = require('http');
const url = require('url');

const PORT = 8000;

// Mock data
const mockStats = {
    total_results: 1250,
    total_categories: 15,
    total_jobs: 23,
    successful_jobs: 18,
    last_update: new Date().toISOString()
};

const mockResults = [
    {
        id: 'result_1',
        title: 'Sample Web Page 1',
        description: 'This is a sample scraped result from a web page with interesting content about web scraping.',
        url: 'https://example.com/page1',
        scraped_at: new Date(Date.now() - 3600000).toISOString()
    },
    {
        id: 'result_2', 
        title: 'Sample Web Page 2',
        description: 'Another sample result demonstrating the scraper\'s ability to extract meaningful content.',
        url: 'https://example.com/page2',
        scraped_at: new Date(Date.now() - 7200000).toISOString()
    },
    {
        id: 'result_3',
        title: 'Sample Web Page 3', 
        description: 'A third example showing various types of content that can be successfully scraped.',
        url: 'https://example.com/page3',
        scraped_at: new Date(Date.now() - 10800000).toISOString()
    }
];

const mockCategories = ['Technology', 'News', 'E-commerce', 'Documentation', 'Blog'];

let currentJob = null;
let jobCounter = 1;

function sendJSON(res, data, statusCode = 200) {
    res.writeHead(statusCode, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
    res.end(JSON.stringify(data));
}

function handleRequest(req, res) {
    const parsedUrl = url.parse(req.url, true);
    const path = parsedUrl.pathname;
    const method = req.method;

    console.log(`${method} ${path}`);

    // Handle CORS preflight
    if (method === 'OPTIONS') {
        res.writeHead(200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        });
        res.end();
        return;
    }

    // API Routes
    if (path === '/api/scraper/health') {
        sendJSON(res, { 
            status: 'healthy', 
            message: 'Mock API is running',
            timestamp: new Date().toISOString()
        });
        
    } else if (path === '/api/scraper/trigger' && method === 'POST') {
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });
        req.on('end', () => {
            try {
                const config = JSON.parse(body || '{}');
                currentJob = {
                    job_id: `job_${jobCounter++}`,
                    status: 'running',
                    started_at: new Date().toISOString(),
                    config: config
                };
                
                // Simulate job completion after 3 seconds
                setTimeout(() => {
                    if (currentJob) {
                        currentJob.status = 'completed';
                        currentJob.completed_at = new Date().toISOString();
                        currentJob.items_scraped = config.max_items || 100;
                    }
                }, 3000);
                
                sendJSON(res, { 
                    success: true, 
                    job_id: currentJob.job_id,
                    message: 'Scraping job started successfully'
                });
            } catch (error) {
                sendJSON(res, { 
                    success: false, 
                    error: 'Invalid JSON payload' 
                }, 400);
            }
        });
        
    } else if (path === '/api/scraper/status') {
        const status = {
            current_job: currentJob,
            last_successful_scrape: {
                job_id: 'job_prev',
                completed_at: new Date(Date.now() - 86400000).toISOString(),
                items_scraped: 150
            },
            scraping_available: true
        };
        sendJSON(res, status);
        
    } else if (path === '/api/scraper/results') {
        const page = parseInt(parsedUrl.query.page) || 1;
        const limit = parseInt(parsedUrl.query.limit) || 10;
        const search = parsedUrl.query.search || '';
        
        let results = mockResults;
        if (search) {
            results = mockResults.filter(r => 
                r.title.toLowerCase().includes(search.toLowerCase()) ||
                r.description.toLowerCase().includes(search.toLowerCase())
            );
        }
        
        sendJSON(res, results);
        
    } else if (path === '/api/scraper/categories') {
        sendJSON(res, mockCategories);
        
    } else if (path === '/api/scraper/stats') {
        sendJSON(res, mockStats);
        
    } else if (path === '/api/scraper/search') {
        const query = parsedUrl.query.q || '';
        const results = mockResults.filter(r => 
            r.title.toLowerCase().includes(query.toLowerCase()) ||
            r.description.toLowerCase().includes(query.toLowerCase())
        );
        sendJSON(res, { results, total: results.length });
        
    } else {
        // 404 for unknown routes
        sendJSON(res, { 
            error: 'Not Found', 
            message: `Route ${path} not found` 
        }, 404);
    }
}

const server = http.createServer(handleRequest);

server.listen(PORT, () => {
    console.log(`🚀 Mock Crawl4AI API Server running on http://localhost:${PORT}`);
    console.log(`📡 Available endpoints:`);
    console.log(`   GET  /api/scraper/health`);
    console.log(`   POST /api/scraper/trigger`);
    console.log(`   GET  /api/scraper/status`);
    console.log(`   GET  /api/scraper/results`);
    console.log(`   GET  /api/scraper/categories`);
    console.log(`   GET  /api/scraper/stats`);
    console.log(`   GET  /api/scraper/search`);
    console.log(``);
    console.log(`🌐 Test the frontend at:`);
    console.log(`   http://localhost:8080/basic-embed.html`);
    console.log(`   http://localhost:8080/advanced-embed.html`);
    console.log(``);
    console.log(`Press Ctrl+C to stop the server`);
});

process.on('SIGINT', () => {
    console.log('\n👋 Shutting down mock API server...');
    server.close(() => {
        process.exit(0);
    });
});
