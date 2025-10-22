#!/usr/bin/env python3
"""
FIXED Docker Production Scraper for Agar Product URLs
Fixes LLM extraction to output clean structured data matching user schema
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.async_configs import LLMConfig

def load_env_file(env_file_path="/app/.llm.env"):
    """Load environment variables from .llm.env file."""
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print(f"✅ Loaded environment variables from {env_file_path}")
    else:
        print(f"⚠️  Environment file not found: {env_file_path}")

# Load environment variables at script start
load_env_file()

class AgarProductScraperFixed:
    """FIXED production scraper for Agar product URLs with proper LLM extraction."""
    
    def __init__(self, output_dir="/app/agar_batch_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stats = {
            "total_urls": 0,
            "successful": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None
        }
        
    def load_urls(self, url_file="/app/complete_agar_product_urls_20251008_122301.json"):
        """Load the 189 product URLs from JSON file."""
        if os.path.exists(url_file):
            with open(url_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    urls = data
                else:
                    # Check for different possible key names
                    urls = data.get('all_product_urls', data.get('urls', []))
            print(f"✅ Loaded {len(urls)} URLs from {url_file}")
            return urls
        else:
            print(f"❌ URL file not found: {url_file}")
            return []
    
    async def scrape_single_product(self, url: str, crawler: AsyncWebCrawler) -> Dict[str, Any]:
        """Scrape a single product URL with proper LLM extraction."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "YOUR_OPENAI_API":
                return {
                    "url": url,
                    "success": False,
                    "error": "OpenAI API key not configured",
                    "scraped_at": datetime.now().isoformat()
                }
            
            # Create LLM configuration
            llm_config = LLMConfig(
                provider="openai/gpt-4o-mini",
                api_token=api_key
            )
            
            # User-specified schema for clean output
            user_schema = {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "product_url": {"type": "string"},
                    "codes": {"type": "array", "items": {"type": "string"}},
                    "skus": {"type": "array", "items": {"type": "string"}}, 
                    "categories": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "sizes": {"type": "array", "items": {"type": "string"}},
                    "specifications": {"type": "object"},
                    "key_benefits": {"type": "array", "items": {"type": "string"}},
                    "description": {
                        "type": "object",
                        "properties": {
                            "overview": {"type": "string"},
                            "how_it_works": {"type": "string"},
                            "applications": {"type": "string"}
                        }
                    },
                    "images": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "url": {"type": "string"},
                                "alt_text": {"type": "string"}
                            }
                        }
                    },
                    "scraped_at": {"type": "string"}
                },
                "required": ["product_name", "product_url", "scraped_at"]
            }
            
            # Improved extraction strategy with detailed instructions
            extraction_strategy = LLMExtractionStrategy(
                llm_config=llm_config,
                schema=user_schema,
                extraction_type="schema",
                instruction=f"""
Extract structured product information from this Agar cleaning product webpage.
Focus ONLY on product details, ignore navigation and site content.

REQUIRED FIELDS:
- product_name: Extract the main product name (e.g., "3D-Gloss", "Acid Wash")
- product_url: Use "{url}"
- scraped_at: Use current timestamp "{datetime.now().isoformat()}"

EXTRACT IF AVAILABLE:
- codes: Product codes from "Code" section or SKU field (e.g., ["3DG5", "3DG20"])
- skus: Same as codes, product SKU identifiers
- categories: Product categories from breadcrumbs or category links (e.g., ["Floor Sealers"])
- tags: Any product tags or special classifications  
- sizes: Available sizes from "Sizes" section (e.g., ["5L", "20L"])
- specifications: Technical specs like pH level, perfume, etc as object (e.g., {{"ph_level": "8.4 - 9.4"}})
- key_benefits: Bullet points from "Key Benefits" section as array of strings
- description: Extract "What is..." and "How Does It Work?" content into:
  - overview: Main product description
  - how_it_works: Technical explanation if available
  - applications: "For Use On..." usage information
- images: Product images with url, alt_text, and type

Return ONLY valid JSON matching the exact schema. Do not include navigation links, website content, or unrelated information.
                """
            )
            
            # Perform the crawl with LLM extraction
            result = await crawler.arun(
                url=url,
                extraction_strategy=extraction_strategy,
                bypass_cache=True,
                only_text=True,
                process_iframes=False,
                remove_overlay_elements=True,
                simulate_user=True,
                override_navigator=True
            )
            
            if result.success and result.extracted_content:
                try:
                    # Parse the extracted JSON
                    product_data = json.loads(result.extracted_content)
                    
                    # Ensure required fields are present
                    product_data["product_url"] = url
                    product_data["scraped_at"] = datetime.now().isoformat()
                    
                    return {
                        "success": True,
                        "product_data": product_data
                    }
                except json.JSONDecodeError as e:
                    return {
                        "url": url,
                        "success": False,
                        "error": f"JSON decode failed: {str(e)}",
                        "raw_extracted_content": result.extracted_content[:500] + "..." if len(result.extracted_content) > 500 else result.extracted_content,
                        "scraped_at": datetime.now().isoformat()
                    }
            else:
                return {
                    "url": url,
                    "success": False,
                    "error": result.error_message if hasattr(result, 'error_message') else "Crawl failed or no extracted content",
                    "scraped_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": f"Exception: {str(e)}",
                "scraped_at": datetime.now().isoformat()
            }
    
    async def run_single_test(self, test_url: str):
        """Test with a single product URL to validate extraction."""
        print(f"🧪 Testing single product extraction: {test_url}")
        
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await self.scrape_single_product(test_url, crawler)
            
            if result["success"]:
                print("✅ Single test successful!")
                print("📋 Extracted product data:")
                print(json.dumps(result["product_data"], indent=2, ensure_ascii=False))
                return result["product_data"]
            else:
                print("❌ Single test failed!")
                print(f"Error: {result['error']}")
                if 'raw_extracted_content' in result:
                    print(f"Raw content: {result['raw_extracted_content']}")
                return None
    
    async def run_batch_scraping(self, urls: List[str], max_concurrent: int = 3, delay_between_batches: float = 2.0):
        """Run batch scraping with clean structured output."""
        print(f"🚀 Starting FIXED batch scraping of {len(urls)} Agar product URLs")
        print(f"   Max concurrent: {max_concurrent}")
        print(f"   Delay between batches: {delay_between_batches}s")
        print(f"   Output directory: {self.output_dir}")
        
        self.stats["total_urls"] = len(urls)
        self.stats["start_time"] = datetime.now()
        
        successful_products = []
        failed_scrapes = []
        
        async with AsyncWebCrawler(verbose=False) as crawler:
            # Process URLs in batches
            for i in range(0, len(urls), max_concurrent):
                batch_urls = urls[i:i + max_concurrent]
                batch_num = (i // max_concurrent) + 1
                total_batches = (len(urls) + max_concurrent - 1) // max_concurrent
                
                print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch_urls)} URLs)")
                
                # Process batch concurrently
                batch_tasks = [
                    self.scrape_single_product(url, crawler) 
                    for url in batch_urls
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process batch results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        print(f"   ❌ {batch_urls[j]}: Exception - {result}")
                        self.stats["failed"] += 1
                        failed_scrapes.append({
                            "url": batch_urls[j],
                            "error": str(result),
                            "scraped_at": datetime.now().isoformat()
                        })
                    elif result["success"]:
                        product_name = result["product_data"].get("product_name", "Unknown")
                        print(f"   ✅ {result['product_data']['product_url']}: {product_name}")
                        self.stats["successful"] += 1
                        successful_products.append(result["product_data"])
                    else:
                        print(f"   ❌ {result['url']}: {result['error']}")
                        self.stats["failed"] += 1
                        failed_scrapes.append(result)
                
                # Delay between batches
                if i + max_concurrent < len(urls):
                    print(f"   ⏱️  Waiting {delay_between_batches}s before next batch...")
                    await asyncio.sleep(delay_between_batches)
        
        self.stats["end_time"] = datetime.now()
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        # Create final clean output
        final_output = {
            "metadata": {
                "scraped_at": self.stats["end_time"].isoformat(),
                "total_urls": self.stats["total_urls"],
                "successful": self.stats["successful"],
                "failed": self.stats["failed"],
                "success_rate": (self.stats["successful"] / self.stats["total_urls"] * 100) if self.stats["total_urls"] > 0 else 0,
                "duration_seconds": duration
            },
            "products": successful_products,
            "failed_scrapes": failed_scrapes
        }
        
        # Save clean results
        final_file = self.output_dir / f"agar_clean_products_{self.timestamp}.json"
        with open(final_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
        
        # Save individual products for easy access
        products_file = self.output_dir / f"agar_products_only_{self.timestamp}.json"
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(successful_products, f, indent=2, ensure_ascii=False)
        
        # Save summary
        summary_file = self.output_dir / f"agar_scraping_summary_{self.timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Agar Product Scraping Summary (FIXED Version)\n")
            f.write(f"=============================================\n")
            f.write(f"Timestamp: {self.stats['end_time'].isoformat()}\n")
            f.write(f"Total URLs: {self.stats['total_urls']}\n")
            f.write(f"Successful: {self.stats['successful']}\n")
            f.write(f"Failed: {self.stats['failed']}\n")
            f.write(f"Success Rate: {(self.stats['successful'] / self.stats['total_urls'] * 100):.1f}%\n")
            f.write(f"Duration: {duration:.1f} seconds\n")
            f.write(f"Clean Products File: {products_file.name}\n")
            f.write(f"Complete Results: {final_file.name}\n")
        
        print(f"\n🎉 FIXED batch scraping completed!")
        print(f"   ✅ Successful: {self.stats['successful']}")
        print(f"   ❌ Failed: {self.stats['failed']}")
        print(f"   📊 Success rate: {(self.stats['successful'] / self.stats['total_urls'] * 100):.1f}%")
        print(f"   ⏱️  Duration: {duration:.1f} seconds")
        print(f"   💾 Clean products saved to: {products_file}")
        print(f"   📋 Complete results: {final_file}")
        
        return final_output

async def main():
    """Main function to run the FIXED scraper."""
    print("🐳 Agar Product Scraper - FIXED Docker Version")
    print("=" * 70)
    
    # Initialize scraper
    scraper = AgarProductScraperFixed()
    
    # Load URLs
    urls = scraper.load_urls()
    if not urls:
        print("❌ No URLs to process. Exiting.")
        return
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "YOUR_OPENAI_API":
        print("❌ OpenAI API key not configured. Please set OPENAI_API_KEY in .llm.env")
        return
    
    print("✅ OpenAI API key configured")
    
    # Test with a single product first
    test_url = urls[0]  # Use first URL for testing
    print(f"\n🧪 Testing extraction with: {test_url}")
    
    test_result = await scraper.run_single_test(test_url)
    if not test_result:
        print("❌ Single test failed. Please check the extraction strategy.")
        return
    
    # Ask user if they want to proceed with full batch
    print(f"\n✅ Single test successful! Ready to process all {len(urls)} URLs.")
    print("This will take several minutes...")
    
    # Run full batch scraping
    results = await scraper.run_batch_scraping(
        urls=urls,
        max_concurrent=3,  # Conservative to avoid rate limits
        delay_between_batches=2.0
    )
    
    print(f"\n📊 Final Statistics:")
    print(f"   Products successfully extracted: {results['metadata']['successful']}")
    print(f"   Failed scrapes: {results['metadata']['failed']}")
    print(f"   Success rate: {results['metadata']['success_rate']:.1f}%")
    print(f"   Duration: {results['metadata']['duration_seconds']:.1f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
