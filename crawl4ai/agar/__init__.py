"""
Agar Product Catalog Scraper

This module provides specialized functionality for scraping Agar's product catalog
using crawl4ai's advanced web crawling capabilities. It implements the 3DN normalized
data model with separate entities for products, media, documents, and categories.

Key Features:
- Async web crawling with crawl4ai
- Normalized JSON output structure
- Media and document processing
- Category hierarchy mapping
- Database integration support
"""

from .agar_scraper import AgarScraper
from .product_extractor import ProductExtractor
from .media_processor import MediaProcessor
from .document_handler import DocumentHandler
from .category_mapper import CategoryMapper
from .json_normalizer import JSONNormalizer
from .schemas import ProductSchema, MediaSchema, DocumentSchema, CategorySchema

__version__ = "1.0.0"
__author__ = "Mick Varga"

__all__ = [
    "AgarScraper",
    "ProductExtractor", 
    "MediaProcessor",
    "DocumentHandler",
    "CategoryMapper",
    "JSONNormalizer",
    "ProductSchema",
    "MediaSchema", 
    "DocumentSchema",
    "CategorySchema"
]
