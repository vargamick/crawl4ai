"""
Main Agar scraper orchestrator.

This module provides the main AgarScraper class that coordinates all the different
components to perform the complete product catalog scraping process.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from .schemas import (
    ScrapingConfig, AgarCatalogData, ProductSchema, MediaSchema, 
    DocumentSchema, CategorySchema, ProductCategoryRelation
)
from .product_extractor import ProductExtractor
from .media_processor import MediaProcessor
from .document_handler import DocumentHandler
from .category_mapper import CategoryMapper
from .json_normalizer import JSONNormalizer


class AgarScraper:
    """
    Main orchestrator for Agar product catalog scraping using crawl4ai.
    """
    
    def __init__(self, config: ScrapingConfig):
        """
        Initialize the AgarScraper with configuration.
        
        Args:
            config: Scraping configuration
        """
        self.config = config
        
        # Initialize all components
        self.product_extractor = ProductExtractor(config)
        self.media_processor = MediaProcessor(config)
        self.document_handler = DocumentHandler(config)
        self.category_mapper = CategoryMapper(config)
        self.json_normalizer = JSONNormalizer(config.output_dir)
        
        # Storage for extracted data
        self.all_products = []
        self.all_media = []
        self.all_documents = []
        self.all_categories = []
        self.all_product_categories = []
    
    async def run_complete_scraping(self, base_url: Optional[str] = None) -> AgarCatalogData:
        """
        Run the complete scraping process.
        
        Args:
            base_url: Optional base URL override
            
        Returns:
            Complete normalized catalog data
        """
        start_time = datetime.now()
        
        if self.config.verbose:
            print(f"Starting Agar product catalog scraping...")
            print(f"Configuration:")
            print(f"  Base URL: {base_url or self.config.base_url}")
            print(f"  Max products: {self.config.max_products or 'unlimited'}")
            print(f"  Include images: {self.config.include_images}")
            print(f"  Include documents: {self.config.include_documents}")
            print(f"  Include categories: {self.config.include_categories}")
            print(f"  Output directory: {self.config.output_dir}")
            print(f"  Delay: {self.config.delay_seconds}s")
            print()
        
        try:
            # Step 1: Extract products
            products = await self._extract_products(base_url)
            if not products:
                print("No products extracted. Exiting.")
                return self._create_empty_catalog()
            
            # Step 2: Process media, documents, and categories for each product
            await self._process_product_details(products)
            
            # Step 3: Post-process and deduplicate
            self._post_process_data()
            
            # Step 4: Create normalized catalog
            catalog_data = self._create_catalog_data()
            
            # Step 5: Save outputs
            await self._save_outputs(catalog_data)
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if self.config.verbose:
                print(f"\nScraping completed successfully!")
                print(f"Duration: {duration:.1f} seconds")
                print(f"Products extracted: {len(self.all_products)}")
                print(f"Media items: {len(self.all_media)}")
                print(f"Documents: {len(self.all_documents)}")
                print(f"Categories: {len(self.all_categories)}")
                print(f"Product-category relationships: {len(self.all_product_categories)}")
            
            return catalog_data
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            raise
    
    async def _extract_products(self, base_url: Optional[str] = None) -> List[ProductSchema]:
        """
        Extract products using the ProductExtractor.
        
        Args:
            base_url: Optional base URL override
            
        Returns:
            List of extracted products
        """
        if self.config.verbose:
            print("Step 1: Extracting products...")
        
        products = await self.product_extractor.run_extraction(base_url)
        self.all_products = products
        
        if self.config.verbose:
            print(f"  Extracted {len(products)} products")
        
        return products
    
    async def _process_product_details(self, products: List[ProductSchema]) -> None:
        """
        Process media, documents, and categories for all products.
        
        Args:
            products: List of products to process
        """
        if self.config.verbose:
            print("Step 2: Processing product details (media, documents, categories)...")
        
        for i, product in enumerate(products, 1):
            if self.config.verbose:
                print(f"  Processing product {i}/{len(products)}: {product.product_name}")
            
            # Get raw extracted data from metadata
            raw_data = product.metadata.get("raw_extracted_data", {})
            
            # Process media
            if self.config.include_images:
                media_items = await self.media_processor.extract_media_from_product(product, raw_data)
                if media_items:
                    # Enhance media with additional metadata
                    enhanced_media = await self.media_processor.enhance_media_metadata(media_items)
                    self.all_media.extend(enhanced_media)
            
            # Process documents
            if self.config.include_documents:
                documents = self.document_handler.extract_documents_from_product(product, raw_data)
                self.all_documents.extend(documents)
            
            # Process categories
            if self.config.include_categories:
                categories, relationships = self.category_mapper.extract_categories_from_product(product, raw_data)
                self.all_categories.extend(categories)
                self.all_product_categories.extend(relationships)
            
            # Rate limiting
            if i < len(products):
                await asyncio.sleep(self.config.delay_seconds)
    
    def _post_process_data(self) -> None:
        """
        Post-process all extracted data to remove duplicates and normalize.
        """
        if self.config.verbose:
            print("Step 3: Post-processing data...")
        
        # Remove duplicate media items
        if self.all_media:
            original_count = len(self.all_media)
            self.all_media = self.media_processor.filter_duplicate_media(self.all_media)
            self.all_media = self.media_processor.sort_media_by_sequence(self.all_media)
            
            if self.config.verbose and original_count != len(self.all_media):
                print(f"  Removed {original_count - len(self.all_media)} duplicate media items")
        
        # Remove duplicate categories
        if self.all_categories:
            original_count = len(self.all_categories)
            self.all_categories = self.category_mapper.deduplicate_categories(self.all_categories)
            self.all_categories = self.category_mapper.sort_categories_by_hierarchy(self.all_categories)
            
            if self.config.verbose and original_count != len(self.all_categories):
                print(f"  Removed {original_count - len(self.all_categories)} duplicate categories")
        
        # Remove duplicate product-category relationships
        if self.all_product_categories:
            original_count = len(self.all_product_categories)
            seen_relationships = set()
            unique_relationships = []
            
            for rel in self.all_product_categories:
                rel_key = (rel.product_id, rel.category_id)
                if rel_key not in seen_relationships:
                    seen_relationships.add(rel_key)
                    unique_relationships.append(rel)
            
            self.all_product_categories = unique_relationships
            
            if self.config.verbose and original_count != len(self.all_product_categories):
                print(f"  Removed {original_count - len(self.all_product_categories)} duplicate relationships")
    
    def _create_catalog_data(self) -> AgarCatalogData:
        """
        Create the normalized catalog data structure.
        
        Returns:
            Normalized catalog data
        """
        if self.config.verbose:
            print("Step 4: Creating normalized catalog structure...")
        
        catalog_data = self.json_normalizer.normalize_catalog_data(
            products=self.all_products,
            media=self.all_media,
            documents=self.all_documents,
            categories=self.all_categories,
            product_categories=self.all_product_categories
        )
        
        return catalog_data
    
    async def _save_outputs(self, catalog_data: AgarCatalogData) -> None:
        """
        Save all output files.
        
        Args:
            catalog_data: Catalog data to save
        """
        if self.config.verbose:
            print("Step 5: Saving output files...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save normalized JSON files
        saved_files = self.json_normalizer.save_normalized_files(
            catalog_data=catalog_data,
            separate_files=True,
            combined_file=True,
            filename_prefix=f"agar_"
        )
        
        # Save legacy format for backward compatibility
        legacy_file = self.json_normalizer.save_legacy_format(
            catalog_data=catalog_data,
            filename_prefix=f"agar_"
        )
        saved_files["legacy"] = legacy_file
        
        # Save summary report
        summary_file = self.json_normalizer.save_summary_report(
            catalog_data=catalog_data,
            filename_prefix=f"agar_"
        )
        saved_files["summary"] = summary_file
        
        if self.config.verbose:
            print(f"  Saved files:")
            for file_type, filepath in saved_files.items():
                print(f"    {file_type}: {filepath}")
    
    def _create_empty_catalog(self) -> AgarCatalogData:
        """
        Create an empty catalog data structure.
        
        Returns:
            Empty catalog data
        """
        return self.json_normalizer.normalize_catalog_data(
            products=[],
            media=[],
            documents=[],
            categories=[],
            product_categories=[]
        )
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the extraction results.
        
        Returns:
            Dictionary with extraction statistics
        """
        return {
            "total_products": len(self.all_products),
            "total_media": len(self.all_media),
            "total_documents": len(self.all_documents),
            "total_categories": len(self.all_categories),
            "total_relationships": len(self.all_product_categories),
            "products_with_media": len(set(m.product_id for m in self.all_media)),
            "products_with_documents": len(set(d.product_id for d in self.all_documents)),
            "products_with_categories": len(set(r.product_id for r in self.all_product_categories)),
        }
    
    async def scrape_single_product(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single product for testing purposes.
        
        Args:
            product_url: URL of the product to scrape
            
        Returns:
            Dictionary with product data or None if failed
        """
        try:
            # Extract product
            product = await self.product_extractor.extract_product(product_url)
            if not product:
                return None
            
            # Get raw data
            raw_data = product.metadata.get("raw_extracted_data", {})
            
            # Extract media, documents, categories
            media_items = await self.media_processor.extract_media_from_product(product, raw_data)
            documents = self.document_handler.extract_documents_from_product(product, raw_data)
            categories, relationships = self.category_mapper.extract_categories_from_product(product, raw_data)
            
            return {
                "product": product.dict(),
                "media": [m.dict() for m in media_items],
                "documents": [d.dict() for d in documents],
                "categories": [c.dict() for c in categories],
                "relationships": [r.dict() for r in relationships],
            }
            
        except Exception as e:
            if self.config.verbose:
                print(f"Error scraping single product {product_url}: {e}")
            return None
