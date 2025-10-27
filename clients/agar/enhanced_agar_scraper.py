"""
Enhanced Agar Scraper implementing Technical Brief v1.0 requirements.

This is the main integration script that combines:
- Enhanced product extraction with modal handling and tab navigation
- Markdown generation per brief template specifications  
- JSON output matching exact brief schema
- Integration with existing discovered product URLs
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .schemas import ScrapingConfig, ProductSchema
from .enhanced_product_extractor import EnhancedProductExtractor
from .markdown_generator import MarkdownGenerator
from .utils import load_discovered_urls


class EnhancedAgarScraper:
    """
    Main scraper orchestrator implementing Technical Brief v1.0 requirements.
    """
    
    def __init__(self, config: ScrapingConfig):
        """
        Initialize the Enhanced Agar Scraper.
        
        Args:
            config: Scraping configuration
        """
        self.config = config
        self.extractor = EnhancedProductExtractor(config)
        self.markdown_generator = MarkdownGenerator(config.output_dir)
        
        # Ensure output directory exists
        os.makedirs(config.output_dir, exist_ok=True)
    
    async def scrape_from_discovered_urls(self, urls_file: str) -> Dict[str, Any]:
        """
        Scrape products using pre-discovered URLs file.
        
        Args:
            urls_file: Path to JSON file containing discovered URLs
            
        Returns:
            Dictionary with scraping results and metadata
        """
        if self.config.verbose:
            print(f"Loading discovered URLs from: {urls_file}")
        
        # Load discovered URLs
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                urls_data = json.load(f)
            
            product_urls = urls_data.get("all_product_urls", [])
            
            if self.config.verbose:
                print(f"Loaded {len(product_urls)} product URLs")
        
        except Exception as e:
            print(f"Error loading URLs file {urls_file}: {e}")
            return {"success": False, "error": str(e)}
        
        # Apply max_products limit if specified
        if self.config.max_products and len(product_urls) > self.config.max_products:
            product_urls = product_urls[:self.config.max_products]
            if self.config.verbose:
                print(f"Limited to {len(product_urls)} products per config")
        
        return await self._scrape_products(product_urls, urls_data.get("metadata", {}))
    
    async def scrape_sample_products(self) -> Dict[str, Any]:
        """
        Scrape the sample products mentioned in the technical brief for testing.
        
        Returns:
            Dictionary with scraping results
        """
        # Sample URLs from technical brief
        sample_urls = [
            "https://agar.com.au/product/everfresh/",
            "https://agar.com.au/product/stone-block/",
            "https://agar.com.au/product/ultrastrip/",
            "https://agar.com.au/product/first-base/"  # Additional sample
        ]
        
        if self.config.verbose:
            print(f"Scraping {len(sample_urls)} sample products for testing")
        
        return await self._scrape_products(sample_urls, {"source": "sample_products"})
    
    async def _scrape_products(self, product_urls: List[str], source_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to scrape products and generate outputs.
        
        Args:
            product_urls: List of product URLs to scrape
            source_metadata: Metadata about the source of URLs
            
        Returns:
            Dictionary with scraping results and file paths
        """
        start_time = datetime.now()
        
        if self.config.verbose:
            print(f"Starting enhanced scraping of {len(product_urls)} products...")
        
        # Extract products using enhanced extractor
        products = await self.extractor.extract_products_from_urls(product_urls)
        
        if not products:
            return {
                "success": False,
                "message": "No products were successfully extracted",
                "total_attempted": len(product_urls),
                "total_extracted": 0
            }
        
        # Generate outputs
        results = {
            "success": True,
            "scraping_metadata": {
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_urls_attempted": len(product_urls),
                "total_products_extracted": len(products),
                "success_rate": f"{(len(products) / len(product_urls)) * 100:.1f}%",
                "source_metadata": source_metadata,
                "brief_compliance": "v1.0"
            },
            "products": products,
            "output_files": {}
        }
        
        # Generate JSON outputs per brief specifications
        json_files = await self._generate_json_outputs(products, results["scraping_metadata"])
        results["output_files"].update(json_files)
        
        # Generate Markdown outputs per brief specifications
        if self.config.verbose:
            print("Generating Markdown documentation...")
        
        markdown_files = self.markdown_generator.generate_all_markdown(products)
        results["output_files"].update(markdown_files)
        
        # Generate index file per brief specifications
        index_file = await self._generate_index_file(results)
        results["output_files"]["index.json"] = index_file
        
        if self.config.verbose:
            print(f"Enhanced scraping completed successfully!")
            print(f"- Products extracted: {len(products)}")
            print(f"- JSON files: {len([f for f in results['output_files'] if f.endswith('.json')])}")
            print(f"- Markdown files: {len([f for f in results['output_files'] if f.endswith('.md')])}")
            print(f"- Output directory: {self.config.output_dir}")
        
        return results
    
    async def _generate_json_outputs(self, products: List[ProductSchema], metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate JSON outputs matching technical brief schema requirements.
        
        Args:
            products: List of extracted products
            metadata: Scraping metadata
            
        Returns:
            Dictionary mapping output types to file paths
        """
        output_files = {}
        
        # Generate individual product JSON files per brief structure
        for product in products:
            try:
                # Create product-specific directory structure
                product_url_path = str(product.product_url).split('/')[-2]
                product_dir = os.path.join(self.config.output_dir, "products", product_url_path)
                os.makedirs(product_dir, exist_ok=True)
                
                # Convert product to JSON format matching brief schema
                product_json = self._product_to_brief_schema(product)
                
                # Save individual product JSON
                product_json_path = os.path.join(product_dir, f"{product_url_path}.json")
                with open(product_json_path, 'w', encoding='utf-8') as f:
                    json.dump(product_json, f, indent=2, ensure_ascii=False, default=str)
                
                output_files[f"products/{product_url_path}.json"] = product_json_path
                
            except Exception as e:
                if self.config.verbose:
                    print(f"Error generating JSON for {product.product_name}: {e}")
        
        # Generate master products collection file
        all_products_json = [self._product_to_brief_schema(p) for p in products]
        master_json_path = os.path.join(self.config.output_dir, "all_products_brief_schema.json")
        
        master_data = {
            "scrape_date": metadata.get("start_time"),
            "total_products": len(products),
            "brief_compliance": "v1.0", 
            "products": all_products_json
        }
        
        with open(master_json_path, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=2, ensure_ascii=False, default=str)
        
        output_files["all_products_brief_schema.json"] = master_json_path
        
        return output_files
    
    def _product_to_brief_schema(self, product: ProductSchema) -> Dict[str, Any]:
        """
        Convert ProductSchema to exact technical brief JSON schema.
        
        Args:
            product: ProductSchema object
            
        Returns:
            Dictionary matching technical brief schema
        """
        metadata = product.metadata or {}
        
        # Build brief-compliant JSON structure
        brief_json = {
            "product_name": product.product_name,
            "product_url": str(product.product_url),
            "codes": metadata.get("codes", []),
            "skus": metadata.get("skus", []),
            "categories": metadata.get("categories", []),
            "tags": metadata.get("tags", []),
            "sizes": metadata.get("sizes", []),
            "specifications": metadata.get("specifications", {}),
            "key_benefits": metadata.get("key_benefits", []),
            "scraped_at": metadata.get("extraction_timestamp", datetime.now().isoformat())
        }
        
        # Add images if available
        raw_data = metadata.get("raw_extracted_data", {})
        if raw_data.get("product_images_src"):
            images_src = raw_data["product_images_src"]
            images_alt = raw_data.get("product_images_alt", [])
            
            if not isinstance(images_src, list):
                images_src = [images_src]
            if not isinstance(images_alt, list):
                images_alt = [images_alt] if images_alt else []
            
            brief_json["images"] = []
            for i, src in enumerate(images_src):
                if src:
                    image_data = {
                        "type": "main" if i == 0 else "gallery",
                        "url": src,
                        "alt_text": images_alt[i] if i < len(images_alt) else ""
                    }
                    brief_json["images"].append(image_data)
        
        # Add documents if available
        documents = metadata.get("documents", [])
        if documents:
            brief_json["documents"] = documents
        
        # Add description structure
        if product.description:
            description_obj = {"overview": product.description}
            
            # Try to extract structured description sections
            raw_desc = raw_data.get("description_content", "")
            if raw_desc:
                if "how does it work" in raw_desc.lower():
                    # Extract how it works section
                    description_obj["how_it_works"] = raw_desc  # Simplified for now
                if "for use on" in raw_desc.lower() or "applications" in raw_desc.lower():
                    description_obj["applications"] = raw_desc  # Simplified for now
            
            brief_json["description"] = description_obj
        
        # Add reviews if available
        reviews = metadata.get("reviews", {})
        if reviews and (reviews.get("rating") or reviews.get("count", 0) > 0):
            brief_json["reviews"] = reviews
        
        return brief_json
    
    async def _generate_index_file(self, scraping_results: Dict[str, Any]) -> str:
        """
        Generate index.json file per technical brief specifications.
        
        Args:
            scraping_results: Complete scraping results
            
        Returns:
            Path to generated index file
        """
        products = scraping_results["products"]
        metadata = scraping_results["scraping_metadata"]
        
        # Build index structure per brief requirements
        index_data = {
            "scrape_date": metadata.get("start_time"),
            "total_products": len(products),
            "successful": len(products),
            "failed": metadata.get("total_urls_attempted", 0) - len(products),
            "products": []
        }
        
        # Add product entries
        for product in products:
            product_url_path = str(product.product_url).split('/')[-2]
            
            product_entry = {
                "name": product.product_name,
                "url": str(product.product_url),
                "status": "success",
                "files": {
                    "json": f"products/{product_url_path}/{product_url_path}.json",
                    "markdown": f"products/{product_url_path}/{product_url_path}.md"
                }
            }
            index_data["products"].append(product_entry)
        
        # Save index file
        index_path = os.path.join(self.config.output_dir, "index.json")
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False, default=str)
        
        return index_path


async def run_enhanced_scraping(
    urls_file: Optional[str] = None,
    max_products: Optional[int] = None,
    output_dir: str = "output",
    verbose: bool = True,
    sample_only: bool = False
) -> Dict[str, Any]:
    """
    Main function to run enhanced Agar scraping per technical brief.
    
    Args:
        urls_file: Path to discovered URLs JSON file
        max_products: Maximum number of products to scrape
        output_dir: Output directory for results
        verbose: Enable verbose logging
        sample_only: Only scrape sample products for testing
        
    Returns:
        Dictionary with scraping results
    """
    # Configure scraping
    config = ScrapingConfig(
        base_url="https://agar.com.au",
        max_products=max_products,
        delay_seconds=2.0,  # Respectful delay
        output_dir=output_dir,
        verbose=verbose,
        include_images=True,
        include_documents=True,
        include_categories=True
    )
    
    # Initialize enhanced scraper
    scraper = EnhancedAgarScraper(config)
    
    if sample_only:
        # Scrape sample products for testing
        results = await scraper.scrape_sample_products()
    elif urls_file:
        # Use provided URLs file
        results = await scraper.scrape_from_discovered_urls(urls_file)
    else:
        # Look for default URLs file
        default_urls_file = "complete_agar_product_urls_20251008_122301.json"
        if os.path.exists(default_urls_file):
            results = await scraper.scrape_from_discovered_urls(default_urls_file)
        else:
            # Fallback to sample products
            print("No URLs file found, using sample products")
            results = await scraper.scrape_sample_products()
    
    return results


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    # Parse basic command line arguments
    sample_only = "--sample" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    max_products = None
    if "--max" in sys.argv:
        idx = sys.argv.index("--max")
        if idx + 1 < len(sys.argv):
            try:
                max_products = int(sys.argv[idx + 1])
            except ValueError:
                pass
    
    print("Enhanced Agar Scraper - Technical Brief v1.0 Implementation")
    print("=" * 60)
    
    # Run scraping
    results = asyncio.run(run_enhanced_scraping(
        sample_only=sample_only,
        max_products=max_products,
        verbose=verbose
    ))
    
    if results.get("success"):
        print("\n✅ Scraping completed successfully!")
        print(f"📊 Products extracted: {results['scraping_metadata']['total_products_extracted']}")
        print(f"📁 Output directory: {results.get('scraping_metadata', {}).get('output_dir', 'output')}")
        print(f"⏱️  Duration: {results['scraping_metadata'].get('end_time', '')}")
    else:
        print(f"\n❌ Scraping failed: {results.get('message', 'Unknown error')}")
        sys.exit(1)
