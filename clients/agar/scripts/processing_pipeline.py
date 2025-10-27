#!/usr/bin/env python3
"""
Agar Processing Pipeline
Comprehensive parameterized pipeline for Crawl4AI scraping with independent step processing.

This pipeline builds upon universal_scraper.py as the foundation and provides:
- Category discovery from Agar website
- URL generation for all product pages
- Independent step processing with graceful failure handling
- Batch processing with configurable parameters
- Product file output organized by categories
- Integration with validation system

Usage:
    python processing_pipeline.py --step all --config pipeline_config.yaml
    python processing_pipeline.py --step category-discovery --config pipeline_config.yaml
    python processing_pipeline.py --step url-generation --batch-size 50
    python processing_pipeline.py --step scraping --categories "Floor Care,Kitchen" --batch-size 10
"""

import asyncio
import json
import os
import sys
import argparse
import yaml
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import time
import logging
from urllib.parse import urljoin, urlparse
import importlib.util

# Add path for universal scraper and validation system
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'pipeline'))
sys.path.append(os.path.dirname(__file__))

# Import universal scraper
try:
    from universal_scraper import UniversalScraper
except ImportError:
    print("❌ Error: Cannot import universal_scraper. Please check the path.")
    sys.exit(1)

# Import validation system
try:
    from validation_system import AgarValidationSystem
except ImportError:
    print("⚠️  Warning: Validation system not available. Continuing without validation.")
    AgarValidationSystem = None

# Crawl4AI imports for category discovery
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai import JsonCssExtractionStrategy
except ImportError:
    print("❌ Error: Cannot import crawl4ai. Please install crawl4ai first.")
    sys.exit(1)


class PipelineStep:
    """Base class for pipeline steps."""
    
    def __init__(self, name: str, config: Dict[str, Any], logger: logging.Logger):
        self.name = name
        self.config = config
        self.logger = logger
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error_message = None
    
    def check_prerequisites(self) -> tuple[bool, str]:
        """Check if prerequisites for this step are met."""
        return True, ""
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the pipeline step."""
        self.start_time = datetime.now()
        self.logger.info(f"🚀 Starting step: {self.name}")
        
        try:
            # Check prerequisites
            prereq_ok, prereq_msg = self.check_prerequisites()
            if not prereq_ok:
                raise Exception(f"Prerequisites not met: {prereq_msg}")
            
            # Execute step logic
            result = await self._execute_step()
            
            self.success = True
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            self.logger.info(f"✅ Step '{self.name}' completed successfully in {duration:.1f}s")
            
            return {
                "step": self.name,
                "success": True,
                "duration_seconds": duration,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "result": result
            }
            
        except Exception as e:
            self.success = False
            self.error_message = str(e)
            self.end_time = datetime.now()
            
            self.logger.error(f"❌ Step '{self.name}' failed: {e}")
            
            return {
                "step": self.name,
                "success": False,
                "error": str(e),
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None
            }
    
    async def _execute_step(self) -> Dict[str, Any]:
        """Override this method in subclasses."""
        raise NotImplementedError


class CategoryDiscoveryStep(PipelineStep):
    """Step to discover categories from Agar website."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        super().__init__("category-discovery", config, logger)
        self.base_url = config.get('base_url', 'https://agar.com.au')
        self.output_dir = config.get('output_dir', 'pipeline_data')
        self.categories_file = os.path.join(self.output_dir, 'categories.json')
    
    async def _execute_step(self) -> Dict[str, Any]:
        """Discover categories from Agar website navigation."""
        os.makedirs(self.output_dir, exist_ok=True)
        
        browser_config = BrowserConfig(headless=True, verbose=False)
        crawler_config = CrawlerRunConfig(
            page_timeout=30000,
            word_count_threshold=10,
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=JsonCssExtractionStrategy({
                "name": "category_extraction",
                "baseSelector": "body",
                "fields": [
                    {"name": "navigation_links", "selector": "nav a, .navigation a, .main-nav a, .menu a", "type": "text"},
                    {"name": "category_links", "selector": ".categories a, .category-link, .product-categories a", "type": "attribute", "attribute": "href"},
                    {"name": "product_category_names", "selector": ".categories a, .category-link, .product-categories a", "type": "text"},
                    {"name": "all_links", "selector": "a[href*='category'], a[href*='products'], a[href*='cleaning']", "type": "attribute", "attribute": "href"}
                ]
            }, verbose=True)
        )
        
        categories_discovered = {}
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # First, get main page to discover category structure
            main_result = await crawler.arun(url=self.base_url, config=crawler_config)
            
            if main_result.success and main_result.extracted_content:
                try:
                    main_data = json.loads(main_result.extracted_content)
                    if isinstance(main_data, list) and len(main_data) > 0:
                        main_data = main_data[0]
                    
                    self.logger.info("📊 Analyzing main page navigation...")
                    
                    # Extract category information from main page
                    category_links = main_data.get('category_links', [])
                    category_names = main_data.get('product_category_names', [])
                    all_links = main_data.get('all_links', [])
                    
                    self.logger.info(f"Found {len(category_links)} category links, {len(category_names)} names, {len(all_links)} total links")
                    
                    # Combine and process links
                    potential_categories = set()
                    
                    # Add direct category links
                    for link in category_links:
                        if link and not link.startswith('mailto:') and not link.startswith('tel:'):
                            potential_categories.add(link)
                    
                    for link in all_links:
                        if link and not link.startswith('mailto:') and not link.startswith('tel:'):
                            potential_categories.add(link)
                    
                    # Filter and process category links
                    for link in potential_categories:
                        # Convert relative URLs to absolute
                        if link.startswith('/'):
                            full_url = urljoin(self.base_url, link)
                        elif not link.startswith('http'):
                            continue
                        else:
                            full_url = link
                        
                        # Extract category name from URL or link text
                        category_name = self._extract_category_name(full_url, category_names)
                        
                        if category_name and self._is_valid_category_url(full_url):
                            categories_discovered[category_name] = {
                                "url": full_url,
                                "discovered_at": datetime.now().isoformat(),
                                "source": "main_navigation"
                            }
                    
                    self.logger.info(f"✅ Discovered {len(categories_discovered)} categories from main navigation")
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse main page extraction: {e}")
            
            # Additional discovery: try common category pages
            common_category_paths = [
                '/products',
                '/categories',
                '/cleaning-products',
                '/professional-cleaning',
                '/commercial-cleaning'
            ]
            
            for path in common_category_paths:
                try:
                    url = urljoin(self.base_url, path)
                    result = await crawler.arun(url=url, config=crawler_config)
                    
                    if result.success:
                        category_name = self._extract_category_name(url, [])
                        if category_name and category_name not in categories_discovered:
                            categories_discovered[category_name] = {
                                "url": url,
                                "discovered_at": datetime.now().isoformat(),
                                "source": "common_paths"
                            }
                            self.logger.info(f"✅ Added category from common path: {category_name}")
                    
                    await asyncio.sleep(1)  # Be respectful
                    
                except Exception as e:
                    self.logger.warning(f"Could not check category path {path}: {e}")
        
        # Add some manual categories if none discovered (fallback)
        if not categories_discovered:
            self.logger.warning("No categories discovered automatically, adding manual fallback categories")
            fallback_categories = {
                "Floor Care": {
                    "url": f"{self.base_url}/products?category=floor-care",
                    "discovered_at": datetime.now().isoformat(),
                    "source": "manual_fallback"
                },
                "Kitchen Cleaning": {
                    "url": f"{self.base_url}/products?category=kitchen",
                    "discovered_at": datetime.now().isoformat(),
                    "source": "manual_fallback"
                },
                "Carpet Care": {
                    "url": f"{self.base_url}/products?category=carpet",
                    "discovered_at": datetime.now().isoformat(),
                    "source": "manual_fallback"
                },
                "Bathroom Cleaning": {
                    "url": f"{self.base_url}/products?category=bathroom",
                    "discovered_at": datetime.now().isoformat(),
                    "source": "manual_fallback"
                }
            }
            categories_discovered.update(fallback_categories)
        
        # Save categories to JSON file
        categories_data = {
            "discovery_metadata": {
                "discovered_at": datetime.now().isoformat(),
                "base_url": self.base_url,
                "total_categories": len(categories_discovered),
                "discovery_method": "navigation_analysis"
            },
            "categories": categories_discovered
        }
        
        with open(self.categories_file, 'w', encoding='utf-8') as f:
            json.dump(categories_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Categories saved to: {self.categories_file}")
        
        return {
            "categories_discovered": len(categories_discovered),
            "categories_file": self.categories_file,
            "categories": list(categories_discovered.keys())
        }
    
    def _extract_category_name(self, url: str, category_names: List[str]) -> str:
        """Extract a clean category name from URL or available names."""
        # First try to match with available category names
        for name in category_names:
            if name and len(name.strip()) > 1:
                return name.strip()
        
        # Extract from URL path
        parsed = urlparse(url)
        path_parts = [part for part in parsed.path.split('/') if part]
        
        if path_parts:
            # Take the last meaningful part
            for part in reversed(path_parts):
                if part and part not in ['products', 'categories', 'category']:
                    # Convert URL slug to title case
                    name = part.replace('-', ' ').replace('_', ' ')
                    return ' '.join(word.capitalize() for word in name.split())
        
        # Fallback: use query parameter
        if '=' in parsed.query:
            for param in parsed.query.split('&'):
                if 'category' in param or 'cat' in param:
                    _, value = param.split('=', 1)
                    name = value.replace('-', ' ').replace('_', ' ')
                    return ' '.join(word.capitalize() for word in name.split())
        
        return None
    
    def _is_valid_category_url(self, url: str) -> bool:
        """Check if URL is likely a valid category page."""
        url_lower = url.lower()
        
        # Valid indicators
        valid_indicators = [
            'category', 'categories', 'products', 'cleaning',
            'professional', 'commercial', 'industrial'
        ]
        
        # Invalid indicators
        invalid_indicators = [
            'contact', 'about', 'privacy', 'terms', 'login',
            'register', 'account', 'cart', 'checkout', 'search',
            'mailto:', 'tel:', '#', 'javascript:'
        ]
        
        # Check invalid first
        for invalid in invalid_indicators:
            if invalid in url_lower:
                return False
        
        # Check for valid indicators
        for valid in valid_indicators:
            if valid in url_lower:
                return True
        
        return False


class URLGenerationStep(PipelineStep):
    """Step to generate product URLs for each category."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        super().__init__("url-generation", config, logger)
        self.output_dir = config.get('output_dir', 'pipeline_data')
        self.categories_file = os.path.join(self.output_dir, 'categories.json')
        self.product_urls_file = os.path.join(self.output_dir, 'product_urls.json')
        self.batch_size = config.get('batch_size', 50)
        self.max_products_per_category = config.get('max_products_per_category', 1000)
    
    def check_prerequisites(self) -> tuple[bool, str]:
        """Check if categories file exists."""
        if not os.path.exists(self.categories_file):
            return False, f"Categories file not found: {self.categories_file}. Run category-discovery step first."
        return True, ""
    
    async def _execute_step(self) -> Dict[str, Any]:
        """Generate product URLs from category pages."""
        # Load categories
        with open(self.categories_file, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        categories = categories_data.get('categories', {})
        
        if not categories:
            raise Exception("No categories found in categories file")
        
        self.logger.info(f"🎯 Generating URLs for {len(categories)} categories")
        
        browser_config = BrowserConfig(headless=True, verbose=False)
        crawler_config = CrawlerRunConfig(
            page_timeout=30000,
            word_count_threshold=10,
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=JsonCssExtractionStrategy({
                "name": "product_url_extraction",
                "baseSelector": "body",
                "fields": [
                    {"name": "product_links", "selector": "a[href*='product'], .product-link, .product a", "type": "attribute", "attribute": "href"},
                    {"name": "product_names", "selector": "a[href*='product'], .product-link, .product a", "type": "text"},
                    {"name": "all_product_links", "selector": "a[href]", "type": "attribute", "attribute": "href"},
                    {"name": "pagination_links", "selector": ".pagination a, .pager a, .next, .more", "type": "attribute", "attribute": "href"}
                ]
            }, verbose=False)
        )
        
        all_product_urls = {}
        category_results = {}
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for category_name, category_info in categories.items():
                self.logger.info(f"📋 Processing category: {category_name}")
                
                category_urls = set()
                pages_processed = 0
                
                try:
                    # Start with main category page
                    category_url = category_info['url']
                    pages_to_process = [category_url]
                    processed_pages = set()
                    
                    while pages_to_process and len(category_urls) < self.max_products_per_category:
                        current_page = pages_to_process.pop(0)
                        
                        if current_page in processed_pages:
                            continue
                        
                        processed_pages.add(current_page)
                        pages_processed += 1
                        
                        self.logger.info(f"  📄 Processing page {pages_processed}: {current_page}")
                        
                        result = await crawler.arun(url=current_page, config=crawler_config)
                        
                        if result.success and result.extracted_content:
                            try:
                                page_data = json.loads(result.extracted_content)
                                if isinstance(page_data, list) and len(page_data) > 0:
                                    page_data = page_data[0]
                                
                                # Extract product URLs
                                product_links = page_data.get('product_links', [])
                                all_links = page_data.get('all_product_links', [])
                                pagination_links = page_data.get('pagination_links', [])
                                
                                # Process product links
                                for link in product_links + all_links:
                                    if link and self._is_product_url(link):
                                        full_url = self._make_absolute_url(link, category_info['url'])
                                        category_urls.add(full_url)
                                
                                # Process pagination
                                for pag_link in pagination_links:
                                    if pag_link and self._is_pagination_url(pag_link):
                                        full_pag_url = self._make_absolute_url(pag_link, current_page)
                                        if full_pag_url not in processed_pages and len(pages_to_process) < 10:
                                            pages_to_process.append(full_pag_url)
                                
                                self.logger.info(f"    ✅ Found {len(category_urls)} product URLs so far")
                                
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"    ⚠️  Failed to parse page data: {e}")
                        
                        # Be respectful with requests
                        await asyncio.sleep(1)
                        
                        # Limit pages per category
                        if pages_processed >= 20:
                            self.logger.info(f"    ⚠️  Reached page limit for category {category_name}")
                            break
                    
                    # Store results for this category
                    category_products = []
                    for url in category_urls:
                        category_products.append({
                            "url": url,
                            "category": category_name,
                            "discovered_at": datetime.now().isoformat()
                        })
                    
                    all_product_urls[category_name] = category_products
                    category_results[category_name] = {
                        "total_products": len(category_products),
                        "pages_processed": pages_processed,
                        "category_url": category_url
                    }
                    
                    self.logger.info(f"✅ Category '{category_name}': {len(category_products)} products from {pages_processed} pages")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to process category {category_name}: {e}")
                    category_results[category_name] = {
                        "error": str(e),
                        "total_products": 0,
                        "pages_processed": pages_processed
                    }
        
        # Generate unified URL list (all products regardless of category duplication)
        all_unique_urls = set()
        category_mapping = {}
        
        for category_name, products in all_product_urls.items():
            for product in products:
                url = product['url']
                all_unique_urls.add(url)
                
                # Track which categories each product belongs to
                if url not in category_mapping:
                    category_mapping[url] = []
                category_mapping[url].append(category_name)
        
        # Create final URL data structure
        final_url_data = {
            "generation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_categories": len(categories),
                "total_unique_products": len(all_unique_urls),
                "total_products_with_duplicates": sum(len(products) for products in all_product_urls.values()),
                "generation_method": "category_crawling"
            },
            "category_results": category_results,
            "product_urls_by_category": all_product_urls,
            "all_unique_product_urls": list(all_unique_urls),
            "product_category_mapping": category_mapping
        }
        
        # Save to file
        with open(self.product_urls_file, 'w', encoding='utf-8') as f:
            json.dump(final_url_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Product URLs saved to: {self.product_urls_file}")
        
        return {
            "categories_processed": len(category_results),
            "total_unique_products": len(all_unique_urls),
            "total_products_with_duplicates": sum(len(products) for products in all_product_urls.values()),
            "product_urls_file": self.product_urls_file,
            "category_breakdown": {cat: res.get('total_products', 0) for cat, res in category_results.items()}
        }
    
    def _is_product_url(self, url: str) -> bool:
        """Check if URL is likely a product page."""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Product indicators
        product_indicators = [
            'product', 'item', '/p/', '/products/', 
            'sku=', 'id=', 'pid='
        ]
        
        # Invalid indicators
        invalid_indicators = [
            'contact', 'about', 'privacy', 'terms', 'login',
            'register', 'account', 'cart', 'checkout', 'search',
            'mailto:', 'tel:', '#', 'javascript:', 'category',
            'page=', 'sort=', 'filter='
        ]
        
        # Check invalid first
        for invalid in invalid_indicators:
            if invalid in url_lower:
                return False
        
        # Check for product indicators
        for indicator in product_indicators:
            if indicator in url_lower:
                return True
        
        return False
    
    def _is_pagination_url(self, url: str) -> bool:
        """Check if URL is a pagination link."""
        if not url:
            return False
        
        url_lower = url.lower()
        pagination_indicators = ['page=', 'p=', 'next', 'more', 'continue']
        
        for indicator in pagination_indicators:
            if indicator in url_lower:
                return True
        
        return False
    
    def _make_absolute_url(self, url: str, base_url: str) -> str:
        """Convert relative URL to absolute URL."""
        if not url:
            return url
        
        if url.startswith('http'):
            return url
        
        return urljoin(base_url, url)


class ScrapingStep(PipelineStep):
    """Step to scrape products using universal_scraper.py as the foundation."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        super().__init__("scraping", config, logger)
        self.output_dir = config.get('output_dir', 'pipeline_data')
        self.product_urls_file = os.path.join(self.output_dir, 'product_urls.json')
        self.scraping_output_dir = os.path.join(self.output_dir, 'scraped_products')
        self.batch_size = config.get('batch_size', 10)
        self.selected_categories = config.get('selected_categories', [])
        self.scraping_mode = config.get('scraping_mode', 'enhanced')
        self.delay = config.get('delay', 2.0)
        self.limit = config.get('limit', None)
    
    def check_prerequisites(self) -> tuple[bool, str]:
        """Check if product URLs file exists."""
        if not os.path.exists(self.product_urls_file):
            return False, f"Product URLs file not found: {self.product_urls_file}. Run url-generation step first."
        return True, ""
    
    async def _execute_step(self) -> Dict[str, Any]:
        """Execute scraping using universal_scraper.py for each category."""
        # Load product URLs
        with open(self.product_urls_file, 'r', encoding='utf-8') as f:
            url_data = json.load(f)
        
        product_urls_by_category = url_data.get('product_urls_by_category', {})
        
        if not product_urls_by_category:
            raise Exception("No product URLs found in URLs file")
        
        # Filter categories if specified
        if self.selected_categories:
            filtered_categories = {}
            for cat_name in self.selected_categories:
                if cat_name in product_urls_by_category:
                    filtered_categories[cat_name] = product_urls_by_category[cat_name]
                else:
                    self.logger.warning(f"⚠️  Selected category '{cat_name}' not found")
            product_urls_by_category = filtered_categories
        
        if not product_urls_by_category:
            raise Exception("No valid categories to process")
        
        os.makedirs(self.scraping_output_dir, exist_ok=True)
        
        self.logger.info(f"🎯 Starting scraping for {len(product_urls_by_category)} categories")
        
        category_results = {}
        total_products_scraped = 0
        
        # Process each category
        for category_name, products in product_urls_by_category.items():
            self.logger.info(f"📋 Processing category: {category_name} ({len(products)} products)")
            
            # Create category output directory
            category_output_dir = os.path.join(self.scraping_output_dir, self._sanitize_filename(category_name))
            os.makedirs(category_output_dir, exist_ok=True)
            
            # Prepare URLs for universal scraper
            category_urls = [product['url'] for product in products]
            
            # Apply limit if specified
            if self.limit:
                remaining_limit = self.limit - total_products_scraped
                if remaining_limit <= 0:
                    self.logger.info(f"⚠️  Reached overall limit, skipping category {category_name}")
                    break
                category_urls = category_urls[:remaining_limit]
            
            # Create temporary URLs file for this category
            temp_urls_file = os.path.join(category_output_dir, 'category_urls.json')
            with open(temp_urls_file, 'w', encoding='utf-8') as f:
                json.dump(category_urls, f, indent=2)
            
            # Configure universal scraper for this category
            scraper_config = {
                'mode': self.scraping_mode,
                'urls_file': temp_urls_file,
                'batch_size': self.batch_size,
                'output_dir': category_output_dir,
                'delay': self.delay,
                'limit': len(category_urls),
                'content_exclusion': self.config.get('content_exclusion', True),
                'format': 'json',
                'verbose': True
            }
            
            try:
                # Initialize and run universal scraper
                scraper = UniversalScraper(scraper_config)
                results = await scraper.run_scraping()
                
                # Process results
                products_scraped = results['scraping_metadata'].get('total_products_extracted', 0)
                products_failed = results['scraping_metadata'].get('total_failed', 0)
                
                category_results[category_name] = {
                    "products_attempted": len(category_urls),
                    "products_scraped": products_scraped,
                    "products_failed": products_failed,
                    "success_rate": f"{(products_scraped / len(category_urls)) * 100:.1f}%" if category_urls else "0%",
                    "output_directory": category_output_dir,
                    "processing_time": results['scraping_metadata'].get('total_processing_time_seconds', 0)
                }
                
                total_products_scraped += products_scraped
                
                self.logger.info(f"✅ Category '{category_name}': {products_scraped}/{len(category_urls)} products scraped")
                
                # Clean up temporary file
                os.remove(temp_urls_file)
                
            except Exception as e:
                self.logger.error(f"❌ Failed to scrape category {category_name}: {e}")
                category_results[category_name] = {
                    "products_attempted": len(category_urls),
                    "products_scraped": 0,
                    "products_failed": len(category_urls),
                    "error": str(e),
                    "output_directory": category_output_dir
                }
        
        return {
            "categories_processed": len(category_results),
            "total_products_scraped": total_products_scraped,
            "scraping_output_dir": self.scraping_output_dir,
            "category_results": category_results
        }
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for use in file system."""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
        sanitized = sanitized.strip('_.')  # Remove leading/trailing underscores and dots
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = 'unknown_category'
        
        return sanitized


class ValidationStep(PipelineStep):
    """Step to validate scraped products using the validation system."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        super().__init__("validation", config, logger)
        self.output_dir = config.get('output_dir', 'pipeline_data')
        self.scraping_output_dir = os.path.join(self.output_dir, 'scraped_products')
        self.validation_output_dir = os.path.join(self.output_dir, 'validation_reports')
    
    def check_prerequisites(self) -> tuple[bool, str]:
        """Check if scraping output directory exists."""
        if not os.path.exists(self.scraping_output_dir):
            return False, f"Scraping output directory not found: {self.scraping_output_dir}. Run scraping step first."
        return True, ""
    
    async def _execute_step(self) -> Dict[str, Any]:
        """Validate scraped products using validation system."""
        if not AgarValidationSystem:
            self.logger.warning("⚠️  Validation system not available, skipping validation")
            return {"validation_skipped": True, "reason": "Validation system not available"}
        
        os.makedirs(self.validation_output_dir, exist_ok=True)
        
        # Initialize validation system
        validator = AgarValidationSystem(
            output_dir=self.validation_output_dir,
            verbose=True
        )
        
        validation_results = {}
        total_products_validated = 0
        total_quality_score = 0
        
        # Process each category directory
        for category_dir in os.listdir(self.scraping_output_dir):
            category_path = os.path.join(self.scraping_output_dir, category_dir)
            
            if not os.path.isdir(category_path):
                continue
                
            self.logger.info(f"🔍 Validating category: {category_dir}")
            
            category_products = []
            category_quality_scores = []
            
            # Find all product JSON files in category
            for filename in os.listdir(category_path):
                if filename.endswith('.json') and not filename.startswith('universal_scraping_results'):
                    product_file = os.path.join(category_path, filename)
                    
                    try:
                        with open(product_file, 'r', encoding='utf-8') as f:
                            product_data = json.load(f)
                        
                        # Validate product
                        validation_result = validator.validate_product(product_data)
                        
                        category_products.append({
                            "filename": filename,
                            "product_name": product_data.get('product_name', 'Unknown'),
                            "url": product_data.get('url', ''),
                            "quality_score": validation_result.get('quality_score', 0),
                            "missing_fields": validation_result.get('missing_required_fields', []),
                            "validation_passed": validation_result.get('validation_passed', False)
                        })
                        
                        category_quality_scores.append(validation_result.get('quality_score', 0))
                        total_products_validated += 1
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to validate {filename}: {e}")
                        category_products.append({
                            "filename": filename,
                            "error": str(e),
                            "quality_score": 0,
                            "validation_passed": False
                        })
            
            # Calculate category statistics
            if category_quality_scores:
                avg_quality = sum(category_quality_scores) / len(category_quality_scores)
                total_quality_score += sum(category_quality_scores)
                passed_validation = sum(1 for p in category_products if p.get('validation_passed', False))
            else:
                avg_quality = 0
                passed_validation = 0
            
            validation_results[category_dir] = {
                "total_products": len(category_products),
                "passed_validation": passed_validation,
                "average_quality_score": avg_quality,
                "validation_rate": f"{(passed_validation / len(category_products)) * 100:.1f}%" if category_products else "0%",
                "products": category_products
            }
            
            self.logger.info(f"✅ Category '{category_dir}': {passed_validation}/{len(category_products)} products passed validation (avg quality: {avg_quality:.1f}%)")
        
        # Generate overall validation report
        overall_avg_quality = total_quality_score / total_products_validated if total_products_validated > 0 else 0
        total_passed = sum(result['passed_validation'] for result in validation_results.values())
        
        validation_report = {
            "validation_metadata": {
                "validated_at": datetime.now().isoformat(),
                "total_products_validated": total_products_validated,
                "total_passed_validation": total_passed,
                "overall_validation_rate": f"{(total_passed / total_products_validated) * 100:.1f}%" if total_products_validated > 0 else "0%",
                "overall_average_quality_score": overall_avg_quality,
                "categories_processed": len(validation_results)
            },
            "category_results": validation_results
        }
        
        # Save validation report
        report_file = os.path.join(self.validation_output_dir, f'validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(validation_report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Validation report saved to: {report_file}")
        
        return {
            "total_products_validated": total_products_validated,
            "total_passed_validation": total_passed,
            "overall_validation_rate": f"{(total_passed / total_products_validated) * 100:.1f}%" if total_products_validated > 0 else "0%",
            "overall_average_quality_score": overall_avg_quality,
            "validation_output_dir": self.validation_output_dir,
            "validation_report_file": report_file
        }


class ProcessingPipeline:
    """Main processing pipeline orchestrator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize processing pipeline."""
        self.config = config
        self.output_dir = config.get('output_dir', 'pipeline_data')
        self.steps_to_run = config.get('steps', ['all'])
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Available steps
        self.available_steps = {
            'category-discovery': CategoryDiscoveryStep,
            'url-generation': URLGenerationStep,
            'scraping': ScrapingStep,
            'validation': ValidationStep
        }
        
        # Step execution order (for 'all')
        self.step_order = ['category-discovery', 'url-generation', 'scraping', 'validation']
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.output_dir, f'pipeline_log_{timestamp}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger('ProcessingPipeline')
        logger.info(f"Pipeline logging initialized - Log file: {log_file}")
        return logger
    
    async def run_pipeline(self) -> Dict[str, Any]:
        """Run the processing pipeline."""
        pipeline_start = datetime.now()
        
        self.logger.info("🚀 AGAR PROCESSING PIPELINE STARTED")
        self.logger.info("=" * 70)
        self.logger.info(f"📁 Output directory: {self.output_dir}")
        self.logger.info(f"🎯 Steps to run: {', '.join(self.steps_to_run)}")
        
        # Determine which steps to execute
        if 'all' in self.steps_to_run:
            steps_to_execute = self.step_order
        else:
            steps_to_execute = [step for step in self.steps_to_run if step in self.available_steps]
        
        if not steps_to_execute:
            raise Exception(f"No valid steps specified. Available steps: {list(self.available_steps.keys())}")
        
        self.logger.info(f"📋 Executing steps: {', '.join(steps_to_execute)}")
        
        # Execute steps
        step_results = {}
        
        for step_name in steps_to_execute:
            self.logger.info(f"\n{'='*20} STEP: {step_name.upper()} {'='*20}")
            
            try:
                step_class = self.available_steps[step_name]
                step = step_class(self.config, self.logger)
                
                result = await step.execute()
                step_results[step_name] = result
                
                if not result['success']:
                    self.logger.error(f"❌ Step '{step_name}' failed, stopping pipeline")
                    break
                    
            except Exception as e:
                self.logger.error(f"❌ Fatal error in step '{step_name}': {e}")
                step_results[step_name] = {
                    "step": step_name,
                    "success": False,
                    "error": str(e),
                    "fatal": True
                }
                break
        
        # Compile final results
        pipeline_end = datetime.now()
        total_duration = (pipeline_end - pipeline_start).total_seconds()
        
        final_results = {
            "pipeline_metadata": {
                "pipeline_version": "Agar Processing Pipeline v1.0",
                "start_time": pipeline_start.isoformat(),
                "end_time": pipeline_end.isoformat(),
                "total_duration_seconds": total_duration,
                "output_directory": self.output_dir,
                "steps_requested": self.steps_to_run,
                "steps_executed": list(step_results.keys()),
                "all_steps_successful": all(result.get('success', False) for result in step_results.values())
            },
            "step_results": step_results
        }
        
        # Save pipeline results
        results_file = os.path.join(self.output_dir, f'pipeline_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Log final summary
        self.logger.info(f"\n{'='*70}")
        self.logger.info("🏁 PIPELINE EXECUTION COMPLETE")
        self.logger.info(f"⏱️  Total duration: {total_duration/60:.1f} minutes")
        self.logger.info(f"✅ Successful steps: {sum(1 for result in step_results.values() if result.get('success', False))}")
        self.logger.info(f"❌ Failed steps: {sum(1 for result in step_results.values() if not result.get('success', False))}")
        self.logger.info(f"💾 Results saved to: {results_file}")
        
        # Print step-by-step summary
        for step_name, result in step_results.items():
            status = "✅" if result.get('success', False) else "❌"
            duration = result.get('duration_seconds', 0)
            self.logger.info(f"  {status} {step_name}: {duration:.1f}s")
        
        return final_results


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file."""
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                return yaml.safe_load(f) or {}
            elif config_path.endswith('.json'):
                return json.load(f)
    except Exception as e:
        print(f"⚠️  Error loading config file {config_path}: {e}")
    
    return {}


def create_sample_config():
    """Create a sample pipeline configuration file."""
    sample_config = {
        "# Agar Processing Pipeline Configuration": None,
        "base_url": "https://agar.com.au",
        "output_dir": "pipeline_data",
        "steps": ["all"],  # or specify: ["category-discovery", "url-generation", "scraping", "validation"]
        "# Category Discovery Settings": None,
        "category_discovery": {
            "max_categories": 50
        },
        "# URL Generation Settings": None,
        "url_generation": {
            "batch_size": 50,
            "max_products_per_category": 1000,
            "max_pages_per_category": 20
        },
        "# Scraping Settings": None,
        "scraping": {
            "scraping_mode": "enhanced",  # enhanced, simple, llm, api
            "batch_size": 10,
            "delay": 2.0,
            "limit": None,  # overall limit across all categories
            "content_exclusion": True,
            "selected_categories": []  # empty = all categories, or specify: ["Floor Care", "Kitchen Cleaning"]
        },
        "# Validation Settings": None,
        "validation": {
            "enabled": True,
            "generate_reports": True
        }
    }
    
    config_file = 'pipeline_config.yaml'
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2, allow_unicode=True)
    
    print(f"✅ Sample pipeline configuration saved to {config_file}")


async def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Agar Processing Pipeline - Comprehensive parameterized pipeline for Crawl4AI scraping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --step all --config pipeline_config.yaml
  %(prog)s --step category-discovery url-generation --output-dir my_pipeline_data
  %(prog)s --step scraping --categories "Floor Care,Kitchen Cleaning" --batch-size 5
  %(prog)s --step validation --config pipeline_config.yaml
  %(prog)s --create-config
        """
    )
    
    # Configuration options
    parser.add_argument('--config', '-c', help='Configuration file (YAML or JSON)')
    parser.add_argument('--create-config', action='store_true', help='Create sample configuration file')
    
    # Pipeline options
    parser.add_argument('--step', '--steps', nargs='+', 
                       choices=['all', 'category-discovery', 'url-generation', 'scraping', 'validation'],
                       default=['all'], help='Pipeline steps to run')
    parser.add_argument('--output-dir', default='pipeline_data', 
                       help='Output directory for pipeline data')
    
    # Step-specific options
    parser.add_argument('--base-url', default='https://agar.com.au', 
                       help='Base URL for Agar website')
    parser.add_argument('--batch-size', type=int, default=10, 
                       help='Batch size for processing')
    parser.add_argument('--categories', help='Comma-separated list of categories to process')
    parser.add_argument('--scraping-mode', choices=['simple', 'enhanced', 'llm', 'api'],
                       default='enhanced', help='Scraping mode for universal scraper')
    parser.add_argument('--delay', type=float, default=2.0, 
                       help='Delay between requests (seconds)')
    parser.add_argument('--limit', type=int, help='Overall limit of products to process')
    
    args = parser.parse_args()
    
    # Handle special cases
    if args.create_config:
        create_sample_config()
        return
    
    # Build configuration
    config = {
        'base_url': args.base_url,
        'output_dir': args.output_dir,
        'steps': args.step,
        'batch_size': args.batch_size,
        'scraping_mode': args.scraping_mode,
        'delay': args.delay,
        'limit': args.limit,
        'content_exclusion': True
    }
    
    # Load from config file if provided
    if args.config:
        file_config = load_config_file(args.config)
        # Merge configs, with CLI args taking precedence
        config = {**file_config, **{k: v for k, v in config.items() if v is not None}}
    
    # Handle categories
    if args.categories:
        config['selected_categories'] = [cat.strip() for cat in args.categories.split(',')]
    
    # Initialize and run pipeline
    try:
        pipeline = ProcessingPipeline(config)
        results = await pipeline.run_pipeline()
        
        print(f"\n🏁 Processing pipeline completed!")
        print(f"📂 Check output directory: {config['output_dir']}")
        
        if results['pipeline_metadata']['all_steps_successful']:
            print("✅ All steps completed successfully!")
        else:
            print("⚠️  Some steps failed - check logs for details")
        
    except Exception as e:
        print(f"❌ Error during pipeline execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🌐 Agar Processing Pipeline v1.0")
    print("Comprehensive parameterized pipeline for Crawl4AI scraping")
    print("=" * 80)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
