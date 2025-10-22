# Crawl4AI Docker Network Setup Guide

## Overview

This guide sets up a complete local Docker network containing:
- **Crawl4AI Server** (Backend API) on port `11235`
- **Crawl4AI Frontend** (Web Interface) on port `3000`
- **Shared network** for inter-service communication

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 crawl4ai-network                        │
│                                                         │
│  ┌─────────────────────┐    ┌─────────────────────────┐│
│  │   crawl4ai-server   │    │   crawl4ai-frontend     ││
│  │   Port: 11235       │◄──►│   Port: 3000           ││
│  │   API Endpoint      │    │   Web Interface        ││
│  └─────────────────────┘    └─────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available for containers
- Ports 3000 and 11235 available

### 2. Launch the Network

```bash
# Start both services
docker-compose -f docker-compose-network.yml up -d

# Or with custom environment
cp .env.network .env
docker-compose -f docker-compose-network.yml up -d

# View logs
docker-compose -f docker-compose-network.yml logs -f
```

### 3. Access Services

- **Frontend Web Interface**: http://localhost:3000
- **Backend API**: http://localhost:11235
- **Health Check**: http://localhost:11235/health

### 4. Test the Setup

```bash
# Test backend API directly
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "extraction_options": {
      "extract_media": true,
      "extract_links": true
    }
  }'

# Check frontend is serving
curl http://localhost:3000
```

## Configuration

### Environment Variables

Copy `.env.network` to `.env` and customize:

```bash
# Image configuration
IMAGE=unclecode/crawl4ai
TAG=latest
FRONTEND_PORT=3000

# Optional API keys (create .llm.env for sensitive data)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### LLM Integration

Create `.llm.env` file for API keys:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
```

## Development Mode

For development with hot reload:

```bash
# Create development override
docker-compose -f docker-compose-network.yml -f docker-compose-network.dev.yml up
```

## Service Details

### Crawl4AI Server (Backend)
- **Container**: `crawl4ai-server`
- **Port**: 11235
- **Health Check**: `/health` endpoint
- **Resources**: 4GB memory limit, 1GB reserved
- **Features**: 
  - Full Crawl4AI API functionality
  - LLM provider integration
  - Browser automation with Chromium
  - Caching and temp storage

### Crawl4AI Frontend (Web Interface)
- **Container**: `crawl4ai-frontend`
- **Port**: 3000 (configurable via FRONTEND_PORT)
- **Technology**: Nginx serving static files
- **Features**:
  - Web-based crawling interface
  - Real-time crawling results
  - Configuration management
  - Example templates

## Network Communication

The frontend communicates with the backend via:
- **Internal network**: `crawl4ai-network` (Docker bridge)
- **Service discovery**: `crawl4ai-server:11235`
- **External access**: `localhost:11235` and `localhost:3000`

## Persistent Storage

### Volumes
- `crawl4ai-cache`: Crawler cache data
- `crawl4ai-temp`: Temporary processing files
- `/dev/shm`: Shared memory for Chromium performance

### Logs
- Frontend logs: `./crawl4ai-scraper-frontend/logs/`
- Backend logs: Docker container logs

## Troubleshooting

### Common Issues

**Port conflicts**:
```bash
# Check port usage
lsof -i :3000
lsof -i :11235

# Change frontend port
FRONTEND_PORT=3001 docker-compose -f docker-compose-network.yml up
```

**Memory issues**:
```bash
# Check container memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
```

**Service communication**:
```bash
# Check network connectivity
docker network ls
docker network inspect crawl4ai-network

# Test internal communication
docker exec crawl4ai-frontend curl http://crawl4ai-server:11235/health
```

**Build issues**:
```bash
# Force rebuild
docker-compose -f docker-compose-network.yml build --no-cache

# Pull latest images
docker-compose -f docker-compose-network.yml pull
```

### Health Checks

Monitor service health:

```bash
# Check service status
docker-compose -f docker-compose-network.yml ps

# View health check logs
docker inspect crawl4ai-server | grep -A 10 Health
```

## Production Considerations

### Security
- Use environment files for sensitive data
- Consider adding authentication to the API
- Set up proper CORS origins instead of wildcard

### Scaling
- Use multiple worker processes
- Implement load balancing with Traefik (labels included)
- Consider horizontal scaling with Docker Swarm

### Monitoring
- Add logging aggregation
- Set up health monitoring
- Implement metrics collection

## Commands Reference

### Lifecycle Management
```bash
# Start services
docker-compose -f docker-compose-network.yml up -d

# Stop services
docker-compose -f docker-compose-network.yml down

# Restart specific service
docker-compose -f docker-compose-network.yml restart crawl4ai-server

# View logs
docker-compose -f docker-compose-network.yml logs -f crawl4ai-frontend
```

### Maintenance
```bash
# Update images
docker-compose -f docker-compose-network.yml pull
docker-compose -f docker-compose-network.yml up -d

# Clean up
docker-compose -f docker-compose-network.yml down -v  # Remove volumes
docker system prune -f  # Clean up unused containers/images
```

### Development
```bash
# Build from source
docker-compose -f docker-compose-network.yml build

# Development mode
docker-compose -f docker-compose-network.yml -f docker-compose-network.dev.yml up
```

## Integration Examples

### API Usage from Frontend
The frontend automatically connects to the backend. For custom integration:

```javascript
// Frontend JavaScript example
const response = await fetch('/crawl', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    urls: ['https://example.com'],
    extraction_options: { extract_media: true }
  })
});
```

### Direct API Access
```bash
# Health check
curl http://localhost:11235/health

# Crawl request
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://example.com"]}'
```

## Files Created

- `docker-compose-network.yml`: Main configuration
- `.env.network`: Environment template
- `DOCKER_NETWORK_SETUP.md`: This documentation

## Next Steps

1. **Test the setup**: Start services and verify both endpoints work
2. **Configure API keys**: Add LLM provider keys in `.llm.env`
3. **Customize frontend**: Modify the web interface as needed
4. **Scale if needed**: Add more workers or implement load balancing

The network is now ready for local development and testing of Crawl4AI with a complete web interface!
