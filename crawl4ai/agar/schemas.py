"""
Data schemas for the Agar product catalog following the 3DN normalized model.

These Pydantic models define the structure for products, media, documents,
categories, and their relationships in the normalized JSON output.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    """Enumeration of supported media types."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class MediaFormat(str, Enum):
    """Enumeration of supported media formats."""
    # Image formats
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
    SVG = "svg"
    
    # Video formats
    MP4 = "mp4"
    WEBM = "webm"
    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    
    # Audio formats
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"


class DocumentType(str, Enum):
    """Enumeration of document types."""
    PDS = "PDS"  # Product Data Sheet
    SDS = "SDS"  # Safety Data Sheet
    MANUAL = "manual"
    SPEC = "specification"
    BROCHURE = "brochure"
    CERTIFICATE = "certificate"
    OTHER = "other"


class ProductSchema(BaseModel):
    """Schema for product information."""
    product_id: str = Field(..., description="Unique product identifier")
    product_name: str = Field(..., description="Product name/title")
    product_url: HttpUrl = Field(..., description="URL to the product page")
    description: Optional[str] = Field(None, description="Product description")
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Record last update timestamp")
    category_ids: List[str] = Field(default_factory=list, description="List of associated category IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional product metadata")


class MediaDimensions(BaseModel):
    """Schema for media dimensions."""
    width: Optional[int] = Field(None, description="Width in pixels")
    height: Optional[int] = Field(None, description="Height in pixels")


class MediaSchema(BaseModel):
    """Schema for media files (images, videos, audio)."""
    media_id: str = Field(..., description="Unique media identifier")
    product_id: str = Field(..., description="Associated product ID")
    media_type: MediaType = Field(..., description="Type of media (image, video, audio)")
    media_format: MediaFormat = Field(..., description="Format/extension of the media file")
    media_url: HttpUrl = Field(..., description="URL to the media file")
    sequence_order: int = Field(1, description="Display order for this media item")
    alt_text: Optional[str] = Field(None, description="Alternative text for accessibility")
    dimensions: Optional[MediaDimensions] = Field(None, description="Media dimensions if applicable")
    file_size_kb: Optional[int] = Field(None, description="File size in kilobytes")
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional media metadata")


class DocumentSchema(BaseModel):
    """Schema for documents (PDFs, datasheets, etc.)."""
    document_id: str = Field(..., description="Unique document identifier")
    product_id: str = Field(..., description="Associated product ID")
    document_type: DocumentType = Field(..., description="Type of document")
    document_name: str = Field(..., description="Human-readable document name")
    document_url: HttpUrl = Field(..., description="URL to the document file")
    version: Optional[str] = Field(None, description="Document version number")
    uploaded_at: Optional[datetime] = Field(None, description="Document upload/creation date")
    file_size_kb: Optional[int] = Field(None, description="File size in kilobytes")
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional document metadata")


class CategorySchema(BaseModel):
    """Schema for product categories with hierarchical support."""
    category_id: str = Field(..., description="Unique category identifier")
    category_name: str = Field(..., description="Category display name")
    parent_category_id: Optional[str] = Field(None, description="Parent category ID for hierarchy")
    description: Optional[str] = Field(None, description="Category description")
    slug: Optional[str] = Field(None, description="URL-friendly category identifier")
    level: int = Field(0, description="Hierarchy level (0 = root)")
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional category metadata")


class ProductCategoryRelation(BaseModel):
    """Schema for many-to-many product-category relationships."""
    product_id: str = Field(..., description="Product ID")
    category_id: str = Field(..., description="Category ID")
    primary: bool = Field(False, description="Whether this is the primary category for the product")
    created_at: datetime = Field(default_factory=datetime.now, description="Relationship creation timestamp")


class AgarCatalogData(BaseModel):
    """Complete normalized catalog data structure."""
    products: List[ProductSchema] = Field(default_factory=list, description="All products")
    media: List[MediaSchema] = Field(default_factory=list, description="All media files")
    documents: List[DocumentSchema] = Field(default_factory=list, description="All documents")
    categories: List[CategorySchema] = Field(default_factory=list, description="All categories")
    product_categories: List[ProductCategoryRelation] = Field(
        default_factory=list, 
        description="Product-category relationships"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Catalog metadata")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: lambda v: str(v)
        }


class ScrapingConfig(BaseModel):
    """Configuration for Agar scraping process."""
    base_url: HttpUrl = Field(..., description="Base URL to start scraping")
    max_products: Optional[int] = Field(None, description="Maximum number of products to scrape")
    delay_seconds: float = Field(1.0, description="Delay between requests")
    output_dir: str = Field("output", description="Directory for JSON output files")
    use_database: bool = Field(False, description="Whether to save to database")
    verbose: bool = Field(False, description="Enable verbose logging")
    include_images: bool = Field(True, description="Process product images")
    include_documents: bool = Field(True, description="Process documents/PDFs")
    include_categories: bool = Field(True, description="Process category information")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
