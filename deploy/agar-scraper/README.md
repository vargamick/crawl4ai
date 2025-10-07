# Agar Scraper Service Deployment

## Overview

The Agar Scraper Service is a containerized application that periodically scrapes the Agar Cleaning Systems product catalog and integrates with the Ask Agar system. It provides REST API endpoints for manual scraping triggers and real-time status monitoring.

## Architecture

```
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Agar Website      │    │  Agar Scraper    │    │  Ask Agar API       │
│   (agar.com.au)     │◄───┤  Service          ├───►│  (Flask + Flowise)  │
└─────────────────────┘    │  - Crawl4ai       │    └─────────────────────┘
                           │  - Playwright     │              │
                           │  - Scheduler      │              │
                           │  - REST API       │              ▼
                           └─────────┬─────────┘    ┌─────────────────────┐
                                     │              │  PostgreSQL DB      │
                                     │              │  - Agar Products    │
                                     └─────────────►│  - Media & Docs     │
                                                    │  - Categories       │
                                                    └─────────────────────┘
```

## Deployment Options

### Option 1: Coolify Deployment (Recommended)

1. **Clone Repository**
   ```bash
   git clone https://github.com/vargamick/crawl4ai.git
   cd crawl4ai
   ```

2. **Deploy via Coolify**
   - Add new service in Coolify dashboard
   - Set source to this repository
   - Set build context to `/deploy/agar-scraper/`
   - Configure environment variables (see below)
   - Deploy and monitor

3. **Environment Variables for Coolify**
   ```
   DATABASE_URL=postgresql://askagar_user:password@postgres:5432/askagar_db
   AGAR_BASE_URL=https://agar.com.au/products/
   FLASK_API_URL=http://askagar-api:5000
   MAX_PRODUCTS=0
   DELAY_SECONDS=2.0
   PORT=8080
   ```

### Option 2: Docker Compose

1. **Build and Deploy**
   ```bash
   cd deploy/agar-scraper
   cp .env.example .env  # Configure environment variables
   docker-compose up -d
   ```

2. **Environment File (.env)**
   ```
   POSTGRES_DB=askagar_db
   POSTGRES_USER=askagar_user
   POSTGRES_PASSWORD=your_secure_password
   ```

## Integration with Ask Agar API

### Extended Flask Routes

Add these routes to your existing Ask Agar Flask application:

```python
# Add to your main Flask app
from agar_integration import agar_bp
app.register_blueprint(agar_bp)
```

### API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/agar/products` | GET | List products with filtering |
| `/api/agar/products/{id}` | GET | Get product details with media/docs |
| `/api/agar/categories` | GET | List product categories |
| `/api/scrape/trigger` | POST | Manually trigger scraping |
| `/api/scrape/status` | GET | Get scraping job status |
| `/api/scrape/history` | GET | Get scraping job history |
| `/health` | GET | Service health check |

## Database Schema

The service automatically creates the following tables:

- `agar_products` - Core product information
- `agar_media` - Product images/videos with metadata
- `agar_documents` - PDFs, data sheets, manuals
- `agar_categories` - Hierarchical product categories
- `agar_product_categories` - Many-to-many relationships
- `agar_scraping_jobs` - Job tracking and history

## Monitoring and Maintenance

### Health Checks

```bash
# Check service health
curl http://agar-scraper:8080/health

# Check scraping status
curl http://agar-scraper:8080/api/scrape/status
```

### Logs

```bash
# View real-time logs
docker logs -f agar-scraper

# View persistent logs
docker exec agar-scraper tail -f /app/logs/agar_service.log
```

### Manual Scraping

```bash
# Trigger immediate scraping
curl -X POST http://agar-scraper:8080/api/scrape/trigger \
  -H "Content-Type: application/json" \
  -d '{"max_products": 10}'
```

## Scheduling

The service runs on the following schedule:
- **Daily**: 2:00 AM - Regular product update scraping
- **Weekly**: Sunday 1:00 AM - Deep catalog synchronization

## Security Considerations

1. **Container Security**
   - Service runs as non-root user
   - Minimal base image with security updates
   - Read-only filesystem where possible

2. **Network Security**
   - Internal network communication only
   - External access via reverse proxy (Traefik)
   - Rate limiting on API endpoints

3. **Data Security**
   - Database credentials via environment variables
   - No sensitive data in container images
   - Encrypted communication with external services

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database connectivity
   docker exec agar-scraper python -c "
   import asyncpg, asyncio
   async def test():
       conn = await asyncpg.connect('postgresql://...')
       print('Connected successfully')
   asyncio.run(test())
   "
   ```

2. **Playwright Browser Issues**
   ```bash
   # Reinstall browser dependencies
   docker exec agar-scraper playwright install chromium
   ```

3. **Scraping Failures**
   ```bash
   # Check Agar website accessibility
   docker exec agar-scraper curl -I https://agar.com.au/products/
   ```

### Performance Tuning

1. **Memory Usage**
   - Increase container memory limit if scraping large catalogs
   - Adjust `MAX_PRODUCTS` to limit scope
   - Monitor memory usage during scraping

2. **Network Performance**
   - Increase `DELAY_SECONDS` if rate limiting occurs
   - Use persistent connections for database
   - Enable HTTP/2 for faster parallel requests

## Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements-agar.txt

# Install Playwright browser
playwright install chromium

# Set environment variables
export DATABASE_URL="postgresql://localhost:5432/askagar_dev"
export AGAR_BASE_URL="https://agar.com.au/products/"

# Run service
python agar_service.py
```

### Testing

```bash
# Run unit tests
python -m pytest tests/

# Test single product extraction
python -c "
import asyncio
from crawl4ai.agar.agar_scraper import AgarScraper
from crawl4ai.agar.schemas import ScrapingConfig

async def test():
    config = ScrapingConfig(base_url='https://agar.com.au', verbose=True)
    scraper = AgarScraper(config)
    result = await scraper.scrape_single_product('https://agar.com.au/product/country-garden/')
    print(f'Success: {bool(result)}')

asyncio.run(test())
"
```

## Support

For issues or questions:
1. Check service logs for error details
2. Verify network connectivity to Agar website
3. Confirm database schema is properly initialized
4. Review Coolify deployment logs for container issues

## Version History

- **v1.0.0** - Initial deployment with basic scraping functionality
- **v1.1.0** - Added API integration and health monitoring
- **v1.2.0** - Enhanced error handling and retry logic
