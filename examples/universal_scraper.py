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
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy, BM25ContentFilter, LLMExtractionStrategy
from crawl4ai.models import LLMConfig

# Enhanced Agar Scraper imports (if available)
try:
    from crawl4ai.agar.schemas import ScrapingConfig
    from crawl4ai.agar.enhanced_agar_scraper import EnhancedAgarScraper
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
                    # Handle different JSON structures
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return (data.get('all_product_urls') or 
                               data.get('urls') or 
                               data.get('product_urls') or [])
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
            wait_for="networkidle",
            page_timeout=30000,
            word_count_threshold=10,
            bypass_cache=True,
            process_iframes=False,
            remove_overlay_elements=True,
            simulate_user=True,
            override_navigator=True,
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
        """Scrape URL using Enhanced Agar Scraper approach."""
        if not ENHANCED_AVAILABLE:
            return None
            
        try:
            config = ScrapingConfig(
                base_url="https://agar.com.au",
                max_products=1,
                delay_seconds=self.delay,
                output_dir=self.output_dir,
                verbose=self.verbose
            )
            
            scraper = EnhancedAgarScraper(config)
            products = await scraper.extractor.extract_products_from_urls([url])
            
            if products:
                product = products[0]
                return scraper._product_to_brief_schema(product)
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Enhanced extraction failed for {url}: {e}")
        
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
                
                # Structure the response
                product_data = {
                    "url": url,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_mode": self.mode,
                    "success": True
                }
                
                # Add extracted fields
                if isinstance(extracted_data, list) and len(extracted_data) > 0:
                    extracted_data = extracted_data[0]
                
                if isinstance(extracted_data, dict):
                    product_data.update(extracted_data)
                
                # Add metadata
                product_data["metadata"] = {
                    "word_count": len(result.markdown.split()) if result.markdown else 0,
                    "html_length": len(result.html) if result.html else 0,
                    "content_exclusion": self.content_exclusion,
                    "processing_time": result.response_headers.get('processing_time', 'unknown')
                }
                
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
            payload = {
                "urls": [url],
                "extraction_options": {
                    "extract_media": True,
                    "extract_links": True,
                    "extract_tables": True,
                    "content_exclusion": self.content_exclusion
                }
            }
            
            response = requests.post(
                f"{self.crawl4ai_url}/crawl",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('results'):
                    result = data['results'][0]
                    return {
                        "url": url,
                        "extraction_timestamp": datetime.now().isoformat(),
                        "extraction_mode": "api",
                        "content": result.get('markdown', ''),
                        "metadata": result.get('metadata', {}),
                        "success": True
                    }
                    
        except Exception as e:
            if self.verbose:
                print(f"❌ API extraction failed for {url}: {e}")
        
        return None
    
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
                        batch_results.append(result)
                    
                    if i < len(batch_urls):
                        await asyncio.sleep(self.delay)
        
        processing_time = (datetime.now() - batch_start).total_seconds()
        
        # Save batch results
        batch_file = f"{self.output_dir}/batch_{batch_num:03d}_results.json"
        batch_data = {
            "batch_metadata": {
                "batch_number": batch_num,
                "total_batches": total_batches,
                "processing_date": datetime.now().isoformat(),
                "urls_attempted": len(batch_urls),
                "products_extracted": len(batch_results),
                "success_rate": f"{(len(batch_results) / len(batch_urls)) * 100:.1f}%",
                "processing_time_seconds": processing_time,
                "extraction_mode": self.mode
            },
            "products": batch_results
        }
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False, default=str)
        
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
        """Create a markdown document for a product."""
        name = product.get('product_name', product.get('title', 'Unknown Product'))
        url = product.get('url', '')
        description = product.get('description', '')
        
        doc = f"""# {name}

## Source Information
- **URL**: {url}
- **Extraction Date**: {product.get('extraction_timestamp', datetime.now().isoformat())}
- **Extraction Mode**: {product.get('extraction_mode', 'unknown')}

## Product Information

### Description
{description if description else 'No description available'}

### Key Benefits
"""
        
        benefits = product.get('key_benefits', [])
        if benefits:
            for benefit in benefits:
                doc += f"- {benefit}\n"
        else:
            doc += "No benefits information available\n"
        
        doc += "\n### Specifications\n"
        specs = product.get('specifications', {})
        if specs and isinstance(specs, dict):
            for key, value in specs.items():
                doc += f"- **{key}**: {value}\n"
        else:
            doc += "No specifications available\n"
        
        # Add metadata
        metadata = product.get('metadata', {})
        if metadata:
            doc += f"\n### Extraction Metadata\n"
            for key, value in metadata.items():
                doc += f"- **{key}**: {value}\n"
        
        return doc


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
