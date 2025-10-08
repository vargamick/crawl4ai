# 🔧 Crawl4AI Scraping Endpoint Configuration Guide

## 📋 Overview

The Docker deployment includes a fully functional FastAPI backend that integrates with the Crawl4AI library. Here's how to configure and use the scraping endpoints.

## 🚀 Quick Start

### 1. API Base URL
```
http://localhost:8000
```

### 2. Main Scraping Endpoint
```
POST /api/scraper/trigger
```

## ⚙️ Configuration Options

### Basic Configuration Model
```json
{
  "urls": ["https://example.com", "https://another-site.com"],
  "max_items": 10,
  "include_media": true,
  "include_documents": true,
  "include_metadata": true,
  "extraction_strategy": "basic",
  "chunking_strategy": "regex"
}
```

### Parameter Details

#### `urls` (optional)
- **Type**: Array of strings
- **Default**: ["https://example.com", "https://httpbin.org/html", "https://quotes.toscrape.com"]
- **Description**: List of URLs to scrape
- **Example**: `["https://news.ycombinator.com", "https://reddit.com/r/python"]`

#### `max_items` (optional)
- **Type**: Integer
- **Default**: 100
- **Description**: Maximum number of URLs to process
- **Example**: `5` (limit to 5 URLs)

#### `include_media` (optional)
- **Type**: Boolean
- **Default**: true
- **Description**: Whether to extract and include media files information
- **Example**: `false` (skip media extraction)

#### `include_documents` (optional)
- **Type**: Boolean
- **Default**: true
- **Description**: Whether to include document attachments
- **Example**: `true`

#### `include_metadata` (optional)
- **Type**: Boolean
- **Default**: true
- **Description**: Whether to include page metadata (title, description, etc.)
- **Example**: `true`

#### `extraction_strategy` (optional)
- **Type**: String
- **Options**: `"basic"`, `"llm"`, `"cosine"`
- **Default**: `"basic"`
- **Description**: Content extraction method
  - `"basic"`: Standard HTML to markdown conversion
  - `"llm"`: AI-powered content extraction (requires LLM setup)
  - `"cosine"`: Cosine similarity-based content filtering

#### `chunking_strategy` (optional)
- **Type**: String
- **Options**: `"regex"`, `null`
- **Default**: `"regex"`
- **Description**: How to chunk the extracted content
  - `"regex"`: Use regex-based chunking
  - `null`: No chunking applied

## 🎯 Usage Examples

### Example 1: Basic Website Scraping
```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://httpbin.org/html"],
    "max_items": 2,
    "extraction_strategy": "basic"
  }'
```

### Example 2: News Sites with Media
```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://news.ycombinator.com", 
      "https://techcrunch.com",
      "https://arstechnica.com"
    ],
    "max_items": 5,
    "include_media": true,
    "include_metadata": true,
    "extraction_strategy": "basic"
  }'
```

### Example 3: Advanced Content Extraction
```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://wikipedia.org/wiki/Artificial_intelligence"],
    "max_items": 1,
    "extraction_strategy": "cosine",
    "chunking_strategy": "regex",
    "include_metadata": true
  }'
```

### Example 4: Minimal Configuration
```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{}' 
```
*This will use all default values and scrape the default URLs*

## 📊 Response Format

### Successful Trigger Response
```json
{
  "success": true,
  "job_id": "job_a1b2c3d4",
  "message": "Scraping job queued successfully"
}
```

### Job Status Response
```json
{
  "current_job": {
    "job_id": "job_a1b2c3d4",
    "status": "completed",
    "config": { ... },
    "created_at": "2025-01-07T12:55:00",
    "results_count": 3
  },
  "scraping_available": true,
  "active_jobs": 0
}
```

## 🔍 Monitoring & Management Endpoints

### Check Job Status
```bash
GET /api/scraper/status
```

### Get Specific Job Details
```bash
GET /api/scraper/jobs/{job_id}
```

### Get All Jobs
```bash
GET /api/scraper/jobs?limit=10
```

### Get Results
```bash
GET /api/scraper/results?page=1&limit=10&search=python
```

### Search Results
```bash
GET /api/scraper/search?q=artificial%20intelligence&page=1&limit=20
```

### Get Statistics
```bash
GET /api/scraper/stats
```

## 🌐 Frontend Integration

The embeddable JavaScript widget automatically connects to these endpoints. Configure the API URL in your frontend:

### Update API Configuration
```javascript
// In your webpage
const scraper = Crawl4AIScraper.embed('#container', {
  apiBaseUrl: 'http://localhost:8000',
  // ... other options
});
```

### Environment Variable Configuration
Add to your `.env` file:
```bash
# API Configuration
API_PORT=8000
CORS_ORIGINS=*
LOG_LEVEL=info

# Crawl4AI Configuration
MAX_WORKERS=1
CRAWLER_VERBOSE=true
CACHE_DIR=/app/cache
TEMP_DIR=/app/temp
```

## 🔧 Advanced Configuration

### Custom Extraction Strategies
To add custom extraction strategies, modify the `api-wrapper/app.py`:

```python
# Add your custom extraction logic in execute_scraping_job function
if config.extraction_strategy == "custom":
    # Your custom extraction logic here
    extraction_strategy = YourCustomStrategy()
```

### Rate Limiting
The current implementation includes a 1-second delay between requests. Modify in `execute_scraping_job`:

```python
# Rate limiting (modify as needed)
await asyncio.sleep(1)  # Change to desired delay
```

### Custom URL Patterns
To add URL validation or custom patterns:

```python
# In ScrapeConfig model
from pydantic import validator

class ScrapeConfig(BaseModel):
    # ... existing fields ...
    
    @validator('urls')
    def validate_urls(cls, v):
        if v:
            for url in v:
                if not url.startswith(('http://', 'https://')):
                    raise ValueError(f'Invalid URL: {url}')
        return v
```

## 🧪 Testing the Configuration

### Using the Landing Page
Visit http://localhost:3001 and use the built-in API testing buttons.

### Using curl
```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs

# Trigger a basic scraping job
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"], "max_items": 1}'
```

### Using Python
```python
import requests

# Trigger scraping
response = requests.post('http://localhost:8000/api/scraper/trigger', json={
    'urls': ['https://example.com', 'https://httpbin.org/html'],
    'max_items': 2,
    'extraction_strategy': 'basic',
    'include_metadata': True
})

job = response.json()
print(f"Job ID: {job['job_id']}")

# Check status
status_response = requests.get('http://localhost:8000/api/scraper/status')
print(status_response.json())
```

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure CORS is properly configured in the API
2. **Connection Refused**: Check if the API container is running (`docker compose ps`)
3. **Timeout Issues**: Large scraping jobs may take time - check job status regularly
4. **Memory Issues**: Limit `max_items` for large-scale scraping

### Debug Mode
Enable verbose logging by setting environment variable:
```bash
CRAWLER_VERBOSE=true
LOG_LEVEL=debug
```

### Container Logs
```bash
# View API container logs
docker compose logs api -f

# View all container logs
docker compose logs -f
```

## 💡 Best Practices

1. **Start Small**: Begin with 1-2 URLs to test configuration
2. **Rate Limiting**: Respect target websites with appropriate delays
3. **Error Handling**: Always check job status before retrieving results
4. **Resource Management**: Monitor memory usage for large scraping jobs
5. **URL Validation**: Ensure URLs are accessible and valid before scraping

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Health Monitoring**: http://localhost:8000/health  
- **Landing Page**: http://localhost:3001
- **Docker Logs**: `docker compose logs api`

The scraping endpoint is now fully configured and ready to use with real Crawl4AI functionality!
