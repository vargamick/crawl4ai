# 🕷️ Crawl4AI Scraper Frontend

Embeddable web scraper interface for Crawl4AI - easily integrate web scraping capabilities into any web application.

## ✨ Features

- **🚀 Easy Integration**: Single script tag deployment
- **🎨 Modern UI**: Responsive design with comprehensive scraping controls
- **🔧 Configurable**: Extensive configuration options via UI or API
- **🔒 Secure**: CSS scoping to prevent conflicts with host applications
- **📱 Responsive**: Works on desktop, tablet, and mobile devices
- **⚡ Performance**: Optimized bundling with webpack
- **🌐 API Integration**: RESTful API communication with error handling
- **📊 Real-time Updates**: Live status monitoring and progress tracking

## 🚀 Quick Start

### 1. Basic Integration

```html
<!DOCTYPE html>
<html>
<head>
    <title>My App with Crawl4AI</title>
</head>
<body>
    <div id="scraper-container"></div>
    
    <!-- Load Crawl4AI Scraper -->
    <script src="https://cdn.jsdelivr.net/npm/crawl4ai-scraper-frontend/dist/crawl4ai-scraper.min.js"></script>
    <script>
        Crawl4AIScraper.embed('#scraper-container', {
            apiUrl: 'http://localhost:8000'
        });
    </script>
</body>
</html>
```

### 2. Advanced Integration

```javascript
// Create instance with custom configuration
const scraper = await Crawl4AIScraper.embed('#my-container', {
    apiUrl: 'https://my-api.example.com',
    apiPrefix: '/api/v1/scraper',
    theme: 'compact',
    enableShadowDOM: true,
    autoInit: true
});

// Listen for events
scraper.addEventListener('scrapingStarted', (event) => {
    console.log('Scraping started:', event.detail);
});

scraper.addEventListener('error', (event) => {
    console.error('Scraper error:', event.detail);
});

// Configure programmatically
scraper.configure({
    maxItems: 500,
    includeMedia: false,
    autoRefreshInterval: 60000
});
```

## 📦 Installation

### Via CDN (Recommended)
```html
<script src="https://cdn.jsdelivr.net/npm/crawl4ai-scraper-frontend/dist/crawl4ai-scraper.min.js"></script>
```

### Via NPM
```bash
npm install crawl4ai-scraper-frontend
```

```javascript
import Crawl4AIScraper from 'crawl4ai-scraper-frontend';

Crawl4AIScraper.embed('#container', { apiUrl: 'http://localhost:8000' });
```

### Local Build
```bash
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai/crawl4ai-scraper-frontend
npm install
npm run build
```

## 🎛️ Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiUrl` | string | `'http://localhost:8000'` | Base URL for Crawl4AI API |
| `apiPrefix` | string | `'/api/scraper'` | API endpoint prefix |
| `container` | string\|Element | - | Container selector or element |
| `theme` | string | `'default'` | UI theme (`'default'`, `'compact'`) |
| `enableShadowDOM` | boolean | `false` | Use Shadow DOM for isolation |
| `cssPrefix` | string | `'c4ai-'` | CSS class prefix for scoping |
| `autoInit` | boolean | `true` | Auto-initialize after embedding |
| `autoRefresh` | boolean | `true` | Enable automatic status refresh |
| `refreshInterval` | number | `30000` | Auto-refresh interval (ms) |
| `resultsPerPage` | number | `10` | Results per page in browser |

### API Configuration
```javascript
{
    apiUrl: 'https://api.example.com',
    apiPrefix: '/api/scraper',
    headers: {
        'Authorization': 'Bearer your-token',
        'X-API-Key': 'your-api-key'
    }
}
```

### UI Configuration
```javascript
{
    theme: 'compact',
    enableShadowDOM: true,
    cssPrefix: 'my-scraper-',
    autoRefresh: false,
    resultsPerPage: 20
}
```

## 📡 API Integration

The frontend expects a REST API with these endpoints:

### Health Check
```
GET /api/scraper/health
Response: { status: 'healthy', message: 'OK' }
```

### Trigger Scraping
```
POST /api/scraper/trigger
Body: { max_items: 100, include_media: true }
Response: { success: true, job_id: 'abc123' }
```

### Get Status
```
GET /api/scraper/status
Response: { 
    current_job: { job_id: 'abc123', status: 'running' },
    last_successful_scrape: { completed_at: '2024-01-01T00:00:00Z' }
}
```

### Get Results
```
GET /api/scraper/results?page=1&limit=10&search=query
Response: { 
    results: [...],
    total: 100,
    page: 1
}
```

### Get Categories
```
GET /api/scraper/categories
Response: ['category1', 'category2', ...]
```

### Get Statistics
```
GET /api/scraper/stats
Response: { 
    total_results: 1500,
    total_categories: 25,
    successful_jobs: 42
}
```

## 🎨 UI Components

### Main Interface
- **Status Monitoring**: Real-time scraper health and job status
- **Quick Actions**: Start quick or full scraping jobs
- **Results Browser**: Browse and search scraped results
- **Configuration**: Comprehensive settings modal

### Features
- **Pagination**: Navigate through large result sets
- **Search & Filter**: Find specific results by keywords or categories
- **Statistics**: View scraping performance metrics
- **Progress Tracking**: Real-time job progress (when supported by API)

## 🔧 Development

### Project Structure
```
crawl4ai-scraper-frontend/
├── src/
│   ├── js/
│   │   ├── embed.js          # Main embeddable entry point
│   │   ├── index.js          # Legacy entry point
│   │   ├── core/
│   │   │   └── api-client.js # API communication
│   │   └── modules/
│   │       └── scraper-ui.js # UI components
│   ├── css/
│   │   └── scraper-ui.css    # Styles
│   └── components/
│       ├── scraper-ui.html   # Main UI template
│       └── config-modal.html # Configuration modal
├── examples/                 # Usage examples
├── dist/                     # Built files
└── docs/                     # Documentation
```

### Build Commands
```bash
npm run build          # Build both dev and production versions
npm run build:dev      # Development build with source maps
npm run build:prod     # Production build (minified)
npm run watch          # Watch mode for development
npm run serve          # Start local development server
npm run serve:examples # Serve examples on port 8080
```

### Build Output
- `dist/crawl4ai-scraper.js` - Development version with source maps
- `dist/crawl4ai-scraper.min.js` - Production version (minified)
- `dist/crawl4ai-scraper.css` - Standalone CSS (legacy)

## 📚 Examples

### Basic Embed
```html
<!DOCTYPE html>
<html>
<head>
    <title>Basic Crawl4AI Integration</title>
</head>
<body>
    <div id="scraper-container"></div>
    <script src="dist/crawl4ai-scraper.min.js"></script>
    <script>
        Crawl4AIScraper.embed('#scraper-container', {
            apiUrl: 'http://localhost:8000'
        });
    </script>
</body>
</html>
```

### Multiple Instances
```javascript
// Standard instance
const scraper1 = Crawl4AIScraper.embed('#container-1', {
    apiUrl: 'http://localhost:8000',
    enableShadowDOM: false
});

// Shadow DOM instance  
const scraper2 = Crawl4AIScraper.embed('#container-2', {
    apiUrl: 'http://localhost:8000',
    enableShadowDOM: true,
    cssPrefix: 'scraper2-'
});
```

### Event Handling
```javascript
const scraper = await Crawl4AIScraper.embed('#container', config);

// Listen for initialization
scraper.addEventListener('initialized', (event) => {
    console.log('Scraper ready:', event.detail.instance);
});

// Listen for errors
scraper.addEventListener('error', (event) => {
    console.error('Error:', event.detail.error);
});

// Listen for scraping events
scraper.addEventListener('scrapingStarted', (event) => {
    console.log('Scraping started with config:', event.detail.config);
});

scraper.addEventListener('statsDisplayed', (event) => {
    console.log('Stats:', event.detail.stats);
});
```

### Custom Styling
```css
/* Override default styles */
[data-c4ai-instance] .crawl4ai-scraper-panel {
    border: 2px solid #your-color;
    border-radius: 12px;
}

[data-c4ai-instance] .btn-primary {
    background-color: #your-primary-color;
}
```

## 🔒 Security Considerations

### CSS Scoping
The frontend automatically scopes CSS using unique instance IDs to prevent conflicts:

```css
/* Generated scoped CSS */
[data-c4ai-instance="c4ai-abc123"] .crawl4ai-scraper-panel { ... }
```

### Shadow DOM
Enable Shadow DOM for complete isolation:
```javascript
Crawl4AIScraper.embed('#container', {
    enableShadowDOM: true  // Complete CSS and JS isolation
});
```

### API Security
Configure authentication headers:
```javascript
{
    apiUrl: 'https://secure-api.example.com',
    headers: {
        'Authorization': 'Bearer ' + getAuthToken(),
        'X-API-Key': 'your-api-key'
    }
}
```

## 🐛 Troubleshooting

### Common Issues

**1. Container not found**
```
Error: Container not found: #my-container
```
- Ensure the container element exists in DOM before calling `embed()`
- Use `document.addEventListener('DOMContentLoaded', ...)` if needed

**2. API connection failed**
```
Error: Failed to connect to scraper service
```
- Verify `apiUrl` is correct and accessible
- Check CORS configuration on your API server
- Verify API endpoints match expected format

**3. Styles not loading**
```
No styles applied to components
```
- Ensure build process completed successfully
- Check browser console for CSS loading errors
- Verify CSS scoping is working (inspect elements)

**4. Multiple instances conflicting**
```
Global method conflicts between instances
```
- Use unique `cssPrefix` for each instance
- Consider enabling `enableShadowDOM: true`
- Avoid global variable conflicts

### Debug Mode
Enable debugging:
```javascript
Crawl4AIScraper.embed('#container', {
    debug: true,  // Enable console logging
    apiUrl: 'http://localhost:8000'
});
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `npm test`
5. Build and verify: `npm run build`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Submit a Pull Request

### Development Setup
```bash
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai/crawl4ai-scraper-frontend
npm install
npm run watch    # Start development with auto-rebuild
npm run serve:examples  # Test with examples
```

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Main Project**: [Crawl4AI](https://github.com/unclecode/crawl4ai)
- **Documentation**: [Crawl4AI Docs](https://docs.crawl4ai.com)
- **Issues**: [GitHub Issues](https://github.com/unclecode/crawl4ai/issues)
- **NPM Package**: [crawl4ai-scraper-frontend](https://www.npmjs.com/package/crawl4ai-scraper-frontend)

---

Made with ❤️ by the Crawl4AI team
