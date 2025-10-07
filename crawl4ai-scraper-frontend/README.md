# Crawl4AI Scraper Frontend

A modular, reusable frontend UI package for web scraping applications built for integration with the [Crawl4AI](https://github.com/unclecode/crawl4ai) project.

## Features

- 🕷️ **Complete Scraper UI** - Ready-to-use web scraping interface
- 🎛️ **Configurable Settings** - Advanced scraper configuration with presets
- 📊 **Real-time Progress** - Live scraping progress monitoring
- 🔍 **Results Browser** - Search, filter, and paginate through scraped data
- 📈 **Statistics Dashboard** - Comprehensive scraping statistics
- 🎨 **Modern UI** - Clean, responsive interface
- 🔧 **Easy Integration** - Simple drop-in solution for existing projects
- 📱 **Responsive Design** - Works on all device sizes
- ⚡ **Fast & Lightweight** - Minimal dependencies, optimized performance

## Quick Start

### 1. Installation

```bash
# Clone or download the package
git clone https://github.com/unclecode/crawl4ai
cd crawl4ai/frontend-packages/crawl4ai-scraper-frontend

# Or install via npm (when published)
npm install crawl4ai-scraper-frontend
```

### 2. Include in Your Project

#### Option A: Use Built Files (Recommended)
```html
<!DOCTYPE html>
<html>
<head>
    <title>My Scraper App</title>
    <!-- Include CSS -->
    <link rel="stylesheet" href="dist/crawl4ai-scraper.css">
</head>
<body>
    <!-- Include the scraper UI component -->
    <div id="scraper-container">
        <!-- Scraper UI will be loaded here -->
    </div>
    
    <!-- Include JavaScript -->
    <script src="dist/crawl4ai-scraper.js"></script>
    <script>
        // Initialize the scraper
        const scraperUI = new Crawl4AIScraper({
            apiBaseUrl: 'http://localhost:8000',
            apiPrefix: '/api/scraper'
        });
        
        scraperUI.initialize();
    </script>
</body>
</html>
```

#### Option B: Use Individual Components
```html
<!DOCTYPE html>
<html>
<head>
    <title>My Scraper App</title>
    <!-- Include your own styles -->
    <link rel="stylesheet" href="src/css/scraper-ui.css">
</head>
<body>
    <!-- Load scraper UI component -->
    <div id="scraper-container"></div>
    
    <!-- Include individual JS modules -->
    <script src="src/js/core/api-client.js"></script>
    <script src="src/js/modules/scraper-ui.js"></script>
    <script>
        // Configure and initialize
        const apiClient = new Crawl4AIApiClient({
            baseUrl: 'http://localhost:8000',
            apiPrefix: '/api/scraper'
        });
        
        const scraperUI = new Crawl4AIScraperUI(apiClient);
        scraperUI.initialize();
    </script>
</body>
</html>
```

## API Integration

Your backend API should implement these endpoints:

### Required Endpoints

```javascript
GET    /api/scraper/health         // Scraper health check
POST   /api/scraper/trigger        // Start scraping job
GET    /api/scraper/status         // Get current job status
GET    /api/scraper/results        // Get scraped results
GET    /api/scraper/stats          // Get scraping statistics
GET    /api/scraper/categories     // Get result categories
GET    /api/scraper/search         // Search results
```

### API Response Format

All endpoints should return JSON in this format:

```javascript
{
  "success": true,
  "data": { /* endpoint-specific data */ },
  "error": null,           // Error message if success is false
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Example API Responses

#### Health Check
```javascript
GET /api/scraper/health
{
  "success": true,
  "data": {
    "status": "healthy",    // "healthy", "degraded", "error"
    "message": "All systems operational"
  }
}
```

#### Trigger Scraping
```javascript
POST /api/scraper/trigger
{
  "max_items": 100,
  "include_media": true,
  "include_documents": true,
  "base_url": "https://example.com"
}

Response:
{
  "success": true,
  "data": {
    "job_id": "job_123",
    "status": "started",
    "message": "Scraping job started successfully"
  }
}
```

#### Get Results
```javascript
GET /api/scraper/results?page=1&limit=20&search=keyword&category=news
{
  "success": true,
  "data": [
    {
      "id": "result_1",
      "title": "Example Page",
      "description": "Page description",
      "url": "https://example.com/page1",
      "scraped_at": "2023-01-01T00:00:00Z",
      "content": "Page content...",
      "metadata": { /* additional data */ }
    }
  ]
}
```

## Configuration

### API Client Configuration

```javascript
const apiClient = new Crawl4AIApiClient({
    baseUrl: 'http://localhost:8000',
    apiPrefix: '/api/scraper',
    headers: {
        'Authorization': 'Bearer your-token',
        'Custom-Header': 'value'
    },
    endpoints: {
        health: '/custom/health',
        trigger: '/custom/start',
        // ... override any endpoint
    }
});
```

### UI Configuration

```javascript
const scraperUI = new Crawl4AIScraperUI(apiClient, {
    resultsPerPage: 20,
    autoRefresh: true,
    refreshInterval: 30000,  // 30 seconds
    enableProgress: true
});
```

## Components

### 1. Scraper UI Component (`scraper-ui.html`)

Main interface with:
- Health status indicator
- Quick action buttons (Quick/Full scrape)
- Real-time progress display
- Results browser with search and pagination

### 2. Configuration Modal (`config-modal.html`)

Advanced configuration interface:
- General settings (URL, limits, depth)
- Advanced options (delays, timeouts, retries)
- Scheduling options
- Preset configurations
- Import/export functionality

### 3. API Client (`api-client.js`)

Centralized API communication:
- RESTful API wrapper
- Error handling
- Configurable endpoints
- Request/response formatting

### 4. UI Controller (`scraper-ui.js`)

UI logic and interactions:
- Status monitoring
- Result display and pagination
- Search and filtering
- Progress tracking

## Styling

The package includes default CSS, but you can customize the appearance:

```css
/* Override default styles */
.crawl4ai-scraper-panel {
    border: 1px solid #your-color;
    border-radius: 8px;
}

.btn-primary {
    background-color: #your-primary-color;
}

/* Customize result items */
.result-item {
    padding: 20px;
    margin: 10px 0;
}
```

## Advanced Usage

### Custom Result Display

```javascript
class MyScraperUI extends Crawl4AIScraperUI {
    displayResults(results) {
        // Custom result rendering logic
        const resultsList = document.getElementById('resultsList');
        
        const customHTML = results.map(result => `
            <div class="my-custom-result">
                <h3>${result.title}</h3>
                <p>${result.description}</p>
                <div class="my-metadata">
                    <!-- Custom metadata display -->
                </div>
            </div>
        `).join('');
        
        resultsList.innerHTML = customHTML;
    }
    
    viewResultDetails(resultId) {
        // Custom detail view logic
        this.showCustomModal(resultId);
    }
}
```

### Integration with Crawl4AI

```python
# Example Flask/FastAPI backend integration
from crawl4ai import WebCrawler

@app.post('/api/scraper/trigger')
async def trigger_scraping(config: dict):
    crawler = WebCrawler()
    
    # Configure crawler based on frontend config
    await crawler.astart()
    
    results = await crawler.arun(
        url=config['base_url'],
        # Map frontend config to crawl4ai parameters
    )
    
    await crawler.aclose()
    
    return {
        'success': True,
        'data': {
            'job_id': generate_job_id(),
            'status': 'completed',
            'results': process_results(results)
        }
    }
```

## Examples

Check the `examples/` directory for complete integration examples:

- `examples/basic/` - Simple integration
- `examples/advanced/` - Custom styling and functionality  
- `examples/flask-backend/` - Complete Flask backend
- `examples/fastapi-backend/` - FastAPI integration

## Browser Support

- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/unclecode/crawl4ai/issues)
- Documentation: [Full documentation](https://crawl4ai.readthedocs.io/)
- Community: [Join discussions](https://github.com/unclecode/crawl4ai/discussions)

## Changelog

### Version 1.0.0
- Initial release
- Complete scraper UI interface
- Configuration management
- Real-time progress tracking
- Results browser with search/filter
- API client with flexible configuration
- Responsive design
- Documentation and examples
