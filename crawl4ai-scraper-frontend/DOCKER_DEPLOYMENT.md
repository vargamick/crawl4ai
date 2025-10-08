# 🐳 Docker Deployment Guide - Crawl4AI Frontend System

This guide covers deploying the Crawl4AI frontend system using Docker containers for both development and production environments.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)
- [Scaling](#scaling)

## 🚀 Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For cloning the repository
- **System Requirements**: 
  - Minimum: 2GB RAM, 2 CPU cores
  - Recommended: 4GB RAM, 4 CPU cores for production

### Verify Prerequisites

```bash
docker --version
docker compose version
```

## ⚡ Quick Start

1. **Clone and prepare the project:**
```bash
git clone <repository-url>
cd crawl4ai-scraper-frontend

# Copy environment configuration
cp .env.example .env
```

2. **Build and start services:**
```bash
# Development mode
docker compose up --build

# Or run in background
docker compose up -d --build
```

3. **Access the application:**
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Health**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs

## 🛠️ Development Deployment

### Development Configuration

The development setup uses:
- **Frontend**: Nginx serving static files on port 3000
- **API**: FastAPI with hot-reload on port 8000
- **Volumes**: Local directories mounted for live development
- **Logging**: Verbose logging enabled

### Development Commands

```bash
# Start development environment
docker compose up

# Build and start fresh
docker compose up --build --force-recreate

# View logs
docker compose logs -f

# Stop services
docker compose down

# Clean up (removes volumes)
docker compose down -v --remove-orphans
```

### Development Environment Variables

Create `.env` file from `.env.example` and customize:

```bash
# Development settings
NODE_ENV=development
PYTHON_ENV=development
LOG_LEVEL=debug
CRAWLER_VERBOSE=true

# Port configuration
FRONTEND_PORT=3000
API_PORT=8000

# CORS for development
CORS_ORIGINS=*
```

## 🏭 Production Deployment

### Production Setup

The production configuration includes:
- **Traefik**: Reverse proxy with SSL termination
- **Let's Encrypt**: Automatic SSL certificates
- **Security**: Enhanced security headers and restrictions
- **Monitoring**: Prometheus and Loki integration
- **Resource Limits**: CPU and memory constraints

### Production Commands

```bash
# Create production environment file
cp .env.example .env.prod

# Edit production configuration
nano .env.prod

# Deploy production stack
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# View production logs
docker compose -f docker-compose.prod.yml logs -f
```

### Production Environment Configuration

```bash
# Production settings (.env.prod)
NODE_ENV=production
PYTHON_ENV=production
LOG_LEVEL=warning

# Domain configuration
DOMAIN=your-domain.com
API_HOST=api.your-domain.com
FRONTEND_HOST=your-domain.com

# SSL configuration
ACME_EMAIL=admin@your-domain.com
SSL_ENABLED=true

# Security
CORS_ORIGINS=https://your-domain.com
API_BASIC_AUTH_USERS=admin:$$2y$$10$$... # htpasswd generated

# Resource limits
API_MEMORY_LIMIT=2G
API_CPU_LIMIT=2.0
MAX_WORKERS=2
```

### SSL Certificate Setup

For production with SSL, ensure:

1. **Domain DNS**: Point your domain to the server
2. **Firewall**: Open ports 80 and 443
3. **Email**: Set `ACME_EMAIL` for Let's Encrypt

```bash
# Create Traefik network (first time only)
docker network create traefik

# Deploy with SSL
docker compose -f docker-compose.prod.yml up -d
```

## ⚙️ Environment Configuration

### Core Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FRONTEND_PORT` | Frontend service port | 3000 | No |
| `API_PORT` | API service port | 8000 | No |
| `DOMAIN` | Production domain | localhost | Yes (prod) |
| `CORS_ORIGINS` | Allowed CORS origins | * | No |
| `LOG_LEVEL` | Logging level | info | No |
| `MAX_WORKERS` | API worker processes | 1 | No |

### Security Variables (Production)

| Variable | Description | Example |
|----------|-------------|---------|
| `API_BASIC_AUTH_USERS` | API basic auth | `admin:$2y$10$...` |
| `RATE_LIMIT` | Requests per minute | 60 |
| `MAX_CONCURRENT_JOBS` | Max concurrent scraping jobs | 3 |
| `REQUEST_TIMEOUT` | Request timeout (seconds) | 300 |

### Resource Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_MEMORY_LIMIT` | API memory limit | 2G |
| `API_CPU_LIMIT` | API CPU limit | 2.0 |
| `API_MEMORY_RESERVATION` | API memory reservation | 512M |
| `API_CPU_RESERVATION` | API CPU reservation | 0.5 |

## 📊 Monitoring and Health Checks

### Health Check Endpoints

- **API Health**: `GET /health` - Simple health check
- **API Detailed**: `GET /api/scraper/health` - Detailed status
- **Frontend Health**: `GET /health` - Nginx health

### Monitoring Stack (Production)

Enable monitoring with profiles:

```bash
# Start with monitoring
docker compose -f docker-compose.prod.yml --profile monitoring up -d

# Access monitoring services
# - Prometheus: http://prometheus.your-domain.com
# - Grafana: http://grafana.your-domain.com (if configured)
```

### Container Health Status

```bash
# Check container health
docker compose ps

# View health check logs
docker compose logs api | grep health
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
lsof -i :3000
lsof -i :8000

# Change ports in .env file
FRONTEND_PORT=3001
API_PORT=8001
```

#### 2. API Container Startup Failures

```bash
# Check API logs
docker compose logs api

# Common causes:
# - Crawl4AI installation issues
# - Python dependencies missing
# - Port conflicts
```

#### 3. Frontend Can't Reach API

```bash
# Check network connectivity
docker compose exec frontend ping api

# Verify API_BASE_URL in environment
docker compose exec frontend env | grep API_BASE_URL
```

#### 4. SSL Certificate Issues (Production)

```bash
# Check Traefik logs
docker compose -f docker-compose.prod.yml logs traefik

# Verify domain DNS resolution
nslookup your-domain.com

# Check certificate status
docker compose -f docker-compose.prod.yml exec traefik cat /letsencrypt/acme.json
```

### Debug Commands

```bash
# Enter container for debugging
docker compose exec api bash
docker compose exec frontend sh

# Check container resource usage
docker stats

# View detailed container info
docker compose exec api cat /proc/meminfo
docker compose exec api ps aux
```

### Log Analysis

```bash
# Follow all logs
docker compose logs -f

# API logs only
docker compose logs -f api

# Filter logs by level
docker compose logs api 2>&1 | grep ERROR
```

## 📈 Scaling

### Horizontal Scaling

Scale API instances:

```bash
# Scale API service
docker compose up -d --scale api=3

# For production with load balancing
docker compose -f docker-compose.prod.yml up -d --scale api=3
```

### Vertical Scaling

Adjust resource limits in `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Performance Optimization

1. **Enable HTTP/2** (Production with Traefik)
2. **Optimize Nginx** caching and compression
3. **Configure API** worker processes based on CPU cores
4. **Database** optimization for job storage (if implemented)
5. **CDN** integration for static assets

## 🔧 Advanced Configuration

### Custom Nginx Configuration

Override default Nginx config:

```bash
# Copy and modify
cp docker/nginx.conf docker/nginx.custom.conf

# Update docker-compose.yml
volumes:
  - ./docker/nginx.custom.conf:/etc/nginx/conf.d/default.conf:ro
```

### Custom API Configuration

Extend the FastAPI application:

```python
# api-wrapper/app.py modifications
@app.middleware("http")
async def custom_middleware(request: Request, call_next):
    # Custom middleware logic
    response = await call_next(request)
    return response
```

### Backup and Restore

```bash
# Backup volumes
docker run --rm -v crawl4ai-cache:/data -v $(pwd):/backup busybox tar czf /backup/cache-backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v crawl4ai-cache:/data -v $(pwd):/backup busybox tar xzf /backup/cache-backup.tar.gz -C /data
```

## 📝 Maintenance

### Regular Maintenance Tasks

```bash
# Update containers
docker compose pull
docker compose up -d

# Clean unused images
docker image prune -f

# Clean system
docker system prune -f

# Backup important data
docker compose exec api tar czf /backup/jobs.tar.gz /app/logs
```

### Log Rotation

Configure log rotation to prevent disk space issues:

```bash
# Add to crontab
0 2 * * * docker system prune -f --filter "until=24h"
```

---

## 🆘 Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review container logs: `docker compose logs`
3. Verify environment configuration
4. Check Docker and system resources

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)

---

**Next Steps**: After deployment, configure your embeddable widget to point to your deployed API endpoint and integrate it into your applications.
