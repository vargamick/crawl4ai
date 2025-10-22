#!/usr/bin/env python3
"""
Simplified Docker Batch Scraper for Agar Products
Uses the core crawl4ai functionality to scrape all products and format them correctly.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.models import LLMConfig

class SimplifiedDockerBatchScraper:
    """
    Simplified batch scraper that works with Docker container.
    """
    
    def __init__(self, urls_file: str, batch_size: int = 8):
        self.urls_file = urls_file
        self.batch_size = batch_size
        self.output_dir = "/app/agar_batch_output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load URLs
        with open(urls_file, 'r') as f:
            data = json.load(f)
        self.product_urls = data.get("all_product_urls", [])
        self.total_urls = len(self.product_urls)
        
        print(f"🐳 Simplified Docker Batch Scraper")
        print(f"📊 Total URLs: {self.total_urls}")
        print(f"📦 Batch size: {batch_size}")
        
    def _create_extraction_strategy(self):
        """Create extraction strategy for product data."""
        schema = {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "product_url": {"type": "string"},
                "description": {"type": "string"},
                "key_benefits": {"type": "array", "items": {"type": "string"}},
                "specifications": {"type": "object"},
                "codes": {"type": "array", "items": {"type": "string"}},
                "skus": {"type": "array", "items": {"type": "string"}},
                "categories": {"type": "array", "items": {"type": "string"}},
                "sizes": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}},
                "scraped_at": {"type": "string"}
            }
        }
        
        llm_config = LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv("OPENAI_API_KEY")
        )
        
        return LLMExtractionStrategy(
            llm_config=llm_config,
            schema=schema,
            extraction_type="schema",
            instruction="""
            Extract structured product information from this Agar cleaning product page.
            Focus on:
            - Product name and description
            - Key benefits (bullet points)
            - Technical specifications (pH level, perfume, etc.)
            - Product codes and SKUs
            - Categories and product classifications
            - Available sizes
            - Any tags or special features
            
            Return exactly in the requested JSON schema format.
            """
        )
    
    async def scrape_product(self, url: str, crawler: AsyncWebCrawler, extraction_strategy) -> Dict[str, Any]:
        """Scrape a single product URL."""
        try:
            result = await crawler.arun(
                url=url,
                extraction_strategy=extraction_strategy,
                bypass_cache=True,
                process_iframes=False,
                remove_overlay_elements=True,
                simulate_user=True,
                override_navigator=True
            )
            
            if result.success and result.extracted_content:
                # Parse the extracted JSON
                try:
                    product_data = json.loads(result.extracted_content)
                    
                    # Ensure required format
                    formatted_data = {
                        "product_name": product_data.get("product_name", ""),
                        "product_url": url,
                        "codes": product_data.get("codes", []),
                        "skus": product_data.get("skus", []),
                        "categories": product_data.get("categories", []),
                        "tags": product_data.get("tags", []),
                        "sizes": product_data.get("sizes", []),
                        "specifications": product_data.get("specifications", {}),
                        "key_benefits": product_data.get("key_benefits", []),
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    # Add description if available
                    if product_data.get("description"):
                        formatted_data["description"] = product_data["description"]
                    
                    return formatted_data
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error for {url}: {e}")
                    return None
            else:
                print(f"❌ Failed to scrape {url}: {result.error_message}")
                return None
                
        except Exception as e:
            print(f"❌ Exception scraping {url}: {e}")
            return None
    
    async def scrape_batch(self, batch_urls: List[str], batch_num: int, total_batches: int) -> Dict[str, Any]:
        """Scrape a batch of URLs."""
        print(f"\n🔄 Processing Batch {batch_num}/{total_batches} ({len(batch_urls)} URLs)")
        
        batch_start = datetime.now()
        batch_results = []
        
        # Create extraction strategy
        extraction_strategy = self._create_extraction_strategy()
        
        # Initialize crawler
        async with AsyncWebCrawler(verbose=True) as crawler:
            # Process each URL in the batch
            for i, url in enumerate(batch_urls, 1):
                print(f"   🎯 Scraping {i}/{len(batch_urls)}: {url}")
                
                product_data = await self.scrape_product(url, crawler, extraction_strategy)
                if product_data:
                    batch_results.append(product_data)
                    
                    # Save individual product file
                    product_slug = url.split('/')[-2]
                    product_file = f"{self.output_dir}/individual/{product_slug}.json"
                    os.makedirs(os.path.dirname(product_file), exist_ok=True)
                    
                    with open(product_file, 'w', encoding='utf-8') as f:
                        json.dump(product_data, f, indent=2, ensure_ascii=False)
                
                # Small delay between requests
                await asyncio.sleep(1.5)
        
        # Save batch results
        batch_file = f"{self.output_dir}/batch_{batch_num:03d}_results.json"
        batch_metadata = {
            "batch_metadata": {
                "batch_number": batch_num,
                "total_batches": total_batches,
                "processing_date": datetime.now().isoformat(),
                "urls_attempted": len(batch_urls),
                "products_extracted": len(batch_results),
                "success_rate": f"{(len(batch_results) / len(batch_urls)) * 100:.1f}%"
            },
            "products": batch_results
        }
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_metadata, f, indent=2, ensure_ascii=False)
        
        processing_time = (datetime.now() - batch_start).total_seconds()
        
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
    
    async def run_all_batches(self) -> Dict[str, Any]:
        """Process all batches."""
        print(f"\n🎬 Starting Docker batch processing of {self.total_urls} Agar products")
        print("=" * 60)
        
        overall_start = datetime.now()
        
        # Create batches
        batches = []
        for i in range(0, len(self.product_urls), self.batch_size):
            batch = self.product_urls[i:i + self.batch_size]
            batches.append(batch)
        
        print(f"📊 Created {len(batches)} batches")
        
        all_results = []
        all_products = []
        total_success = 0
        total_failed = 0
        
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
                print(f"⏸️  Pausing 5 seconds before next batch...")
                await asyncio.sleep(5)
        
        overall_time = (datetime.now() - overall_start).total_seconds()
        
        # Compile final results
        final_results = {
            "scraping_metadata": {
                "start_time": overall_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_processing_time": f"{overall_time:.1f}s",
                "total_urls_attempted": self.total_urls,
                "total_products_extracted": total_success,
                "total_failed": total_failed,
                "success_rate": f"{(total_success / self.total_urls) * 100:.1f}%",
                "batches_processed": len(batches),
                "batch_size": self.batch_size,
                "output_format": "Technical Brief v1.0 Schema",
                "environment": "Docker Container - Simplified"
            },
            "batch_results": all_results,
            "all_products_brief_schema": all_products
        }
        
        # Save master results
        master_file = f"{self.output_dir}/complete_agar_scraping_results.json"
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
        
        # Save products-only file
        products_only_file = f"{self.output_dir}/all_products_final.json"
        with open(products_only_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 DOCKER BATCH PROCESSING COMPLETE!")
        print("=" * 60)
        print(f"📊 Final Results:")
        print(f"   🎯 URLs processed: {self.total_urls}")
        print(f"   ✅ Products extracted: {total_success}")
        print(f"   ❌ Failed extractions: {total_failed}")
        print(f"   📈 Success rate: {(total_success / self.total_urls) * 100:.1f}%")
        print(f"   ⏱️  Total time: {overall_time/60:.1f} minutes")
        print(f"   📁 Master results: {master_file}")
        print(f"   📄 Products only: {products_only_file}")
        
        return final_results

async def main():
    """Main execution function."""
    urls_file = "/app/complete_agar_product_urls_20251008_122301.json"
    
    if not os.path.exists(urls_file):
        print(f"❌ URLs file not found: {urls_file}")
        return
    
    # Initialize and run batch scraper
    scraper = SimplifiedDockerBatchScraper(urls_file=urls_file, batch_size=8)
    results = await scraper.run_all_batches()
    
    print(f"\n🏁 All batches completed!")

if __name__ == "__main__":
    print("🐳 Simplified Docker Agar Product Batch Scraper")
    print("Using core Crawl4AI with LLM extraction")
    print("=" * 60)
    
    asyncio.run(main())
