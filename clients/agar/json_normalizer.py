"""
JSON normalizer for Agar product catalog data.

This module handles the conversion of extracted product data into the normalized
3DN JSON structure with separate files for each entity type.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .schemas import (
    AgarCatalogData, 
    ProductSchema, 
    MediaSchema, 
    DocumentSchema, 
    CategorySchema,
    ProductCategoryRelation
)
from .utils import ensure_directory, safe_filename


class JSONNormalizer:
    """
    Handles the normalization and output of product catalog data to JSON files.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the JSON normalizer.
        
        Args:
            output_dir: Directory to save JSON output files
        """
        self.output_dir = output_dir
        ensure_directory(output_dir)
    
    def normalize_catalog_data(
        self, 
        products: List[ProductSchema],
        media: List[MediaSchema],
        documents: List[DocumentSchema],
        categories: List[CategorySchema],
        product_categories: List[ProductCategoryRelation]
    ) -> AgarCatalogData:
        """
        Combine all data into a normalized catalog structure.
        
        Args:
            products: List of products
            media: List of media items
            documents: List of documents
            categories: List of categories
            product_categories: List of product-category relationships
            
        Returns:
            Complete normalized catalog data
        """
        catalog_data = AgarCatalogData(
            products=products,
            media=media,
            documents=documents,
            categories=categories,
            product_categories=product_categories,
            metadata={
                "created_at": datetime.now().isoformat(),
                "total_products": len(products),
                "total_media": len(media),
                "total_documents": len(documents),
                "total_categories": len(categories),
                "total_relationships": len(product_categories),
                "generator": "crawl4ai-agar-scraper",
                "version": "1.0.0"
            }
        )
        
        return catalog_data
    
    def save_normalized_files(
        self, 
        catalog_data: AgarCatalogData,
        separate_files: bool = True,
        combined_file: bool = True,
        filename_prefix: str = ""
    ) -> Dict[str, str]:
        """
        Save normalized data to JSON files.
        
        Args:
            catalog_data: Normalized catalog data
            separate_files: Whether to save separate files for each entity type
            combined_file: Whether to save a combined file with all data
            filename_prefix: Optional prefix for filenames
            
        Returns:
            Dictionary mapping file types to their saved paths
        """
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Helper function to save JSON
        def save_json(data: Any, filename: str) -> str:
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=self._json_serializer
                )
            return filepath
        
        # Save separate files for each entity type
        if separate_files:
            # Products
            if catalog_data.products:
                filename = f"{filename_prefix}products_{timestamp}.json" if filename_prefix else f"products_{timestamp}.json"
                products_data = [product.dict() for product in catalog_data.products]
                saved_files["products"] = save_json(products_data, filename)
            
            # Media
            if catalog_data.media:
                filename = f"{filename_prefix}media_{timestamp}.json" if filename_prefix else f"media_{timestamp}.json"
                media_data = [media.dict() for media in catalog_data.media]
                saved_files["media"] = save_json(media_data, filename)
            
            # Documents
            if catalog_data.documents:
                filename = f"{filename_prefix}documents_{timestamp}.json" if filename_prefix else f"documents_{timestamp}.json"
                documents_data = [doc.dict() for doc in catalog_data.documents]
                saved_files["documents"] = save_json(documents_data, filename)
            
            # Categories
            if catalog_data.categories:
                filename = f"{filename_prefix}categories_{timestamp}.json" if filename_prefix else f"categories_{timestamp}.json"
                categories_data = [cat.dict() for cat in catalog_data.categories]
                saved_files["categories"] = save_json(categories_data, filename)
            
            # Product-Category relationships
            if catalog_data.product_categories:
                filename = f"{filename_prefix}product_categories_{timestamp}.json" if filename_prefix else f"product_categories_{timestamp}.json"
                relationships_data = [rel.dict() for rel in catalog_data.product_categories]
                saved_files["product_categories"] = save_json(relationships_data, filename)
        
        # Save combined file
        if combined_file:
            filename = f"{filename_prefix}catalog_complete_{timestamp}.json" if filename_prefix else f"catalog_complete_{timestamp}.json"
            combined_data = catalog_data.dict()
            saved_files["combined"] = save_json(combined_data, filename)
        
        return saved_files
    
    def save_legacy_format(
        self, 
        catalog_data: AgarCatalogData,
        filename_prefix: str = ""
    ) -> str:
        """
        Save data in legacy format for backward compatibility with existing Agar tools.
        
        Args:
            catalog_data: Normalized catalog data
            filename_prefix: Optional prefix for filename
            
        Returns:
            Path to saved legacy format file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}catalog_legacy_{timestamp}.json" if filename_prefix else f"catalog_legacy_{timestamp}.json"
        
        # Convert to legacy format
        legacy_data = []
        
        # Create lookup dictionaries
        media_by_product = {}
        documents_by_product = {}
        categories_by_product = {}
        
        for media in catalog_data.media:
            if media.product_id not in media_by_product:
                media_by_product[media.product_id] = []
            media_by_product[media.product_id].append(media)
        
        for document in catalog_data.documents:
            if document.product_id not in documents_by_product:
                documents_by_product[document.product_id] = []
            documents_by_product[document.product_id].append(document)
        
        # Build category lookup
        category_lookup = {cat.category_id: cat for cat in catalog_data.categories}
        for rel in catalog_data.product_categories:
            if rel.product_id not in categories_by_product:
                categories_by_product[rel.product_id] = []
            if rel.category_id in category_lookup:
                categories_by_product[rel.product_id].append(category_lookup[rel.category_id])
        
        # Convert each product to legacy format
        for product in catalog_data.products:
            legacy_product = {
                "id": product.product_id,
                "name": product.product_name,
                "url": str(product.product_url),
                "description": product.description or "",
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat(),
                "categories": [cat.category_name for cat in categories_by_product.get(product.product_id, [])],
                "images": [],
                "attachments": {
                    "PDS": [],
                    "SDS": [],
                    "other": []
                },
                "metadata": product.metadata
            }
            
            # Add media (images/videos)
            for media in media_by_product.get(product.product_id, []):
                if media.media_type == "image":
                    legacy_product["images"].append({
                        "url": str(media.media_url),
                        "alt": media.alt_text or "",
                        "format": media.media_format,
                        "dimensions": media.dimensions.dict() if media.dimensions else None,
                        "sequence": media.sequence_order
                    })
            
            # Add documents
            for document in documents_by_product.get(product.product_id, []):
                doc_data = {
                    "name": document.document_name,
                    "url": str(document.document_url),
                    "version": document.version,
                    "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
                    "file_size_kb": document.file_size_kb
                }
                
                # Group by document type for legacy format
                if document.document_type == "PDS":
                    legacy_product["attachments"]["PDS"].append(doc_data)
                elif document.document_type == "SDS":
                    legacy_product["attachments"]["SDS"].append(doc_data)
                else:
                    legacy_product["attachments"]["other"].append(doc_data)
            
            legacy_data.append(legacy_product)
        
        # Save legacy format file
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                legacy_data,
                f,
                ensure_ascii=False,
                indent=2,
                default=self._json_serializer
            )
        
        return filepath
    
    def create_summary_report(self, catalog_data: AgarCatalogData) -> Dict[str, Any]:
        """
        Create a summary report of the catalog data.
        
        Args:
            catalog_data: Normalized catalog data
            
        Returns:
            Dictionary containing summary statistics
        """
        # Calculate statistics
        total_products = len(catalog_data.products)
        total_media = len(catalog_data.media)
        total_documents = len(catalog_data.documents)
        total_categories = len(catalog_data.categories)
        
        # Media statistics
        media_by_type = {}
        media_by_format = {}
        for media in catalog_data.media:
            media_by_type[media.media_type] = media_by_type.get(media.media_type, 0) + 1
            media_by_format[media.media_format] = media_by_format.get(media.media_format, 0) + 1
        
        # Document statistics
        documents_by_type = {}
        for document in catalog_data.documents:
            documents_by_type[document.document_type] = documents_by_type.get(document.document_type, 0) + 1
        
        # Category statistics
        categories_by_level = {}
        for category in catalog_data.categories:
            categories_by_level[category.level] = categories_by_level.get(category.level, 0) + 1
        
        # Products with media/documents
        products_with_media = len(set(media.product_id for media in catalog_data.media))
        products_with_documents = len(set(doc.product_id for doc in catalog_data.documents))
        products_with_categories = len(set(rel.product_id for rel in catalog_data.product_categories))
        
        summary = {
            "extraction_timestamp": datetime.now().isoformat(),
            "totals": {
                "products": total_products,
                "media_items": total_media,
                "documents": total_documents,
                "categories": total_categories,
                "product_category_relationships": len(catalog_data.product_categories)
            },
            "media_statistics": {
                "by_type": media_by_type,
                "by_format": media_by_format,
                "products_with_media": products_with_media,
                "average_media_per_product": round(total_media / total_products, 2) if total_products > 0 else 0
            },
            "document_statistics": {
                "by_type": documents_by_type,
                "products_with_documents": products_with_documents,
                "average_documents_per_product": round(total_documents / total_products, 2) if total_products > 0 else 0
            },
            "category_statistics": {
                "by_level": categories_by_level,
                "products_with_categories": products_with_categories,
                "average_categories_per_product": round(len(catalog_data.product_categories) / total_products, 2) if total_products > 0 else 0
            },
            "data_completeness": {
                "products_with_descriptions": len([p for p in catalog_data.products if p.description]),
                "products_with_media": products_with_media,
                "products_with_documents": products_with_documents,
                "products_with_categories": products_with_categories
            }
        }
        
        return summary
    
    def save_summary_report(self, catalog_data: AgarCatalogData, filename_prefix: str = "") -> str:
        """
        Save a summary report to JSON file.
        
        Args:
            catalog_data: Normalized catalog data
            filename_prefix: Optional prefix for filename
            
        Returns:
            Path to saved summary file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}summary_{timestamp}.json" if filename_prefix else f"summary_{timestamp}.json"
        
        summary = self.create_summary_report(catalog_data)
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                summary,
                f,
                ensure_ascii=False,
                indent=2,
                default=self._json_serializer
            )
        
        return filepath
    
    def _json_serializer(self, obj):
        """
        Custom JSON serializer for datetime and other objects.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serializable representation of the object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle Pydantic models
        if hasattr(obj, 'dict'):
            return obj.dict()
        
        # Handle URLs
        if hasattr(obj, '__str__'):
            return str(obj)
        
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
