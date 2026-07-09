"""
Utility functions for the Agar product catalog scraper.

This module provides common helper functions used across different components
of the Agar scraping system.
"""

import re
import hashlib
import os
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, urljoin
from datetime import datetime


def generate_product_id(product_url: str) -> str:
    """
    Generate a unique product ID from the product URL.
    
    Args:
        product_url: The product page URL
        
    Returns:
        Unique product identifier string
    """
    # Extract the slug from the URL path
    parsed = urlparse(product_url)
    path_parts = [part for part in parsed.path.split('/') if part]
    
    # Try to find the product slug (usually after /product/)
    product_slug = None
    if 'product' in path_parts:
        product_index = path_parts.index('product')
        if product_index + 1 < len(path_parts):
            product_slug = path_parts[product_index + 1]
    
    if not product_slug:
        # Fallback: use the last meaningful part of the path
        product_slug = path_parts[-1] if path_parts else 'unknown'
    
    # Clean up the slug and create ID
    product_slug = re.sub(r'[^a-zA-Z0-9\-_]', '', product_slug)
    
    # Create a hash to ensure uniqueness while keeping it readable
    url_hash = hashlib.md5(product_url.encode()).hexdigest()[:8]
    
    return f"prod_{product_slug}_{url_hash}"


def generate_media_id(product_id: str, media_url: str, sequence: int) -> str:
    """
    Generate a unique media ID.
    
    Args:
        product_id: Associated product ID
        media_url: URL of the media file
        sequence: Sequence order of the media
        
    Returns:
        Unique media identifier string
    """
    # Create hash from media URL
    media_hash = hashlib.md5(media_url.encode()).hexdigest()[:8]
    return f"med_{product_id}_{sequence:03d}_{media_hash}"


def generate_document_id(product_id: str, document_url: str) -> str:
    """
    Generate a unique document ID.
    
    Args:
        product_id: Associated product ID
        document_url: URL of the document file
        
    Returns:
        Unique document identifier string
    """
    # Create hash from document URL
    doc_hash = hashlib.md5(document_url.encode()).hexdigest()[:8]
    return f"doc_{product_id}_{doc_hash}"


def generate_category_id(category_name: str, parent_id: Optional[str] = None) -> str:
    """
    Generate a unique category ID.
    
    Args:
        category_name: Name of the category
        parent_id: Optional parent category ID
        
    Returns:
        Unique category identifier string
    """
    # Clean category name for ID
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', category_name.lower())
    clean_name = re.sub(r'\s+', '_', clean_name.strip())
    
    # Create hash for uniqueness
    name_hash = hashlib.md5(category_name.encode()).hexdigest()[:6]
    
    return f"cat_{clean_name}_{name_hash}"


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text content.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Remove common HTML artifacts first
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    
    # Remove excessive whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove extra punctuation
    text = re.sub(r'\.{2,}', '...', text)
    text = re.sub(r'-{2,}', '--', text)
    
    return text.strip()


def extract_urls_from_text(text: str, base_url: str) -> List[str]:
    """
    Extract and normalize URLs from text content.
    
    Args:
        text: Text containing URLs
        base_url: Base URL for relative link resolution
        
    Returns:
        List of normalized absolute URLs
    """
    if not text:
        return []
    
    urls = []
    
    # Pattern for URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|/[^\s<>"{}|\\^`\[\]]*'
    
    matches = re.findall(url_pattern, text)
    
    for match in matches:
        try:
            # Normalize the URL
            if match.startswith('www.'):
                match = 'https://' + match
            elif match.startswith('/'):
                match = urljoin(base_url, match)
            
            # Basic validation
            parsed = urlparse(match)
            if parsed.netloc and parsed.scheme in ['http', 'https']:
                urls.append(match)
                
        except Exception:
            continue
    
    return list(set(urls))  # Remove duplicates


def detect_document_type(filename: str, link_text: str = "") -> str:
    """
    Detect the type of document based on filename and link text.
    
    Args:
        filename: Name or URL of the file
        link_text: Text of the link pointing to the document
        
    Returns:
        Document type string (PDS, SDS, manual, etc.)
    """
    filename_lower = filename.lower()
    link_text_lower = link_text.lower()
    
    # Check for specific document types
    if any(term in filename_lower or term in link_text_lower 
           for term in ['pds', 'product data sheet', 'product-data-sheet']):
        return 'PDS'
    
    if any(term in filename_lower or term in link_text_lower 
           for term in ['sds', 'safety data sheet', 'safety-data-sheet', 'msds']):
        return 'SDS'
    
    if any(term in filename_lower or term in link_text_lower 
           for term in ['manual', 'user guide', 'instructions']):
        return 'manual'
    
    if any(term in filename_lower or term in link_text_lower 
           for term in ['spec', 'specification', 'technical']):
        return 'specification'
    
    if any(term in filename_lower or term in link_text_lower 
           for term in ['brochure', 'flyer', 'leaflet']):
        return 'brochure'
    
    if any(term in filename_lower or term in link_text_lower 
           for term in ['certificate', 'cert', 'certification']):
        return 'certificate'
    
    return 'other'


def detect_media_format(url: str) -> Optional[str]:
    """
    Detect media format from URL or filename.
    
    Args:
        url: Media file URL
        
    Returns:
        Media format string or None
    """
    url_lower = url.lower()
    
    # Image formats
    if any(ext in url_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg']):
        for ext in ['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg']:
            if f'.{ext}' in url_lower:
                return ext
    
    # Video formats
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    if 'vimeo.com' in url_lower:
        return 'vimeo'
    if any(ext in url_lower for ext in ['.mp4', '.webm']):
        return 'mp4' if '.mp4' in url_lower else 'webm'
    
    # Audio formats
    if any(ext in url_lower for ext in ['.mp3', '.wav', '.ogg']):
        for ext in ['mp3', 'wav', 'ogg']:
            if f'.{ext}' in url_lower:
                return ext
    
    return None


def ensure_directory(path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
    """
    os.makedirs(path, exist_ok=True)


def safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing/replacing problematic characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename for filesystem use
    """
    # Replace problematic characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove excessive underscores
    safe = re.sub(r'_{2,}', '_', safe)
    
    # Trim and ensure it's not empty
    safe = safe.strip('_')
    if not safe:
        safe = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return safe


def normalize_category_name(category_name: str) -> str:
    """
    Normalize category names for consistency.
    
    Args:
        category_name: Raw category name
        
    Returns:
        Normalized category name
    """
    if not category_name:
        return ""
    
    # Clean and normalize
    normalized = clean_text(category_name)
    
    # Title case
    normalized = normalized.title()
    
    # Fix common issues
    normalized = re.sub(r'\bAnd\b', 'and', normalized)
    normalized = re.sub(r'\bThe\b', 'the', normalized)
    normalized = re.sub(r'\bOf\b', 'of', normalized)
    normalized = re.sub(r'\bFor\b', 'for', normalized)
    
    return normalized


def create_slug(text: str) -> str:
    """
    Create a URL-friendly slug from text.
    
    Args:
        text: Input text
        
    Returns:
        URL-friendly slug
    """
    if not text:
        return ""
    
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    
    return slug


def extract_version_from_filename(filename: str) -> Optional[str]:
    """
    Extract version information from filename.
    
    Args:
        filename: Filename to analyze
        
    Returns:
        Version string if found, None otherwise
    """
    # Common version patterns
    patterns = [
        r'v(\d+(?:\.\d+)*)',  # v1.0, v2.3.1
        r'version[_\s]*(\d+(?:\.\d+)*)',  # version_1.0
        r'rev[_\s]*(\d+)',  # rev_1, rev 2
        r'r(\d+)',  # r1, r2
        r'(\d+(?:\.\d+)+)',  # 1.0, 2.3.1 (standalone)
    ]
    
    filename_lower = filename.lower()
    
    for pattern in patterns:
        match = re.search(pattern, filename_lower)
        if match:
            return match.group(1)
    
    return None


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split a list into batches of specified size.
    
    Args:
        items: List to batch
        batch_size: Size of each batch
        
    Returns:
        List of batches
    """
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"
