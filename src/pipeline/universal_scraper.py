#!/usr/bin/env python3
"""
Universal Crawl4AI Scraper
Configurable script that replaces all the various scraping examples with a single parameterized approach.

Usage:
    python universal_scraper.py --mode enhanced --urls product_urls.json --batch-size 10 --output results/
    python universal_scraper.py --mode simple --urls urls.json --content-exclusion --limit 50
    python universal_scraper.py --mode document --urls urls.json --format markdown --delay 2

Features:
- Multiple extraction modes (enhanced, simple, content-exclusion, document-generation)
- Configurable batch processing
- Content exclusion options
- Different output formats
- Environment detection (Docker/Local)
- Progress tracking and error handling
- Comprehensive configuration via CLI arguments or config file
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
from typing import List, Dict, Any, Optional
import time
import requests

# Crawl4AI imports
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy, BM25ContentFilter, LLMExtractionStrategy
from crawl4ai.async_configs import LLMConfig

# Enhanced Agar Scraper imports (if available)
try:
    from clients.agar.schemas import ScrapingConfig
    from clients.agar.enhanced_agar_scraper import EnhancedAgarScraper
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    print("⚠️  Enhanced Agar Scraper not available, will use core functionality")


class UniversalScraper:
    """
    Universal scraper that consolidates all example functionality into a single configurable class.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize scraper with configuration."""
        self.config = config
        self.mode = config.get('mode', 'simple')
        self.urls_file = config.get('urls_file')
        self.batch_size = config.get('batch_size', 10)
        self.output_dir = config.get('output_dir', 'scraping_results')
        self.delay = config.get('delay', 2.0)
        self.limit = config.get('limit', None)
        self.content_exclusion = config.get('content_exclusion', False)
        self.format = config.get('format', 'json')
        self.verbose = config.get('verbose', True)
        
        # Environment detection
        self.is_docker = os.path.exists('/.dockerenv') or config.get('docker', False)
        self.crawl4ai_url = config.get('crawl4ai_url', 'http://localhost:11235')
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load URLs
        self.product_urls = self._load_urls()
        if self.limit:
            self.product_urls = self.product_urls[:self.limit]
        self.total_urls = len(self.product_urls)
        
        self._print_initialization()
    
    def _print_initialization(self):
        """Print initialization information."""
        print(f"🚀 Universal Crawl4AI Scraper")
        print(f"=" * 60)
        print(f"🔧 Mode: {self.mode}")
        print(f"📁 URLs file: {self.urls_file}")
        print(f"🎯 Total URLs: {self.total_urls}")
        print(f"📦 Batch size: {self.batch_size}")
        print(f"📂 Output directory: {self.output_dir}")
        print(f"🐳 Environment: {'Docker' if self.is_docker else 'Local'}")
        print(f"🛡️  Content exclusion: {'Enabled' if self.content_exclusion else 'Disabled'}")
        print(f"📋 Format: {self.format}")
        print(f"⏰ Delay between requests: {self.delay}s")
        
    def _load_urls(self) -> List[str]:
        """Load URLs from file."""
        if not self.urls_file or not os.path.exists(self.urls_file):
            print(f"❌ URLs file not found: {self.urls_file}")
            return []
        
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                if self.urls_file.endswith('.json'):
                    data = json.load(f)
                    urls = []
                    
                    # Handle different JSON structures
                    if isinstance(data, list):
                        # Simple list of URLs
                        return data
                    elif isinstance(data, dict):
                        # Check for direct URL arrays
                        if data.get('all_product_urls'):
                            return data['all_product_urls']
                        elif data.get('urls'):
                            return data['urls']
                        elif data.get('product_urls'):
                            return data['product_urls']
                        
                        # Handle product_urls.json structure with categories
                        for category_name, products in data.items():
                            if isinstance(products, list):
                                for product in products:
                                    if isinstance(product, dict) and 'url' in product:
                                        urls.append(product['url'])
                                    elif isinstance(product, str):
                                        urls.append(product)
                        
                        # Remove duplicates while preserving order
                        seen = set()
                        unique_urls = []
                        for url in urls:
                            if url not in seen:
                                seen.add(url)
                                unique_urls.append(url)
                        
                        return unique_urls
                        
                elif self.urls_file.endswith(('.txt', '.csv')):
                    return [line.strip() for line in f.readlines() if line.strip()]
                
        except Exception as e:
            print(f"❌ Error loading URLs: {e}")
        
        return []
    
    def _get_extraction_strategy(self):
        """Get extraction strategy based on mode and configuration."""
        if self.mode == 'enhanced' and ENHANCED_AVAILABLE:
            # Use Enhanced Agar Scraper approach
            return None  # Will be handled separately in enhanced mode
        
        elif self.mode == 'llm':
            # LLM-based extraction
            schema = {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "description": {"type": "string"},
                    "key_benefits": {"type": "array", "items": {"type": "string"}},
                    "specifications": {"type": "object"},
                    "codes": {"type": "array", "items": {"type": "string"}},
                    "categories": {"type": "array", "items": {"type": "string"}},
                    "price": {"type": "string"},
                    "availability": {"type": "string"}
                }
            }
            
            llm_config = LLMConfig(
                provider=self.config.get('llm_provider', "openai/gpt-4o-mini"),
                api_token=os.getenv("OPENAI_API_KEY")
            )
            
            return LLMExtractionStrategy(
                llm_config=llm_config,
                schema=schema,
                extraction_type="schema",
                instruction=self.config.get('extraction_instruction', 
                    "Extract structured product information focusing on name, description, benefits, and specifications.")
            )
        
        else:  # CSS-based extraction
            schema = {
                "name": "universal_product_extraction",
                "baseSelector": "body",
                "fields": [
                    {"name": "title", "selector": "h1, .product-title, .entry-title", "type": "text"},
                    {"name": "description", "selector": ".product-description, .short-description", "type": "text"},
                    {"name": "price", "selector": ".price, .product-price, .cost", "type": "text"},
                    {"name": "specifications", "selector": ".specs, .specifications, .product-details", "type": "text"},
                    {"name": "images", "selector": ".product-images img, .gallery img", "type": "attribute", "attribute": "src"},
                    {"name": "categories", "selector": ".categories, .product-categories", "type": "text"}
                ]
            }
            
            return JsonCssExtractionStrategy(schema, verbose=self.verbose)
    
    def _get_crawler_config(self) -> CrawlerRunConfig:
        """Get crawler configuration based on settings."""
        config = CrawlerRunConfig(
            page_timeout=30000,  # 30 seconds should be sufficient
            word_count_threshold=10,
            cache_mode=CacheMode.BYPASS,
        )
        
        # Content exclusion configuration
        if self.content_exclusion:
            config.excluded_selector = """
                nav, header, footer, 
                .navigation, .navbar, .main-nav, .site-header,
                .product-enquiry, .enquiry-form, form[class*="enquiry"], 
                .footer-subscription, .newsletter-signup, .footer-newsletter,
                .sidebar, .widget-area, .social-media, .social-links,
                .breadcrumbs, .back-to-top, .scroll-to-top,
                .related-products, .upsells, .cross-sells,
                .modal, .popup, .overlay, .newsletter-modal
            """
            
            config.excluded_tags = [
                "script", "style", "noscript", "iframe", 
                "nav", "header", "footer", "aside", "form"
            ]
            
            config.remove_forms = True
            config.remove_overlay_elements = True
            
            if self.config.get('bm25_filter', True):
                config.content_filter = BM25ContentFilter(
                    bm25_threshold=self.config.get('bm25_threshold', 1.0),
                    user_query=self.config.get('filter_query', "product information specifications features benefits")
                )
        
        # Set extraction strategy
        extraction_strategy = self._get_extraction_strategy()
        if extraction_strategy:
            config.extraction_strategy = extraction_strategy
        
        return config
    
    async def scrape_url_enhanced(self, url: str, crawler_config: CrawlerRunConfig) -> Optional[Dict[str, Any]]:
        """Scrape URL using Enhanced Agar Scraper approach for rich product extraction."""
        if not ENHANCED_AVAILABLE:
            if self.verbose:
                print(f"⚠️  Enhanced Agar Scraper not available for {url}")
            return None
            
        try:
            # Configure enhanced Agar scraper
            config = ScrapingConfig(
                base_url="https://agar.com.au",
                max_products=1,
                delay_seconds=self.delay,
                output_dir=self.output_dir,
                verbose=self.verbose,
                include_images=True,
                include_documents=True,
                include_categories=True
            )
            
            # Initialize enhanced scraper
            scraper = EnhancedAgarScraper(config)
            
            # Extract products using enhanced logic
            products = await scraper.extractor.extract_products_from_urls([url])
            
            if products:
                product = products[0]
                
                # Use the enhanced scraper's schema conversion method
                enhanced_data = scraper._product_to_brief_schema(product)
                
                # Add universal scraper metadata
                enhanced_data.update({
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_mode": "enhanced",
                    "success": True
                })
                
                # Extract rich metadata from the product
                if hasattr(product, 'metadata') and product.metadata:
                    metadata = product.metadata
                    
                    # Add Open Graph and Twitter metadata structure like in create_test_example.py
                    rich_metadata = {
                        "title": enhanced_data.get("product_name", ""),
                        "description": product.description if hasattr(product, 'description') else "",
                        "keywords": None,
                        "author": None,
                    }
                    
                    # Add Open Graph metadata
                    if metadata.get("raw_extracted_data"):
                        raw_data = metadata["raw_extracted_data"]
                        
                        # Extract product images for og:image
                        product_images = raw_data.get("product_images_src", [])
                        if isinstance(product_images, str):
                            product_images = [product_images]
                        
                        if product_images and product_images[0]:
                            og_image = product_images[0]
                            if not og_image.startswith('http'):
                                og_image = f"https://agar.com.au{og_image}" if og_image.startswith('/') else f"https://agar.com.au/{og_image}"
                        else:
                            og_image = None
                        
                        rich_metadata.update({
                            "og:locale": "en_US",
                            "og:type": "product",
                            "og:title": f"{enhanced_data.get('product_name', '')} | Agar Cleaning Systems",
                            "og:description": (product.description or "Professional cleaning product")[:160],
                            "og:url": url,
                            "og:site_name": "Agar Cleaning Systems Pty Ltd",
                            "og:image": og_image,
                            "og:image:width": "1000",
                            "og:image:height": "1000", 
                            "og:image:type": "image/png",
                            "twitter:card": "summary_large_image",
                            "twitter:label1": "Product Category",
                            "twitter:data1": ", ".join(enhanced_data.get("categories", [])) or "Cleaning Products",
                            "article:publisher": "https://www.facebook.com/agarcleaningsystems",
                            "article:modified_time": datetime.now().isoformat()
                        })
                    
                    enhanced_data["metadata"] = rich_metadata
                    
                    # Add structured product information
                    if metadata.get("specifications"):
                        enhanced_data["specifications"] = metadata["specifications"]
                    
                    if metadata.get("key_benefits"):
                        enhanced_data["key_benefits"] = metadata["key_benefits"]
                    
                    # Extract SKU, size, pH level for compatibility with autobrite.md format
                    specs = metadata.get("specifications", {})
                    codes = enhanced_data.get("codes", [])
                    
                    if codes:
                        enhanced_data["sku"] = codes[0] if isinstance(codes, list) else str(codes)
                    
                    # Try to extract size and pH from specifications or raw data
                    raw_data = metadata.get("raw_extracted_data", {})
                    
                    # Extract size
                    for key, value in specs.items():
                        if any(size_word in key.lower() for size_word in ['size', 'volume', 'capacity']):
                            enhanced_data["size"] = str(value)
                            break
                    
                    # Extract pH level
                    for key, value in specs.items():
                        if 'ph' in key.lower():
                            enhanced_data["ph_level"] = str(value)
                            break
                    
                    # Add description structure
                    if product.description:
                        enhanced_data["description"] = product.description
                        
                        # Try to extract structured description parts
                        desc_content = raw_data.get("description_content", "")
                        if desc_content:
                            enhanced_data["full_description"] = desc_content
                
                return enhanced_data
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Enhanced extraction failed for {url}: {str(e)}")
                import traceback
                print(f"   Full traceback: {traceback.format_exc()}")
        
        return None
    
    async def scrape_url_standard(self, url: str, crawler: AsyncWebCrawler, crawler_config: CrawlerRunConfig) -> Optional[Dict[str, Any]]:
        """Scrape URL using standard Crawl4AI approach."""
        try:
            result = await crawler.arun(url=url, config=crawler_config)
            
            if result.success:
                extracted_data = {}
                
                if result.extracted_content:
                    try:
                        extracted_data = json.loads(result.extracted_content)
                    except json.JSONDecodeError:
                        extracted_data = {"raw_content": result.extracted_content}
                
                # Extract rich metadata from HTML (like API mode does)
                rich_metadata = self._extract_meta_tags(result.html or "")
                
                # Get product name from title or og:title
                page_title = rich_metadata.get('title', result.title if hasattr(result, 'title') else '')
                product_name = self._extract_product_name(page_title, url)
                
                # Structure the response
                product_data = {
                    "url": url,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_mode": self.mode,
                    "success": True,
                    "title": product_name,
                    "product_name": product_name,
                }
                
                # Add extracted fields
                if isinstance(extracted_data, list) and len(extracted_data) > 0:
                    extracted_data = extracted_data[0]
                
                if isinstance(extracted_data, dict):
                    product_data.update(extracted_data)
                
                # Combine rich metadata with basic metadata
                basic_metadata = {
                    "word_count": len(result.markdown.split()) if result.markdown else 0,
                    "html_length": len(result.html) if result.html else 0,
                    "content_exclusion": self.content_exclusion,
                    "processing_time": result.response_headers.get('processing_time', 'unknown') if hasattr(result, 'response_headers') else 'unknown'
                }
                
                # Merge rich metadata with basic metadata
                combined_metadata = {**basic_metadata, **rich_metadata}
                product_data["metadata"] = combined_metadata
                
                # Include raw content for document generation
                if self.format in ['markdown', 'document']:
                    product_data["raw_markdown"] = result.markdown
                    product_data["raw_html"] = result.html
                
                return product_data
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Standard extraction failed for {url}: {e}")
        
        return None
    
    async def scrape_url_api(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape URL using API approach (for Docker environments)."""
        try:
            # Prepare payload matching Docker API format
            payload = {
                "urls": [url],
                "formats": ["markdown", "cleaned_html"],
                "word_count_threshold": 10,
                "only_text": False,
                "bypass_cache": True
            }
            
            if self.content_exclusion:
                payload["excluded_tags"] = ["nav", "header", "footer", "aside", "form"]
                payload["remove_forms"] = True
                payload["remove_overlay_elements"] = True
            
            response = requests.post(
                f"{self.crawl4ai_url}/crawl",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=90
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    results = data.get('results', [])
                    if results:
                        result = results[0]
                        
                        # Extract rich metadata from HTML
                        html_content = result.get('html', result.get('cleaned_html', ''))
                        rich_metadata = self._extract_meta_tags(html_content)
                        
                        # Get basic metadata
                        basic_metadata = result.get('metadata', {})
                        
                        # Combine rich metadata with basic metadata
                        combined_metadata = {**basic_metadata, **rich_metadata}
                        
                        # Extract product name from title or og:title
                        page_title = rich_metadata.get('title', result.get('title', ''))
                        product_name = self._extract_product_name(page_title, url)
                        
                        return {
                            "url": url,
                            "extraction_timestamp": datetime.now().isoformat(),
                            "extraction_mode": "api",
                            "success": True,
                            "raw_markdown": result.get('markdown', ''),
                            "raw_html": result.get('cleaned_html', ''),
                            "content": result.get('markdown', ''),
                            "metadata": combined_metadata,
                            "title": product_name,
                            "product_name": product_name,
                        }
                else:
                    if self.verbose:
                        print(f"❌ API returned unsuccessful response for {url}: {data}")
                    
        except Exception as e:
            if self.verbose:
                print(f"❌ API extraction failed for {url}: {e}")
        
        return None
    
    def _extract_meta_tags(self, html_content: str) -> Dict[str, Any]:
        """Extract meta tags including OpenGraph and Twitter cards from HTML."""
        import re
        from html import unescape
        
        metadata = {}
        
        if not html_content:
            return metadata
        
        try:
            # Define patterns for different meta tag types
            meta_patterns = [
                # Standard meta tags
                r'<meta\s+name=["\']([^"\']+)["\']\s+content=["\']([^"\']*)["\'][^>]*>',
                r'<meta\s+content=["\']([^"\']*?)["\']\s+name=["\']([^"\']+)["\'][^>]*>',
                # Property meta tags (OpenGraph, etc.)
                r'<meta\s+property=["\']([^"\']+)["\']\s+content=["\']([^"\']*)["\'][^>]*>',
                r'<meta\s+content=["\']([^"\']*?)["\']\s+property=["\']([^"\']+)["\'][^>]*>',
                # HTTP-equiv meta tags
                r'<meta\s+http-equiv=["\']([^"\']+)["\']\s+content=["\']([^"\']*)["\'][^>]*>',
            ]
            
            for pattern in meta_patterns:
                matches = re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if 'name=' in match.group(0).lower() or 'http-equiv=' in match.group(0).lower():
                        # For name/http-equiv patterns, first group is name, second is content
                        if 'content=' in match.group(0)[:match.start(1)]:
                            # content comes before name
                            content, name = match.groups()
                        else:
                            # name comes before content
                            name, content = match.groups()
                    else:
                        # For property patterns, determine order
                        if 'content=' in match.group(0)[:match.start(1)]:
                            # content comes before property
                            content, name = match.groups()
                        else:
                            # property comes before content
                            name, content = match.groups()
                    
                    if name and content:
                        # Clean up the values
                        name = unescape(name.strip())
                        content = unescape(content.strip())
                        
                        # Store in metadata
                        if content:  # Only store non-empty content
                            metadata[name] = content
            
            # Extract title if not already present
            if 'title' not in metadata:
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE | re.DOTALL)
                if title_match:
                    metadata['title'] = unescape(title_match.group(1).strip())
            
            # Ensure we have key metadata fields even if empty
            essential_fields = [
                'title', 'description', 'keywords', 'author',
                'og:title', 'og:description', 'og:url', 'og:image', 'og:site_name', 'og:type',
                'twitter:card', 'twitter:title', 'twitter:description', 'twitter:image'
            ]
            
            for field in essential_fields:
                if field not in metadata:
                    metadata[field] = None
                        
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error extracting meta tags: {e}")
        
        return metadata
    
    def _extract_product_name(self, page_title: str, url: str) -> str:
        """Extract clean product name from page title."""
        if not page_title:
            # Try to extract from URL as fallback
            url_parts = url.strip('/').split('/')
            if url_parts and url_parts[-1]:
                # Convert URL slug to title case
                name = url_parts[-1].replace('-', ' ').replace('_', ' ')
                return ' '.join(word.capitalize() for word in name.split())
            return "Unknown Product"
        
        # Clean up title - remove site name and separators
        title = page_title.strip()
        
        # Common patterns to remove
        patterns_to_remove = [
            r'\s*\|\s*Agar Cleaning Systems.*$',
            r'\s*-\s*Agar Cleaning Systems.*$',
            r'\s*\|\s*Agar.*$',
            r'\s*-\s*Agar.*$',
        ]
        
        for pattern in patterns_to_remove:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        return title.strip() if title.strip() else "Unknown Product"
    
    async def scrape_batch(self, batch_urls: List[str], batch_num: int, total_batches: int) -> Dict[str, Any]:
        """Scrape a batch of URLs."""
        print(f"\n🔄 Processing Batch {batch_num}/{total_batches} ({len(batch_urls)} URLs)")
        
        batch_start = datetime.now()
        batch_results = []
        
        if self.mode == 'enhanced' and ENHANCED_AVAILABLE:
            # Enhanced mode - process each URL with Enhanced Agar Scraper
            crawler_config = self._get_crawler_config()
            for i, url in enumerate(batch_urls, 1):
                if self.verbose:
                    print(f"  🎯 Scraping {i}/{len(batch_urls)}: {url}")
                
                result = await self.scrape_url_enhanced(url, crawler_config)
                if result:
                    # Save individual product file
                    await self._save_individual_product_file(result)
                    batch_results.append(result)
                
                if i < len(batch_urls):
                    await asyncio.sleep(self.delay)
                    
        elif self.is_docker and self.mode == 'api':
            # API mode for Docker
            for i, url in enumerate(batch_urls, 1):
                if self.verbose:
                    print(f"  🎯 Scraping {i}/{len(batch_urls)}: {url}")
                
                result = await self.scrape_url_api(url)
                if result:
                    # Save individual product file
                    await self._save_individual_product_file(result)
                    batch_results.append(result)
                
                if i < len(batch_urls):
                    await asyncio.sleep(self.delay)
                    
        else:
            # Standard async crawler mode
            browser_config = BrowserConfig(headless=True, verbose=self.verbose)
            crawler_config = self._get_crawler_config()
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                for i, url in enumerate(batch_urls, 1):
                    if self.verbose:
                        print(f"  🎯 Scraping {i}/{len(batch_urls)}: {url}")
                    
                    result = await self.scrape_url_standard(url, crawler, crawler_config)
                    if result:
                        # Save individual product file
                        await self._save_individual_product_file(result)
                        batch_results.append(result)
                    
                    if i < len(batch_urls):
                        await asyncio.sleep(self.delay)
        
        processing_time = (datetime.now() - batch_start).total_seconds()
        
        if self.verbose:
            print(f"✅ Batch {batch_num} completed:")
            print(f"   📊 Products extracted: {len(batch_results)}/{len(batch_urls)}")
            print(f"   ⏱️  Processing time: {processing_time:.1f}s")
        
        return {
            "batch_num": batch_num,
            "success": len(batch_results) > 0,
            "urls_attempted": len(batch_urls),
            "products_extracted": len(batch_results),
            "processing_time": processing_time,
            "products": batch_results
        }
    
    async def _save_individual_product_file(self, product_data: Dict[str, Any]) -> str:
        """Save individual product file with filtered content, named after product name."""
        # Extract product name for filename
        product_name = (
            product_data.get('product_name') or 
            product_data.get('title') or 
            'Unknown_Product'
        )
        
        # Clean product name for filename (remove special characters)
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', product_name)
        safe_name = re.sub(r'\s+', '_', safe_name).strip('_')
        if not safe_name:
            safe_name = 'Unknown_Product'
        
        # Create filtered product data (exclude large raw content sections)
        filtered_data = {
            "url": product_data.get("url"),
            "extraction_timestamp": product_data.get("extraction_timestamp"),
            "extraction_mode": product_data.get("extraction_mode"),
            "success": product_data.get("success"),
            "metadata": product_data.get("metadata", {}),
            "title": product_data.get("title", ""),
            "product_name": product_data.get("product_name", "")
        }
        
        # Add any additional extracted structured data (but not raw content)
        excluded_keys = {
            'raw_markdown', 'raw_html', 'content', 'markdown_with_citations', 
            'references_markdown', 'fit_markdown', 'fit_html'
        }
        
        for key, value in product_data.items():
            if key not in excluded_keys and key not in filtered_data:
                # Only add non-raw content fields
                if not (isinstance(value, dict) and any(raw_key in value for raw_key in excluded_keys)):
                    filtered_data[key] = value
        
        # Create individual product file
        product_filename = f"{self.output_dir}/{safe_name}.json"
        
        # Handle duplicate filenames by adding counter
        counter = 1
        original_filename = product_filename
        while os.path.exists(product_filename):
            base, ext = os.path.splitext(original_filename)
            product_filename = f"{base}_{counter}{ext}"
            counter += 1
        
        try:
            with open(product_filename, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, indent=2, ensure_ascii=False, default=str)
            
            if self.verbose:
                print(f"    💾 Saved: {os.path.basename(product_filename)}")
                
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Failed to save {product_filename}: {e}")
        
        return product_filename

    def _create_batches(self) -> List[List[str]]:
        """Create batches from URLs."""
        batches = []
        for i in range(0, len(self.product_urls), self.batch_size):
            batch = self.product_urls[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    async def run_scraping(self) -> Dict[str, Any]:
        """Run the complete scraping process."""
        print(f"\n🎬 Starting Universal Scraping Process")
        print(f"=" * 60)
        
        overall_start = datetime.now()
        batches = self._create_batches()
        
        all_results = []
        all_products = []
        total_success = 0
        total_failed = 0
        
        print(f"📊 Created {len(batches)} batches of max {self.batch_size} URLs each")
        
        # Process each batch
        for i, batch_urls in enumerate(batches, 1):
            batch_result = await self.scrape_batch(batch_urls, i, len(batches))
            all_results.append(batch_result)
            
            if batch_result["success"]:
                total_success += batch_result["products_extracted"]
                all_products.extend(batch_result.get("products", []))
            
            total_failed += (batch_result["urls_attempted"] - batch_result.get("products_extracted", 0))
            
            # Pause between batches
            if i < len(batches):
                print(f"⏸️  Pausing {self.delay} seconds before next batch...")
                await asyncio.sleep(self.delay)
        
        overall_time = (datetime.now() - overall_start).total_seconds()
        
        # Compile final results
        final_results = {
            "scraping_metadata": {
                "scraper_version": "Universal Scraper v1.0",
                "start_time": overall_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_processing_time_seconds": overall_time,
                "extraction_mode": self.mode,
                "content_exclusion_enabled": self.content_exclusion,
                "environment": "Docker" if self.is_docker else "Local",
                "total_urls_attempted": self.total_urls,
                "total_products_extracted": total_success,
                "total_failed": total_failed,
                "success_rate": f"{(total_success / self.total_urls) * 100:.1f}%",
                "batches_processed": len(batches),
                "batch_size": self.batch_size,
                "delay_seconds": self.delay,
                "output_format": self.format
            },
            "batch_results": all_results,
            "all_products": all_products
        }
        
        # Save master results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        master_file = f"{self.output_dir}/universal_scraping_results_{timestamp}.json"
        
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save products-only file
        products_file = f"{self.output_dir}/extracted_products_{timestamp}.json"
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False, default=str)
        
        # Generate documents if requested
        if self.format in ['markdown', 'document']:
            await self._generate_documents(all_products, timestamp)
        
        print(f"\n🎉 UNIVERSAL SCRAPING COMPLETE!")
        print(f"=" * 60)
        print(f"📊 Final Results:")
        print(f"   🎯 URLs processed: {self.total_urls}")
        print(f"   ✅ Products extracted: {total_success}")
        print(f"   ❌ Failed extractions: {total_failed}")
        print(f"   📈 Success rate: {(total_success / self.total_urls) * 100:.1f}%")
        print(f"   ⏱️  Total time: {overall_time/60:.1f} minutes")
        print(f"   📁 Master results: {os.path.basename(master_file)}")
        print(f"   📄 Products file: {os.path.basename(products_file)}")
        
        return final_results
    
    async def _generate_documents(self, products: List[Dict[str, Any]], timestamp: str):
        """Generate markdown documents for each product."""
        docs_dir = f"{self.output_dir}/documents_{timestamp}"
        os.makedirs(docs_dir, exist_ok=True)
        
        print(f"\n📝 Generating {len(products)} product documents...")
        
        for product in products:
            product_name = product.get('product_name', product.get('title', 'Unknown Product'))
            slug = re.sub(r'[^a-zA-Z0-9_-]', '_', product_name.lower())
            
            doc_content = self._create_product_document(product)
            doc_file = f"{docs_dir}/{slug}.md"
            
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(doc_content)
        
        print(f"✅ Documents saved to: {docs_dir}")
    
    def _create_product_document(self, product: Dict[str, Any]) -> str:
        """Create a structured markdown document for a product matching autobrite.md format."""
        # Extract key information
        name = product.get('product_name', product.get('title', 'Unknown Product'))
        url = product.get('url', '')
        extraction_date = product.get('extraction_timestamp', datetime.now().isoformat())
        
        # Parse extraction date for display
        try:
            if extraction_date:
                dt = datetime.fromisoformat(extraction_date.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%d/%m/%Y')
            else:
                formatted_date = datetime.now().strftime('%d/%m/%Y')
        except:
            formatted_date = datetime.now().strftime('%d/%m/%Y')
        
        # Extract structured data from raw content or extracted fields
        raw_markdown = product.get('raw_markdown', '')
        raw_html = product.get('raw_html', '')
        
        # Try to extract structured information
        product_info = self._extract_product_structure(product, raw_markdown, raw_html)
        
        # Build the document following autobrite.md template
        doc = f"""## Source Information

- **URL**: {url}
- **Extraction Date**: {formatted_date}


## Product Information

### Core Product Details

- **Product Name**: {product_info['name']}
- **SKU**: {product_info['sku']}
- **Size**: {product_info['size']}
- **pH Level**: {product_info['ph_level']}
- **Category**: {product_info['category']}
- **Product Type**: {product_info['product_type']}

### Product Description

**What is {product_info['name']}?**
{product_info['description']}

### Key Benefits

{self._format_benefits_list(product_info['benefits'])}

### How It Works

{product_info['how_it_works']}

### Usage Applications

**For Use On:**
{self._format_usage_list(product_info['usage_applications'])}

**Optimal Usage:**
{product_info['optimal_usage']}

## Technical Specifications

{self._format_specifications_table(product_info['technical_specs'])}

## Media Assets Extracted

### Product Images

{self._format_images_section(product_info['images'])}

## Product Categories & Related Products

### Primary Category
- {product_info['primary_category']}

### Related Product Categories
{self._format_related_categories(product_info['related_categories'])}

"""
        
        return doc
    
    def _extract_product_structure(self, product: Dict[str, Any], raw_markdown: str, raw_html: str) -> Dict[str, Any]:
        """Extract structured product information from available data."""
        import re
        
        # Initialize with defaults
        product_structure = {
            'name': product.get('product_name', product.get('title', 'Unknown Product')),
            'sku': '',
            'size': '',
            'ph_level': '',
            'category': product.get('category', ''),
            'product_type': '',
            'description': product.get('description', 'Product description not available.'),
            'benefits': product.get('key_benefits', []),
            'how_it_works': 'Information about how this product works is not available.',
            'usage_applications': [],
            'optimal_usage': 'Usage information not available.',
            'technical_specs': {},
            'images': [],
            'primary_category': product.get('category', 'Uncategorized'),
            'related_categories': []
        }
        
        # Try to extract from markdown content if available
        content = raw_markdown or product.get('content', '')
        
        if content:
            # Extract SKU
            sku_patterns = [
                r'(?:SKU|Product Code|Code):\s*([A-Z0-9]+)',
                r'Product\s+Code\s*[:\-]\s*([A-Z0-9]+)',
                r'SKU\s*[:\-]\s*([A-Z0-9]+)'
            ]
            for pattern in sku_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    product_structure['sku'] = match.group(1)
                    break
            
            # Extract size
            size_patterns = [
                r'(?:Size|Volume):\s*(\d+[LlMm]?)',
                r'(\d+L)\s*(?:container|bottle|pack)',
                r'Available\s+in\s*(\d+[LlMm]?)'
            ]
            for pattern in size_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    product_structure['size'] = match.group(1)
                    break
            
            # Extract pH level
            ph_patterns = [
                r'(?:pH|pH Level):\s*([\d\.\s\+\-\/]+)',
                r'pH\s+of\s+([\d\.\s\+\-\/]+)',
                r'pH\s*[:\-]\s*([\d\.\s\+\-\/]+)'
            ]
            for pattern in ph_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    product_structure['ph_level'] = match.group(1).strip()
                    break
            
            # Extract product type from description
            if 'cleaner' in content.lower():
                if 'floor' in content.lower():
                    product_structure['product_type'] = 'Floor cleaner'
                elif 'carpet' in content.lower():
                    product_structure['product_type'] = 'Carpet cleaner'
                elif 'kitchen' in content.lower():
                    product_structure['product_type'] = 'Kitchen cleaner'
                else:
                    product_structure['product_type'] = 'Cleaning product'
            
            # Try to extract better description
            desc_patterns = [
                r'What is [^?]+\?\s*([^\.]+\.(?:[^\.]+\.)*)',
                r'(?:Description|Product Description)[:\-]\s*([^\n\r]+)',
                r'^([A-Z][^\.]+\.[^\.]*\.(?:[^\.]+\.)*)'
            ]
            for pattern in desc_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match and len(match.group(1)) > len(product_structure['description']):
                    product_structure['description'] = match.group(1).strip()
                    break
        
        # Use extracted data from JSON if available and better
        if product.get('specifications'):
            specs = product['specifications']
            if isinstance(specs, dict):
                product_structure['technical_specs'] = specs
            elif isinstance(specs, str):
                # Try to parse specifications from text
                spec_lines = specs.split('\n')
                for line in spec_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        product_structure['technical_specs'][key.strip()] = value.strip()
        
        # Add basic specs if we extracted them
        if product_structure['sku']:
            product_structure['technical_specs']['Product Code'] = product_structure['sku']
        if product_structure['size']:
            product_structure['technical_specs']['Size'] = product_structure['size']
        if product_structure['ph_level']:
            product_structure['technical_specs']['pH Level'] = product_structure['ph_level']
        if product_structure['category']:
            product_structure['technical_specs']['Category'] = product_structure['category']
        
        return product_structure
    
    def _format_benefits_list(self, benefits: List[str]) -> str:
        """Format benefits as numbered list."""
        if not benefits:
            return "Benefits information not available."
        
        formatted = ""
        for i, benefit in enumerate(benefits, 1):
            formatted += f"{i}. {benefit}\n"
        
        return formatted.strip()
    
    def _format_usage_list(self, usage_apps: List[str]) -> str:
        """Format usage applications as bullet list."""
        if not usage_apps:
            return "- Usage information not available"
        
        formatted = ""
        for app in usage_apps:
            formatted += f"- {app}\n"
        
        return formatted.strip()
    
    def _format_specifications_table(self, specs: Dict[str, Any]) -> str:
        """Format specifications as markdown table."""
        if not specs:
            return """| Specification | Value |
|---------------|-------|
| Information | Not available |"""
        
        table = "| Specification | Value |\n|---------------|-------|\n"
        for key, value in specs.items():
            table += f"| {key} | {value} |\n"
        
        return table
    
    def _format_images_section(self, images: List[str]) -> str:
        """Format images section."""
        if not images:
            return "No product images extracted."
        
        formatted = ""
        for i, image in enumerate(images, 1):
            formatted += f"{i}. **Product Image {i}**\n"
            formatted += f"   - URL: {image}\n"
            formatted += f"   - Format: {image.split('.')[-1].upper() if '.' in image else 'Unknown'}\n\n"
        
        return formatted.strip()
    
    def _format_related_categories(self, categories: List[str]) -> str:
        """Format related categories list."""
        if not categories:
            return "- Related categories not available"
        
        formatted = ""
        for category in categories:
            formatted += f"- {category}\n"
        
        return formatted.strip()


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file."""
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                return yaml.safe_load(f)
            elif config_path.endswith('.json'):
                return json.load(f)
    except Exception as e:
        print(f"⚠️  Error loading config file {config_path}: {e}")
    
    return {}


def create_sample_config():
    """Create a sample configuration file."""
    sample_config = {
        "mode": "simple",  # enhanced, simple, llm, api
        "urls_file": "product_urls.json",
        "batch_size": 10,
        "output_dir": "scraping_results",
        "delay": 2.0,
        "limit": None,
        "content_exclusion": False,
        "format": "json",  # json, markdown, document
        "verbose": True,
        "docker": False,
        "crawl4ai_url": "http://localhost:11235",
        "llm_provider": "openai/gpt-4o-mini",
        "bm25_filter": True,
        "bm25_threshold": 1.0,
        "filter_query": "product information specifications features benefits",
        "extraction_instruction": "Extract structured product information focusing on name, description, benefits, and specifications."
    }
    
    with open('scraper_config.yaml', 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    
    print("✅ Sample configuration saved to scraper_config.yaml")


async def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Universal Crawl4AI Scraper - Configurable web scraping tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode simple --urls urls.json --batch-size 5
  %(prog)s --mode enhanced --urls products.json --content-exclusion --limit 50
  %(prog)s --config scraper_config.yaml
  %(prog)s --create-config
        """
    )
    
    # Configuration options
    parser.add_argument('--config', '-c', help='Configuration file (YAML or JSON)')
    parser.add_argument('--create-config', action='store_true', help='Create sample configuration file')
    
    # Basic options
    parser.add_argument('--mode', choices=['simple', 'enhanced', 'llm', 'api'], 
                       default='simple', help='Extraction mode')
    parser.add_argument('--urls', '--urls-file', dest='urls_file', 
                       help='URL file (JSON, TXT, or CSV)')
    parser.add_argument('--batch-size', type=int, default=10, 
                       help='Batch size for processing')
    parser.add_argument('--output', '--output-dir', dest='output_dir', 
                       default='scraping_results', help='Output directory')
    
    # Processing options
    parser.add_argument('--delay', type=float, default=2.0, 
                       help='Delay between requests (seconds)')
    parser.add_argument('--limit', type=int, help='Limit number of URLs to process')
    parser.add_argument('--content-exclusion', action='store_true', 
                       help='Enable content exclusion')
    parser.add_argument('--format', choices=['json', 'markdown', 'document'], 
                       default='json', help='Output format')
    
    # Environment options
    parser.add_argument('--docker', action='store_true', help='Force Docker mode')
    parser.add_argument('--crawl4ai-url', default='http://localhost:11235', 
                       help='Crawl4AI server URL for API mode')
    parser.add_argument('--verbose', '-v', action='store_true', default=True,
                       help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
    
    args = parser.parse_args()
    
    # Handle special cases
    if args.create_config:
        create_sample_config()
        return
    
    # Build configuration
    config = {}
    
    # Load from config file if provided
    if args.config:
        config = load_config_file(args.config)
    
    # Override with command line arguments
    config.update({
        'mode': args.mode,
        'urls_file': args.urls_file,
        'batch_size': args.batch_size,
        'output_dir': args.output_dir,
        'delay': args.delay,
        'limit': args.limit,
        'content_exclusion': args.content_exclusion,
        'format': args.format,
        'docker': args.docker,
        'crawl4ai_url': args.crawl4ai_url,
        'verbose': not args.quiet if args.quiet else args.verbose
    })
    
    # Validate required parameters
    if not config.get('urls_file'):
        print("❌ Error: URLs file is required. Use --urls to specify the file.")
        parser.print_help()
        return
    
    # Initialize and run scraper
    try:
        scraper = UniversalScraper(config)
        results = await scraper.run_scraping()
        
        print(f"\n🏁 Scraping completed successfully!")
        print(f"📂 Check output directory: {config['output_dir']}")
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🌐 Universal Crawl4AI Scraper v1.0")
    print("Consolidates all example functionality into a single configurable tool")
    print("=" * 70)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
