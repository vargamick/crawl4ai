"""
Product extraction system for Agar catalog scraping.

This module handles the core product information extraction using crawl4ai's
AsyncWebCrawler and various extraction strategies.
"""

import asyncio
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy
from crawl4ai.extraction_strategy import ExtractionStrategy

from .schemas import ProductSchema, ScrapingConfig
from .utils import generate_product_id, clean_text, extract_urls_from_text


class ProductExtractor:
    """
    Handles product information extraction from Agar website pages.
    """
    
    def __init__(self, config: ScrapingConfig):
        """
        Initialize the ProductExtractor.
        
        Args:
            config: Scraping configuration
        """
        self.config = config
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=config.verbose
        )
        
        # Define CSS selectors for Agar product pages
        self.product_extraction_schema = {
            "name": "agar_products",
            "baseSelector": "body",
            "fields": [
                {
                    "name": "product_title",
                    "selector": "h1.product_title, .product-title h1, .entry-title",
                    "type": "text"
                },
                {
                    "name": "product_description", 
                    "selector": ".product-description, .woocommerce-product-details__short-description, .product-short-description",
                    "type": "text"
                },
                {
                    "name": "product_content",
                    "selector": ".product-content, .woocommerce-tabs, #tab-description",
                    "type": "text"
                },
                {
                    "name": "product_images",
                    "selector": ".product-images img, .woocommerce-product-gallery img, .product-gallery img",
                    "type": "attribute",
                    "attribute": "src"
                },
                {
                    "name": "product_image_alts",
                    "selector": ".product-images img, .woocommerce-product-gallery img, .product-gallery img", 
                    "type": "attribute",
                    "attribute": "alt"
                },
                {
                    "name": "attachment_links",
                    "selector": "a[href*='.pdf'], a[href*='attachment'], .attachments a, .product-attachments a",
                    "type": "attribute", 
                    "attribute": "href"
                },
                {
                    "name": "attachment_texts",
                    "selector": "a[href*='.pdf'], a[href*='attachment'], .attachments a, .product-attachments a",
                    "type": "text"
                },
                {
                    "name": "categories",
                    "selector": ".product-categories a, .posted_in a, .product-meta .posted_in a",
                    "type": "text"
                },
                {
                    "name": "category_links",
                    "selector": ".product-categories a, .posted_in a, .product-meta .posted_in a",
                    "type": "attribute",
                    "attribute": "href"
                }
            ]
        }
        
        self.extraction_strategy = JsonCssExtractionStrategy(
            self.product_extraction_schema, 
            verbose=config.verbose
        )

    async def discover_product_urls(self, base_url: str) -> List[str]:
        """
        Discover all product URLs from the Agar website.
        
        Args:
            base_url: Starting URL for discovery
            
        Returns:
            List of discovered product URLs
        """
        product_urls = set()
        urls_to_process = [base_url]
        processed_urls = set()
        
        # Define selectors for different types of pages - FIXED for actual Agar HTML structure
        discovery_schema = {
            "name": "url_discovery",
            "baseSelector": "body", 
            "fields": [
                {
                    "name": "product_links",
                    "selector": ".woocommerce-LoopProduct-link, .woocommerce-loop-product__link, a[href*='/product/']",
                    "type": "attribute",
                    "attribute": "href"
                },
                {
                    "name": "category_links", 
                    "selector": ".product-category a, a[href*='/product-category/'], .cat-item a",
                    "type": "attribute",
                    "attribute": "href"
                },
                {
                    "name": "pagination_links",
                    "selector": ".pagination a, .page-numbers a, nav.woocommerce-pagination a",
                    "type": "attribute", 
                    "attribute": "href"
                }
            ]
        }
        
        discovery_strategy = JsonCssExtractionStrategy(discovery_schema, verbose=self.config.verbose)
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            while urls_to_process and len(processed_urls) < 50:  # Limit discovery to avoid infinite loops
                current_url = urls_to_process.pop(0)
                
                if current_url in processed_urls:
                    continue
                    
                processed_urls.add(current_url)
                
                if self.config.verbose:
                    print(f"Discovering URLs from: {current_url}")
                
                try:
                    run_config = CrawlerRunConfig(
                        extraction_strategy=discovery_strategy,
                        cache_mode="enabled"
                    )
                    
                    result = await crawler.arun(url=current_url, config=run_config)
                    
                    if result.extracted_content:
                        # Safe JSON parsing instead of dangerous eval()
                        try:
                            import json
                            extracted_data = json.loads(result.extracted_content)
                        except json.JSONDecodeError:
                            if self.config.verbose:
                                print(f"Failed to parse JSON from {current_url}")
                            continue
                        
                        # Debug: print extracted data structure
                        if self.config.verbose:
                            print(f"Extracted data type: {type(extracted_data)}")
                            print(f"Extracted data: {extracted_data}")
                        
                        # Handle different JSON structures
                        data_to_process = extracted_data
                        if isinstance(extracted_data, list) and len(extracted_data) > 0:
                            # If it's a list, take the first item
                            data_to_process = extracted_data[0] if isinstance(extracted_data[0], dict) else {}
                        elif not isinstance(extracted_data, dict):
                            # If it's not a dict or list, skip
                            continue
                        
                        # Process discovered links
                        for field_name in ["product_links", "category_links", "pagination_links"]:
                            link_list = data_to_process.get(field_name, [])
                            
                            # Handle both single values and lists
                            if not isinstance(link_list, list):
                                link_list = [link_list] if link_list else []
                            
                            for link in link_list:
                                if not link or not isinstance(link, str):
                                    continue
                                    
                                # Make absolute URL
                                abs_url = urljoin(current_url, link)
                                
                                # Check if it's a product URL
                                if '/product/' in abs_url and abs_url not in product_urls:
                                    product_urls.add(abs_url)
                                    if self.config.verbose:
                                        print(f"Found product URL: {abs_url}")
                                    
                                # Add to discovery queue if it's a category or pagination link
                                elif (('/product-category/' in abs_url or '/page/' in abs_url) 
                                      and abs_url not in processed_urls 
                                      and abs_url not in urls_to_process):
                                    urls_to_process.append(abs_url)
                                    if self.config.verbose:
                                        print(f"Added category URL to queue: {abs_url}")
                    
                    # Be respectful to the server
                    await asyncio.sleep(self.config.delay_seconds)
                    
                except Exception as e:
                    if self.config.verbose:
                        print(f"Error discovering URLs from {current_url}: {e}")
                    continue
        
        product_urls = list(product_urls)
        
        # Apply limit if specified
        if self.config.max_products and len(product_urls) > self.config.max_products:
            product_urls = product_urls[:self.config.max_products]
        
        if self.config.verbose:
            print(f"Discovered {len(product_urls)} product URLs")
            
        return product_urls

    async def extract_product(self, product_url: str) -> Optional[ProductSchema]:
        """
        Extract product information from a single product page.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            ProductSchema object or None if extraction fails
        """
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            try:
                run_config = CrawlerRunConfig(
                    extraction_strategy=self.extraction_strategy,
                    cache_mode="enabled"
                )
                
                result = await crawler.arun(url=product_url, config=run_config)
                
                if not result.extracted_content:
                    if self.config.verbose:
                        print(f"No content extracted from {product_url}")
                    return None
                
                # Safe JSON parsing instead of dangerous eval()
                try:
                    import json
                    extracted_data = json.loads(result.extracted_content)
                except json.JSONDecodeError:
                    if self.config.verbose:
                        print(f"Failed to parse JSON from {product_url}")
                    return None
                
                # Handle different JSON structures (same as in discover_product_urls)
                data_to_process = extracted_data
                if isinstance(extracted_data, list) and len(extracted_data) > 0:
                    # If it's a list, take the first item
                    data_to_process = extracted_data[0] if isinstance(extracted_data[0], dict) else {}
                elif not isinstance(extracted_data, dict):
                    # If it's not a dict or list, skip
                    if self.config.verbose:
                        print(f"Unexpected data structure from {product_url}: {type(extracted_data)}")
                    return None
                
                # Generate product ID from URL
                product_id = generate_product_id(product_url)
                
                # Extract and clean product name
                product_name = clean_text(data_to_process.get("product_title", ""))
                if not product_name:
                    # Fallback: extract from URL or HTML title
                    product_name = urlparse(product_url).path.split('/')[-2].replace('-', ' ').title()
                
                # Combine descriptions
                description_parts = []
                if data_to_process.get("product_description"):
                    description_parts.append(clean_text(data_to_process["product_description"]))
                if data_to_process.get("product_content"):
                    description_parts.append(clean_text(data_to_process["product_content"]))
                
                description = " ".join(description_parts) if description_parts else None
                
                # Create ProductSchema
                product = ProductSchema(
                    product_id=product_id,
                    product_name=product_name,
                    product_url=product_url,
                    description=description,
                    metadata={
                        "raw_extracted_data": data_to_process,
                        "original_data_structure": str(type(extracted_data)),
                        "extraction_timestamp": datetime.now().isoformat()
                    }
                )
                
                if self.config.verbose:
                    print(f"Extracted product: {product.product_name}")
                
                return product
                
            except Exception as e:
                if self.config.verbose:
                    print(f"Error extracting product from {product_url}: {e}")
                return None

    async def extract_products_batch(self, product_urls: List[str]) -> List[ProductSchema]:
        """
        Extract products in batch with concurrency control.
        
        Args:
            product_urls: List of product URLs to process
            
        Returns:
            List of successfully extracted ProductSchema objects
        """
        products = []
        
        # Process in batches to avoid overwhelming the server
        batch_size = 5
        for i in range(0, len(product_urls), batch_size):
            batch = product_urls[i:i + batch_size]
            
            if self.config.verbose:
                print(f"Processing batch {i//batch_size + 1}/{(len(product_urls) + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            tasks = [self.extract_product(url) for url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            for result in batch_results:
                if isinstance(result, ProductSchema):
                    products.append(result)
                elif isinstance(result, Exception) and self.config.verbose:
                    print(f"Batch processing error: {result}")
            
            # Delay between batches
            if i + batch_size < len(product_urls):
                await asyncio.sleep(self.config.delay_seconds * 2)
        
        if self.config.verbose:
            print(f"Successfully extracted {len(products)} products from {len(product_urls)} URLs")
        
        return products

    async def run_extraction(self, base_url: Optional[str] = None) -> List[ProductSchema]:
        """
        Run the complete product extraction process.
        
        Args:
            base_url: Optional base URL override
            
        Returns:
            List of extracted ProductSchema objects
        """
        start_url = base_url or str(self.config.base_url)
        
        if self.config.verbose:
            print(f"Starting product extraction from: {start_url}")
        
        # Step 1: Discover product URLs
        product_urls = await self.discover_product_urls(start_url)
        
        if not product_urls:
            print("No product URLs discovered")
            return []
        
        # Step 2: Extract products
        products = await self.extract_products_batch(product_urls)
        
        if self.config.verbose:
            print(f"Extraction complete: {len(products)} products extracted")
        
        return products
