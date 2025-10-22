#!/usr/bin/env python3
"""
Batch Processing Script for Agar Product URLs
Scrapes all products from complete_agar_product_urls_20251008_122301.json using the Enhanced Agar Scraper.
Generates output in the exact format requested by the user.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time

# Add the crawl4ai directory to the path
sys.path.insert(0, 'crawl4ai')

from crawl4ai.agar.schemas import ScrapingConfig
from crawl4ai.agar.enhanced_agar_scraper import EnhancedAgarScraper

class BatchAgarScraper:
    """
    Batch processor for scraping all Agar products with enhanced output formatting.
    """
    
    def __init__(self, urls_file: str, batch_size: int = 15, output_dir: str = "agar_batch_output"):
        """
        Initialize batch scraper.
        
        Args:
            urls_file: Path to the JSON file containing product URLs
            batch_size: Number of URLs to process per batch
            output_dir: Directory for output files
        """
        self.urls_file = urls_file
        self.batch_size = batch_size
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load URLs
        self.product_urls = self._load_urls()
        self.total_urls = len(self.product_urls)
        
        print(f"🚀 Batch Agar Scraper Initialized")
        print(f"📁 URLs file: {urls_file}")
        print(f"🎯 Total URLs to scrape: {self.total_urls}")
        print(f"📦 Batch size: {batch_size}")
        print(f"📂 Output directory: {output_dir}")
        
    def _load_urls(self) -> List[str]:
        """Load product URLs from JSON file."""
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            urls = data.get("all_product_urls", [])
            print(f"✅ Loaded {len(urls)} product URLs from {self.urls_file}")
            return urls
            
        except Exception as e:
            print(f"❌ Error loading URLs file: {e}")
            return []
    
    def _create_batches(self) -> List[List[str]]:
        """Split URLs into batches."""
        batches = []
        for i in range(0, len(self.product_urls), self.batch_size):
            batch = self.product_urls[i:i + self.batch_size]
            batches.append(batch)
        
        print(f"📊 Created {len(batches)} batches of max {self.batch_size} URLs each")
        return batches
    
    async def scrape_batch(self, batch_urls: List[str], batch_num: int, total_batches: int) -> Dict[str, Any]:
        """
        Scrape a single batch of URLs.
        
        Args:
            batch_urls: List of URLs for this batch
            batch_num: Current batch number (1-indexed)
            total_batches: Total number of batches
            
        Returns:
            Batch results dictionary
        """
        print(f"\n🔄 Processing Batch {batch_num}/{total_batches} ({len(batch_urls)} URLs)")
        print(f"🎯 URLs: {batch_urls[0]}...{batch_urls[-1] if len(batch_urls) > 1 else ''}")
        
        # Create config for this batch
        config = ScrapingConfig(
            base_url="https://agar.com.au",
            max_products=len(batch_urls),
            delay_seconds=1.5,  # Respectful delay
            output_dir=f"{self.output_dir}/batch_{batch_num:03d}",
            verbose=True,
            include_images=True,
            include_documents=True,
            include_categories=True
        )
        
        # Initialize scraper
        scraper = EnhancedAgarScraper(config)
        
        # Process batch
        batch_start = datetime.now()
        try:
            # Manually extract products for this batch
            products = await scraper.extractor.extract_products_from_urls(batch_urls)
            
            if not products:
                print(f"⚠️  Batch {batch_num}: No products extracted")
                return {
                    "batch_num": batch_num,
                    "success": False,
                    "urls_attempted": len(batch_urls),
                    "products_extracted": 0,
                    "processing_time": 0,
                    "error": "No products extracted"
                }
            
            # Generate outputs in the exact format requested
            batch_results = []
            for product in products:
                # Convert to the exact brief schema format
                product_json = scraper._product_to_brief_schema(product)
                batch_results.append(product_json)
                
                # Save individual product file
                product_slug = str(product.product_url).split('/')[-2]
                product_file = f"{config.output_dir}/individual/{product_slug}.json"
                os.makedirs(os.path.dirname(product_file), exist_ok=True)
                
                with open(product_file, 'w', encoding='utf-8') as f:
                    json.dump(product_json, f, indent=2, ensure_ascii=False, default=str)
            
            # Save batch results
            batch_file = f"{config.output_dir}/batch_{batch_num:03d}_results.json"
            batch_data = {
                "batch_metadata": {
                    "batch_number": batch_num,
                    "total_batches": total_batches,
                    "processing_date": datetime.now().isoformat(),
                    "urls_attempted": len(batch_urls),
                    "products_extracted": len(products),
                    "success_rate": f"{(len(products) / len(batch_urls)) * 100:.1f}%"
                },
                "products": batch_results
            }
            
            with open(batch_file, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, indent=2, ensure_ascii=False, default=str)
            
            processing_time = (datetime.now() - batch_start).total_seconds()
            
            print(f"✅ Batch {batch_num} completed:")
            print(f"   📊 Products extracted: {len(products)}/{len(batch_urls)}")
            print(f"   ⏱️  Processing time: {processing_time:.1f}s")
            print(f"   💾 Saved to: {batch_file}")
            
            return {
                "batch_num": batch_num,
                "success": True,
                "urls_attempted": len(batch_urls),
                "products_extracted": len(products),
                "processing_time": processing_time,
                "output_file": batch_file,
                "products": batch_results
            }
            
        except Exception as e:
            processing_time = (datetime.now() - batch_start).total_seconds()
            print(f"❌ Batch {batch_num} failed: {e}")
            
            return {
                "batch_num": batch_num,
                "success": False,
                "urls_attempted": len(batch_urls),
                "products_extracted": 0,
                "processing_time": processing_time,
                "error": str(e)
            }
    
    async def run_all_batches(self) -> Dict[str, Any]:
        """
        Process all batches and compile final results.
        
        Returns:
            Complete scraping results
        """
        print(f"\n🎬 Starting batch processing of {self.total_urls} Agar products")
        print(f"=" * 60)
        
        overall_start = datetime.now()
        batches = self._create_batches()
        
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
            
            # Brief pause between batches to be respectful
            if i < len(batches):
                print(f"⏸️  Pausing 3 seconds before next batch...")
                await asyncio.sleep(3)
        
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
                "source_file": self.urls_file
            },
            "batch_results": all_results,
            "all_products_brief_schema": all_products
        }
        
        # Save master results file
        master_file = f"{self.output_dir}/complete_agar_scraping_results.json"
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save products-only file in exact requested format
        products_only_file = f"{self.output_dir}/all_products_final.json"
        with open(products_only_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n🎉 BATCH PROCESSING COMPLETE!")
        print(f"=" * 60)
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
    urls_file = "complete_agar_product_urls_20251008_122301.json"
    
    if not os.path.exists(urls_file):
        print(f"❌ URLs file not found: {urls_file}")
        return
    
    # Initialize and run batch scraper
    batch_scraper = BatchAgarScraper(
        urls_file=urls_file,
        batch_size=15,  # Process 15 URLs per batch for manageable chunks
        output_dir="agar_batch_output"
    )
    
    # Run all batches
    results = await batch_scraper.run_all_batches()
    
    print(f"\n🏁 All batches completed successfully!")
    print(f"📊 Check the output directory for results: agar_batch_output/")

if __name__ == "__main__":
    print("🧪 Agar Product Batch Scraper")
    print("Using Enhanced Agar Scraper with Technical Brief v1.0 Schema")
    print("=" * 60)
    
    # Run the batch processing
    asyncio.run(main())
