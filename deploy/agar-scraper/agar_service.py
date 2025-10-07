#!/usr/bin/env python3
"""
Agar Scraper Service - Main application entry point.

This service provides:
1. Scheduled scraping of Agar product catalog
2. REST API for manual scraping triggers
3. Health monitoring endpoints
4. Database integration for scraped data
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add crawl4ai to Python path
sys.path.insert(0, '/app')

from flask import Flask, jsonify, request
from flask_cors import CORS
import schedule
import threading
import time

from crawl4ai.agar.agar_scraper import AgarScraper
from crawl4ai.agar.schemas import ScrapingConfig
from database_integration import AgarDatabaseIntegrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/agar_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Flask application setup
app = Flask(__name__)
CORS(app)

# Configuration from environment variables
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/askagar_db')
AGAR_BASE_URL = os.getenv('AGAR_BASE_URL', 'https://agar.com.au/products/')
SCRAPE_SCHEDULE = os.getenv('SCRAPE_SCHEDULE', '0 2 * * *')  # Daily at 2 AM
MAX_PRODUCTS = int(os.getenv('MAX_PRODUCTS', '0')) or None
DELAY_SECONDS = float(os.getenv('DELAY_SECONDS', '2.0'))

# Global database integrator
db_integrator = None
current_job_id = None


async def initialize_database():
    """Initialize database connection."""
    global db_integrator
    try:
        db_integrator = AgarDatabaseIntegrator(DATABASE_URL)
        await db_integrator.connect()
        logger.info("Database connection initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


async def perform_scraping(job_id=None, max_products=None):
    """Perform the actual scraping operation."""
    global current_job_id
    
    if job_id:
        current_job_id = job_id
    else:
        current_job_id = await db_integrator.create_scraping_job()
    
    try:
        logger.info(f"Starting scraping job {current_job_id}")
        
        # Configure scraper
        config = ScrapingConfig(
            base_url=AGAR_BASE_URL,
            max_products=max_products or MAX_PRODUCTS,
            delay_seconds=DELAY_SECONDS,
            output_dir='/app/output',
            verbose=True,
            include_images=True,
            include_documents=True,
            include_categories=True
        )
        
        # Run scraper
        scraper = AgarScraper(config)
        catalog_data = await scraper.run_complete_scraping()
        
        # Save to database
        await db_integrator.save_catalog_data(catalog_data, current_job_id)
        
        logger.info(f"Scraping job {current_job_id} completed successfully")
        return {
            'job_id': current_job_id,
            'status': 'completed',
            'products_scraped': len(catalog_data.products),
            'media_processed': len(catalog_data.media),
            'documents_processed': len(catalog_data.documents),
            'categories_processed': len(catalog_data.categories),
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Scraping job {current_job_id} failed: {e}")
        if db_integrator:
            await db_integrator.update_job_error(current_job_id, str(e))
        raise


def scheduled_scraping():
    """Wrapper for scheduled scraping to handle async."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(perform_scraping())
    except Exception as e:
        logger.error(f"Scheduled scraping failed: {e}")
    finally:
        loop.close()


# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check database connectivity
        if not db_integrator:
            return jsonify({'status': 'unhealthy', 'reason': 'Database not initialized'}), 503
        
        # Check last successful scrape (sync check)
        return jsonify({
            'status': 'healthy',
            'service': 'agar-scraper',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


@app.route('/api/scrape/trigger', methods=['POST'])
def trigger_scrape():
    """Manually trigger a scraping job."""
    try:
        data = request.get_json() or {}
        max_products = data.get('max_products')
        
        # Start scraping in background thread
        def run_scrape():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(perform_scraping(max_products=max_products))
                logger.info(f"Manual scraping completed: {result}")
            except Exception as e:
                logger.error(f"Manual scraping failed: {e}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_scrape)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Scraping job started',
            'job_id': current_job_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to trigger scraping: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape/status', methods=['GET'])
def get_scraping_status():
    """Get current scraping status."""
    try:
        if not current_job_id:
            return jsonify({'message': 'No active scraping job'})
        
        # In a real implementation, you'd check database for job status
        return jsonify({
            'job_id': current_job_id,
            'status': 'running',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape/history', methods=['GET'])
def get_scraping_history():
    """Get scraping job history."""
    try:
        # This would query the database for historical jobs
        return jsonify({
            'message': 'Historical data would be retrieved from database',
            'jobs': []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def setup_scheduling():
    """Setup scheduled scraping."""
    # Schedule daily scraping at 2 AM
    schedule.every().day.at("02:00").do(scheduled_scraping)
    
    # Schedule weekly deep scrape on Sundays at 1 AM
    schedule.every().sunday.at("01:00").do(scheduled_scraping)
    
    logger.info("Scraping schedule configured")


def run_scheduler():
    """Run the scheduler in a separate thread."""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


async def startup():
    """Application startup sequence."""
    logger.info("Starting Agar Scraper Service")
    
    # Initialize database
    if not await initialize_database():
        logger.error("Failed to initialize database, exiting")
        sys.exit(1)
    
    # Setup scheduling
    setup_scheduling()
    
    # Start scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Agar Scraper Service started successfully")


if __name__ == '__main__':
    # Run startup sequence
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(startup())
    loop.close()
    
    # Start Flask application
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
