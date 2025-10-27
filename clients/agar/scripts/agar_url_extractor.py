#!/usr/bin/env python3
"""
Agar URL Extractor
Focused tool for building comprehensive Agar product URL extraction files.

This tool extracts the category discovery and URL generation components from the 
full processing pipeline to create a streamlined solution specifically for 
building product URL files that can be consumed by other scraping tools.

Key Features:
- Discovers product categories from Agar website navigation
- Generates comprehensive product URL lists with category associations  
- Handles pagination automatically
- Outputs clean JSON files ready for consumption by scraping systems
- Configurable batch sizes, limits, and processing parameters

Usage:
    python agar_url_extractor.py --output-dir agar_urls
    python agar_url_extractor.py --config url_extraction_config.yaml --max-products 500
    python agar_url_extractor.py --base-url https://agar.com.au --batch-size 25 --verbose
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

# Crawl4AI imports
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai import JsonCssExtractionStrategy
except ImportError:
    print("❌ Error: Cannot import crawl4ai. Please install crawl4ai first.")
    sys.exit(1)


class AgarCategoryDiscovery:
    """Discovers product categories from Agar website navigation."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.base_url = config.get('base_url', 'https://agar.com.au')
        self.output_dir = config.get('output_dir', 'agar_url_data')
        self.max_categories = config.get('max_categories', 50)
        self.categories_file = os.path.join(self.output_dir, 'categories.json')
    
    async def discover_categories(self) -> Dict[str, Any]:
        """Discover categories dynamically from Agar website Products navigation using raw HTML parsing."""
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.logger.info(f"🔍 Dynamically discovering categories from Products navigation: {self.base_url}")
        
        # Since JsonCssExtractionStrategy has issues, let's extract raw HTML and parse it manually
        browser_config = BrowserConfig(headless=True, verbose=False)
        crawler_config = CrawlerRunConfig(
            page_timeout=30000,
            word_count_threshold=10,
            cache_mode=CacheMode.BYPASS,
            # No extraction strategy - we'll get raw HTML
        )
        
        categories_discovered = {}
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Extract raw HTML from homepage
            result = await crawler.arun(url=self.base_url, config=crawler_config)
            
            if result.success and result.html:
                try:
                    import re
                    html_content = result.html
                    
                    self.logger.info("📊 Parsing raw HTML for Products navigation...")
                    
                    # Find ALL product category links from the entire Products navigation
                    # Look for the complete Products dropdown menu structure
                    self.logger.info("📊 Searching for complete Products navigation structure...")
                    
                    # Extract the entire Products dropdown menu section
                    # Look for the main Products dropdown container
                    navigation_pattern = r'<ul[^>]*aria-labelledby=["\']menu-item-dropdown-1652["\'][^>]*>(.*?)</ul>'
                    navigation_match = re.search(navigation_pattern, html_content, re.DOTALL | re.IGNORECASE)
                    
                    if navigation_match:
                        navigation_html = navigation_match.group(1)
                        self.logger.info(f"Found Products dropdown navigation section ({len(navigation_html)} chars)")
                        
                        # Extract ALL dropdown-item links with comprehensive pattern
                        # This pattern captures both main categories and subcategories
                        comprehensive_pattern = r'<a[^>]*href=["\']([^"\']+product-category[^"\']*)["\'][^>]*class=["\'][^"\']*dropdown-item[^"\']*["\'][^>]*>([^<]+)</a>'
                        
                        # Find all matches
                        all_links = re.findall(comprehensive_pattern, navigation_html, re.IGNORECASE)
                        self.logger.info(f"Found {len(all_links)} category links using comprehensive pattern")
                        
                        # Also try alternate pattern with href after class
                        if len(all_links) < 20:  # If we didn't get enough categories
                            alt_pattern = r'<a[^>]*class=["\'][^"\']*dropdown-item[^"\']*["\'][^>]*href=["\']([^"\']+product-category[^"\']*)["\'][^>]*>([^<]+)</a>'
                            alt_links = re.findall(alt_pattern, navigation_html, re.IGNORECASE)
                            self.logger.info(f"Alternate pattern found {len(alt_links)} additional links")
                            
                            # Combine results, avoiding duplicates
                            seen_urls = set(link[0] for link in all_links)
                            for href, name in alt_links:
                                if href not in seen_urls:
                                    all_links.append((href, name))
                                    seen_urls.add(href)
                        
                        # If still not enough, try a more aggressive approach
                        if len(all_links) < 20:
                            # Extract from the entire HTML content, not just the dropdown
                            self.logger.info("Using aggressive extraction from entire page content...")
                            broad_pattern = r'<a[^>]*href=["\']([^"\']+/product-category/[^"\']*)["\'][^>]*>([^<]+)</a>'
                            broad_links = re.findall(broad_pattern, html_content, re.IGNORECASE)
                            
                            # Filter and deduplicate
                            seen_urls = set(link[0] for link in all_links)
                            for href, name in broad_links:
                                # Basic filtering for valid category links
                                if (href not in seen_urls and 
                                    'product-category' in href and 
                                    not any(invalid in href.lower() for invalid in ['contact', 'about', 'search', 'cart'])):
                                    all_links.append((href, name))
                                    seen_urls.add(href)
                            
                            self.logger.info(f"Broad extraction added {len(broad_links)} potential links, total now: {len(all_links)}")
                        
                        links = all_links
                        self.logger.info(f"Final extraction: {len(links)} category links found")
                        
                        # Debug: show sample of extracted links
                        if links:
                            self.logger.debug(f"Sample extracted links: {links[:3]}")
                        
                        for href, name in links:
                            # Check if this is a product category link
                            if 'product-category' in href:
                                # Clean up the name (decode HTML entities)
                                import html
                                clean_name = html.unescape(name.strip())
                                
                                # Convert to absolute URL if needed
                                if href.startswith('/'):
                                    full_url = urljoin(self.base_url, href)
                                elif href.startswith('http'):
                                    full_url = href
                                else:
                                    continue
                                
                                if clean_name and len(clean_name) > 1:
                                    categories_discovered[clean_name] = {
                                        "url": full_url,
                                        "discovered_at": datetime.now().isoformat(),
                                        "source": "dynamic_navigation_regex"
                                    }
                                    self.logger.debug(f"✅ Added category: {clean_name} -> {full_url}")
                        
                        self.logger.info(f"✅ Dynamically extracted {len(categories_discovered)} categories from navigation")
                    else:
                        self.logger.error("Could not find Products dropdown navigation in HTML")
                        # Debug: show a sample of the HTML around menu items
                        menu_sample = re.search(r'menu-item-dropdown-1652.*?{0,500}', html_content, re.DOTALL | re.IGNORECASE)
                        if menu_sample:
                            self.logger.debug(f"HTML around menu-item-dropdown-1652: {menu_sample.group()[:300]}...")
                    
                except Exception as e:
                    self.logger.error(f"Failed to parse HTML navigation: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                self.logger.error("Failed to get HTML content from homepage")
            
        # If no categories discovered from navigation, this is a FAILURE
        if not categories_discovered:
            self.logger.error("❌ CATEGORY DISCOVERY FAILED - NO categories found from navigation")
            self.logger.error("This indicates the CSS selectors or filtering logic is not working correctly")
            raise Exception("Category discovery failed - no categories extracted from navigation. Fix the CSS selectors or filtering logic.")
        
        # Limit categories if specified
        if self.max_categories and len(categories_discovered) > self.max_categories:
            self.logger.info(f"⚠️  Limiting to {self.max_categories} categories")
            categories_discovered = dict(list(categories_discovered.items())[:self.max_categories])
        
        # Save categories data
        categories_data = {
            "discovery_metadata": {
                "discovered_at": datetime.now().isoformat(),
                "base_url": self.base_url,
                "total_categories": len(categories_discovered),
                "discovery_method": "navigation_analysis",
                "tool_version": "Agar URL Extractor v1.0"
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
        """Extract clean category name from URL or available names."""
        # Try to match with available category names first
        for name in category_names:
            if name and len(name.strip()) > 1:
                return name.strip()
        
        # Extract from URL path
        parsed = urlparse(url)
        path_parts = [part for part in parsed.path.split('/') if part]
        
        if path_parts:
            for part in reversed(path_parts):
                if part and part not in ['products', 'categories', 'category']:
                    # Convert URL slug to title case
                    name = part.replace('-', ' ').replace('_', ' ')
                    return ' '.join(word.capitalize() for word in name.split())
        
        # Try query parameter
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
        
        valid_indicators = [
            'category', 'categories', 'products', 'cleaning',
            'professional', 'commercial', 'industrial'
        ]
        
        invalid_indicators = [
            'contact', 'about', 'privacy', 'terms', 'login',
            'register', 'account', 'cart', 'checkout', 'search',
            'mailto:', 'tel:', '#', 'javascript:'
        ]
        
        # Check invalid indicators first
        for invalid in invalid_indicators:
            if invalid in url_lower:
                return False
        
        # Check for valid indicators
        for valid in valid_indicators:
            if valid in url_lower:
                return True
        
        return False


class AgarURLGeneration:
    """Generates product URLs from discovered categories with pagination handling."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.output_dir = config.get('output_dir', 'agar_url_data')
        self.categories_file = os.path.join(self.output_dir, 'categories.json')
        self.product_urls_file = os.path.join(self.output_dir, 'product_urls.json')
        self.batch_size = config.get('batch_size', 50)
        self.max_products_per_category = config.get('max_products_per_category', 1000)
        self.max_pages_per_category = config.get('max_pages_per_category', 20)
        self.delay = config.get('delay', 1.0)
    
    def check_prerequisites(self) -> tuple[bool, str]:
        """Check if categories file exists."""
        if not os.path.exists(self.categories_file):
            return False, f"Categories file not found: {self.categories_file}. Run category discovery first."
        return True, ""
    
    async def generate_product_urls(self) -> Dict[str, Any]:
        """Generate product URLs from category pages with pagination handling."""
        # Check prerequisites
        prereq_ok, prereq_msg = self.check_prerequisites()
        if not prereq_ok:
            raise Exception(prereq_msg)
        
        # Load categories
        with open(self.categories_file, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        categories = categories_data.get('categories', {})
        
        if not categories:
            raise Exception("No categories found in categories file")
        
        self.logger.info(f"🎯 Generating URLs for {len(categories)} categories")
        
        browser_config = BrowserConfig(headless=True, verbose=False)
        
        # Use raw HTML extraction since JsonCssExtractionStrategy has issues with multiple matches
        crawler_config = CrawlerRunConfig(
            page_timeout=30000,
            word_count_threshold=10,
            cache_mode=CacheMode.BYPASS,
            # No extraction strategy - we'll parse HTML manually to avoid JsonCssExtractionStrategy bugs
        )
        
        all_product_urls = {}
        category_results = {}
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for category_name, category_info in categories.items():
                self.logger.info(f"📋 Processing category: {category_name}")
                
                category_urls = set()
                pages_processed = 0
                
                try:
                    # Process category with pagination
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
                        
                        if result.success and result.html:
                            try:
                                # Parse HTML directly to avoid JsonCssExtractionStrategy bugs
                                html_content = result.html
                                
                                # Extract ALL product links from the HTML using regex
                                # Pattern matches: <a href="product-url" class="woocommerce-LoopProduct-link ...">
                                product_pattern = r'<a[^>]*href=["\']([^"\']*product[^"\']*)["\'][^>]*class=["\'][^"\']*woocommerce-LoopProduct-link[^"\']*["\']'
                                product_matches = re.findall(product_pattern, html_content, re.IGNORECASE)
                                
                                self.logger.debug(f"    Raw regex found {len(product_matches)} product links")
                                
                                # Process ALL product links found
                                for link in product_matches:
                                    if link and self._is_product_url(link):
                                        full_url = self._make_absolute_url(link, current_page)
                                        category_urls.add(full_url)
                                        self.logger.debug(f"      Added product: {full_url}")
                                
                                # Extract pagination links
                                pagination_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*class=["\'][^"\']*(?:pagination|pager|next|more)[^"\']*["\']'
                                pagination_matches = re.findall(pagination_pattern, html_content, re.IGNORECASE)
                                
                                # Also look for simple pagination patterns
                                simple_pagination_pattern = r'<a[^>]*href=["\']([^"\']*page[^"\']*)["\']'
                                simple_pagination_matches = re.findall(simple_pagination_pattern, html_content, re.IGNORECASE)
                                pagination_matches.extend(simple_pagination_matches)
                                
                                # Handle pagination
                                for pag_link in pagination_matches:
                                    if pag_link and self._is_pagination_url(pag_link):
                                        full_pag_url = self._make_absolute_url(pag_link, current_page)
                                        if (full_pag_url not in processed_pages and 
                                            len(pages_to_process) < 10 and 
                                            pages_processed < self.max_pages_per_category):
                                            pages_to_process.append(full_pag_url)
                                            self.logger.debug(f"      Added pagination: {full_pag_url}")
                                
                                self.logger.info(f"    ✅ Found {len(category_urls)} product URLs so far (added {len(product_matches)} from this page)")
                                
                            except Exception as e:
                                self.logger.warning(f"    ⚠️  Failed to parse HTML: {e}")
                        
                        # Respectful delay
                        await asyncio.sleep(self.delay)
                        
                        # Prevent infinite pagination
                        if pages_processed >= self.max_pages_per_category:
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
        
        # Create unified URL structure
        all_unique_urls = set()
        category_mapping = {}
        
        for category_name, products in all_product_urls.items():
            for product in products:
                url = product['url']
                all_unique_urls.add(url)
                
                # Track category associations
                if url not in category_mapping:
                    category_mapping[url] = []
                category_mapping[url].append(category_name)
        
        # Final URL data structure
        final_url_data = {
            "generation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_categories": len(categories),
                "total_unique_products": len(all_unique_urls),
                "total_products_with_duplicates": sum(len(products) for products in all_product_urls.values()),
                "generation_method": "category_crawling_with_pagination",
                "tool_version": "Agar URL Extractor v1.0"
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
        
        product_indicators = [
            'product', 'item', '/p/', '/products/', 
            'sku=', 'id=', 'pid='
        ]
        
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
        if not url or url.startswith('http'):
            return url
        
        return urljoin(base_url, url)


class AgarURLExtractor:
    """Main Agar URL Extractor orchestrator with organized run structure."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_output_dir = 'output'  # Fixed base directory as requested
        self.verbose = config.get('verbose', False)
        
        # Create run-specific directory structure
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"run_{self.run_timestamp}"
        self.run_dir = os.path.join(self.base_output_dir, self.run_id)
        
        # Create organized directory structure
        self.logs_dir = os.path.join(self.run_dir, 'logs')
        self.metadata_dir = os.path.join(self.run_dir, 'metadata')
        
        # Ensure all directories exist
        os.makedirs(self.run_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Update config with run-specific output directory
        self.run_config = config.copy()
        self.run_config['output_dir'] = self.run_dir
        
        # Setup logging with organized structure
        self.logger = self._setup_logging()
        
        # Save run configuration
        self._save_run_metadata()
        
        # Initialize components with run-specific config
        self.category_discovery = AgarCategoryDiscovery(self.run_config, self.logger)
        self.url_generation = AgarURLGeneration(self.run_config, self.logger)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration with organized structure."""
        log_file = os.path.join(self.logs_dir, 'url_extraction.log')
        
        log_level = logging.DEBUG if self.verbose else logging.INFO
        
        # Clear any existing handlers to avoid conflicts
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger('AgarURLExtractor')
        logger.info(f"URL Extractor logging initialized - Log file: {log_file}")
        logger.info(f"Run ID: {self.run_id}")
        logger.info(f"Run directory: {self.run_dir}")
        return logger
    
    def _save_run_metadata(self):
        """Save run configuration and metadata."""
        run_metadata = {
            "run_info": {
                "run_id": self.run_id,
                "run_timestamp": self.run_timestamp,
                "start_time": datetime.now().isoformat(),
                "tool_version": "Agar URL Extractor v1.1",
                "run_directory": self.run_dir,
                "base_output_directory": self.base_output_dir
            },
            "configuration": self.config,
            "directory_structure": {
                "run_dir": self.run_dir,
                "logs_dir": self.logs_dir,
                "metadata_dir": self.metadata_dir,
                "categories_file": os.path.join(self.run_dir, 'categories.json'),
                "product_urls_file": os.path.join(self.run_dir, 'product_urls.json'),
                "extraction_results_file": os.path.join(self.run_dir, 'extraction_results.json'),
                "log_file": os.path.join(self.logs_dir, 'url_extraction.log')
            }
        }
        
        metadata_file = os.path.join(self.metadata_dir, 'run_config.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(run_metadata, f, indent=2, ensure_ascii=False)
    
    def _update_run_completion_metadata(self, results: Dict[str, Any]):
        """Update run metadata with completion information."""
        completion_metadata = {
            "completion_info": {
                "completed_at": datetime.now().isoformat(),
                "extraction_successful": results['extraction_metadata']['extraction_successful'],
                "run_id": self.run_id,
                "summary": results.get('summary', {})
            },
            "file_outputs": {
                "categories_file": os.path.join(self.run_dir, 'categories.json'),
                "product_urls_file": os.path.join(self.run_dir, 'product_urls.json'),
                "extraction_results_file": os.path.join(self.run_dir, 'extraction_results.json'),
                "log_file": os.path.join(self.logs_dir, 'url_extraction.log'),
                "run_metadata_file": os.path.join(self.metadata_dir, 'run_config.json')
            },
            "performance_metrics": {
                "total_duration_seconds": results['extraction_metadata']['total_duration_seconds'],
                "categories_discovered": results['summary']['categories_discovered'],
                "unique_products_found": results['summary']['total_unique_products'],
                "total_products_with_duplicates": results['summary']['total_products_with_duplicates']
            }
        }
        
        completion_file = os.path.join(self.metadata_dir, 'run_completion.json')
        with open(completion_file, 'w', encoding='utf-8') as f:
            json.dump(completion_metadata, f, indent=2, ensure_ascii=False)
    
    async def run_extraction(self) -> Dict[str, Any]:
        """Run the complete URL extraction process."""
        extraction_start = datetime.now()
        
        self.logger.info("🌐 AGAR URL EXTRACTOR STARTED")
        self.logger.info("=" * 60)
        self.logger.info(f"📁 Run directory: {self.run_dir}")
        self.logger.info(f"📁 Base output directory: {self.base_output_dir}")
        self.logger.info(f"🎯 Base URL: {self.config.get('base_url', 'https://agar.com.au')}")
        
        results = {}
        
        try:
            # Step 1: Discover Categories
            self.logger.info(f"\n{'='*15} CATEGORY DISCOVERY {'='*15}")
            category_result = await self.category_discovery.discover_categories()
            results['category_discovery'] = category_result
            
            # Step 2: Generate Product URLs
            self.logger.info(f"\n{'='*15} URL GENERATION {'='*15}")
            url_result = await self.url_generation.generate_product_urls()
            results['url_generation'] = url_result
            
            # Final summary
            extraction_end = datetime.now()
            total_duration = (extraction_end - extraction_start).total_seconds()
            
            final_results = {
                "extraction_metadata": {
                    "tool_version": "Agar URL Extractor v1.1",
                    "run_id": self.run_id,
                    "start_time": extraction_start.isoformat(),
                    "end_time": extraction_end.isoformat(),
                    "total_duration_seconds": total_duration,
                    "base_output_directory": self.base_output_dir,
                    "run_directory": self.run_dir,
                    "extraction_successful": True
                },
                "results": results,
                "summary": {
                    "categories_discovered": category_result.get('categories_discovered', 0),
                    "total_unique_products": url_result.get('total_unique_products', 0),
                    "total_products_with_duplicates": url_result.get('total_products_with_duplicates', 0),
                    "categories_processed": url_result.get('categories_processed', 0),
                    "product_urls_file": url_result.get('product_urls_file', ''),
                    "categories_file": category_result.get('categories_file', '')
                }
            }
            
            # Save extraction results in run directory
            results_file = os.path.join(self.run_dir, 'extraction_results.json')
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(final_results, f, indent=2, ensure_ascii=False)
            
            # Update run metadata with completion info
            self._update_run_completion_metadata(final_results)
            
            # Log final summary
            self.logger.info(f"\n{'='*60}")
            self.logger.info("🏁 URL EXTRACTION COMPLETE")
            self.logger.info(f"🆔 Run ID: {self.run_id}")
            self.logger.info(f"📁 Run directory: {self.run_dir}")
            self.logger.info(f"⏱️  Total duration: {total_duration/60:.1f} minutes")
            self.logger.info(f"📂 Categories discovered: {category_result.get('categories_discovered', 0)}")
            self.logger.info(f"🔗 Unique product URLs: {url_result.get('total_unique_products', 0)}")
            self.logger.info(f"📄 Results saved to: {results_file}")
            self.logger.info(f"📋 Logs available in: {self.logs_dir}")
            self.logger.info(f"⚙️  Metadata available in: {self.metadata_dir}")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"❌ Error during URL extraction: {e}")
            
            extraction_end = datetime.now()
            total_duration = (extraction_end - extraction_start).total_seconds()
            
            error_results = {
                "extraction_metadata": {
                    "tool_version": "Agar URL Extractor v1.1",
                    "run_id": self.run_id,
                    "start_time": extraction_start.isoformat(),
                    "end_time": extraction_end.isoformat(),
                    "total_duration_seconds": total_duration,
                    "base_output_directory": self.base_output_dir,
                    "run_directory": self.run_dir,
                    "extraction_successful": False,
                    "error": str(e)
                },
                "results": results
            }
            
            return error_results


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
    """Create a sample URL extraction configuration file."""
    sample_config = {
        "# Agar URL Extractor Configuration": None,
        "base_url": "https://agar.com.au",
        "output_dir": "agar_url_data",
        
        "# Category Discovery Settings": None,
        "max_categories": 50,
        "common_category_paths": [
            "/products",
            "/categories", 
            "/cleaning-products",
            "/professional-cleaning",
            "/commercial-cleaning"
        ],
        "fallback_categories": {
            "Floor Care": "https://agar.com.au/products?category=floor-care",
            "Kitchen Cleaning": "https://agar.com.au/products?category=kitchen",
            "Carpet Care": "https://agar.com.au/products?category=carpet",
            "Bathroom Cleaning": "https://agar.com.au/products?category=bathroom"
        },
        
        "# URL Generation Settings": None,
        "batch_size": 50,
        "max_products_per_category": 1000,
        "max_pages_per_category": 20,
        "delay": 1.0,
        
        "# Output Settings": None,
        "verbose": False
    }
    
    config_file = 'url_extraction_config.yaml'
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2, allow_unicode=True)
    
    print(f"✅ Sample URL extraction configuration saved to {config_file}")


async def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Agar URL Extractor - Focused tool for building comprehensive Agar product URL extraction files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --output-dir agar_urls
  %(prog)s --config url_extraction_config.yaml --max-products 500
  %(prog)s --base-url https://agar.com.au --batch-size 25 --verbose
  %(prog)s --create-config
        """
    )
    
    # Configuration options
    parser.add_argument('--config', '-c', help='Configuration file (YAML or JSON)')
    parser.add_argument('--create-config', action='store_true', help='Create sample configuration file')
    
    # Main options
    parser.add_argument('--output-dir', default='agar_url_data', 
                       help='Output directory for URL extraction data')
    parser.add_argument('--base-url', default='https://agar.com.au', 
                       help='Base URL for Agar website')
    
    # Processing options
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Batch size for processing')
    parser.add_argument('--max-categories', type=int, default=50,
                       help='Maximum number of categories to discover')
    parser.add_argument('--max-products', type=int, default=1000,
                       help='Maximum products per category')
    parser.add_argument('--max-pages', type=int, default=20,
                       help='Maximum pages per category')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests (seconds)')
    
    # Display options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Handle special cases
    if args.create_config:
        create_sample_config()
        return
    
    # Build configuration
    config = {
        'base_url': args.base_url,
        'output_dir': args.output_dir,
        'batch_size': args.batch_size,
        'max_categories': args.max_categories,
        'max_products_per_category': args.max_products,
        'max_pages_per_category': args.max_pages,
        'delay': args.delay,
        'verbose': args.verbose
    }
    
    # Load from config file if provided
    if args.config:
        file_config = load_config_file(args.config)
        # Merge configs, with CLI args taking precedence
        config = {**file_config, **{k: v for k, v in config.items() if v is not None}}
    
    # Initialize and run URL extractor
    try:
        extractor = AgarURLExtractor(config)
        results = await extractor.run_extraction()
        
        print(f"\n🏁 URL extraction completed!")
        print(f"📂 Check output directory: {config['output_dir']}")
        
        if results['extraction_metadata']['extraction_successful']:
            summary = results['summary']
            print("✅ URL extraction successful!")
            print(f"📂 Categories discovered: {summary['categories_discovered']}")
            print(f"🔗 Unique product URLs: {summary['total_unique_products']}")
            print(f"📄 Product URLs file: {summary['product_urls_file']}")
            print(f"📄 Categories file: {summary['categories_file']}")
        else:
            print("⚠️  URL extraction failed - check logs for details")
        
    except Exception as e:
        print(f"❌ Error during URL extraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🌐 Agar URL Extractor v1.0")
    print("Focused tool for building comprehensive Agar product URL extraction files")
    print("=" * 80)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  URL extraction interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
