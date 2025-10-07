FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN pip install playwright
RUN playwright install-deps chromium
RUN playwright install chromium

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-agar.txt .
RUN pip install -r requirements-agar.txt

# Copy the entire crawl4ai module
COPY crawl4ai/ ./crawl4ai/
COPY deploy/agar-scraper/agar_service.py ./
COPY deploy/agar-scraper/database_integration.py ./
COPY deploy/agar-scraper/health_monitor.py ./

# Create necessary directories
RUN mkdir -p /app/output /app/logs

# Create non-root user for security
RUN useradd -r -s /bin/false scraper
RUN chown -R scraper:scraper /app
USER scraper

# Expose port for health checks and API
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "agar_service.py"]
