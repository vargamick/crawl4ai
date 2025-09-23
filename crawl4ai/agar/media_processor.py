"""
Media processing module for Agar product catalog.

This module handles the extraction and processing of media files (images, videos)
from product pages, including metadata extraction and normalization.
"""

import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from .schemas import MediaSchema, MediaType, MediaFormat, MediaDimensions, ProductSchema, ScrapingConfig
from .utils import generate_media_id, detect_media_format, clean_text


class MediaProcessor:
    """
    Handles media file extraction and processing for product pages.
    """
    
    def __init__(self, config: ScrapingConfig):
        """
        Initialize the MediaProcessor.
        
        Args:
            config: Scraping configuration
        """
        self.config = config
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=config.verbose
        )
    
    async def extract_media_from_product(self, product: ProductSchema, raw_extracted_data: Dict[str, Any]) -> List[MediaSchema]:
        """
        Extract media files from a product's raw extracted data.
        
        Args:
            product: Product schema object
            raw_extracted_data: Raw data extracted from the product page
            
        Returns:
            List of MediaSchema objects
        """
        if not self.config.include_images:
            return []
        
        media_items = []
        
        # Extract images
        images = await self._extract_images(product, raw_extracted_data)
        media_items.extend(images)
        
        # Extract videos (YouTube embeds, etc.)
        videos = await self._extract_videos(product, raw_extracted_data)
        media_items.extend(videos)
        
        if self.config.verbose and media_items:
            print(f"  Found {len(media_items)} media items for product: {product.product_name}")
        
        return media_items
    
    async def _extract_images(self, product: ProductSchema, raw_data: Dict[str, Any]) -> List[MediaSchema]:
        """
        Extract image media from raw product data.
        
        Args:
            product: Product schema object
            raw_data: Raw extracted data
            
        Returns:
            List of image MediaSchema objects
        """
        images = []
        
        # Get image URLs and alt texts
        image_urls = raw_data.get("product_images", [])
        alt_texts = raw_data.get("product_image_alts", [])
        
        # Normalize to lists
        if isinstance(image_urls, str):
            image_urls = [image_urls]
        if isinstance(alt_texts, str):
            alt_texts = [alt_texts]
        
        # Ensure alt_texts list is same length as image_urls
        while len(alt_texts) < len(image_urls):
            alt_texts.append("")
        
        # Process each image
        for sequence, (img_url, alt_text) in enumerate(zip(image_urls, alt_texts), 1):
            if not img_url:
                continue
            
            # Make absolute URL
            if not img_url.startswith('http'):
                img_url = urljoin(str(product.product_url), img_url)
            
            # Detect format
            media_format = detect_media_format(img_url)
            if not media_format:
                # Try to guess from common image extensions
                if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                    media_format = img_url.lower().split('.')[-1].split('?')[0]
                else:
                    media_format = "jpg"  # Default fallback
            
            # Generate media ID
            media_id = generate_media_id(product.product_id, img_url, sequence)
            
            # Create MediaSchema
            try:
                media_item = MediaSchema(
                    media_id=media_id,
                    product_id=product.product_id,
                    media_type=MediaType.IMAGE,
                    media_format=MediaFormat(media_format.lower()),
                    media_url=img_url,
                    sequence_order=sequence,
                    alt_text=clean_text(alt_text) if alt_text else None,
                    metadata={
                        "extracted_from": "product_images",
                        "original_url": img_url
                    }
                )
                
                images.append(media_item)
                
            except Exception as e:
                if self.config.verbose:
                    print(f"  Error creating media schema for {img_url}: {e}")
                continue
        
        return images
    
    async def _extract_videos(self, product: ProductSchema, raw_data: Dict[str, Any]) -> List[MediaSchema]:
        """
        Extract video media from raw product data.
        
        Args:
            product: Product schema object
            raw_data: Raw extracted data
            
        Returns:
            List of video MediaSchema objects
        """
        videos = []
        
        # Look for video content in various places
        content_sections = [
            raw_data.get("product_content", ""),
            raw_data.get("product_description", ""),
        ]
        
        video_sequence = 1
        
        for content in content_sections:
            if not content:
                continue
            
            # Find YouTube video URLs
            youtube_patterns = [
                r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
                r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
                r'https?://youtu\.be/([a-zA-Z0-9_-]+)',
                r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
                r'youtu\.be/([a-zA-Z0-9_-]+)'
            ]
            
            for pattern in youtube_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    video_id = match.group(1)
                    youtube_url = f"https://www.youtube.com/embed/{video_id}"
                    
                    # Generate media ID
                    media_id = generate_media_id(product.product_id, youtube_url, video_sequence)
                    
                    try:
                        video_item = MediaSchema(
                            media_id=media_id,
                            product_id=product.product_id,
                            media_type=MediaType.VIDEO,
                            media_format=MediaFormat.YOUTUBE,
                            media_url=youtube_url,
                            sequence_order=video_sequence,
                            metadata={
                                "youtube_video_id": video_id,
                                "extracted_from": "product_content",
                                "original_match": match.group(0)
                            }
                        )
                        
                        videos.append(video_item)
                        video_sequence += 1
                        
                    except Exception as e:
                        if self.config.verbose:
                            print(f"  Error creating video schema for {youtube_url}: {e}")
                        continue
            
            # Find Vimeo video URLs
            vimeo_patterns = [
                r'https?://(?:www\.)?vimeo\.com/(\d+)',
                r'vimeo\.com/(\d+)'
            ]
            
            for pattern in vimeo_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    video_id = match.group(1)
                    vimeo_url = f"https://vimeo.com/{video_id}"
                    
                    # Generate media ID
                    media_id = generate_media_id(product.product_id, vimeo_url, video_sequence)
                    
                    try:
                        video_item = MediaSchema(
                            media_id=media_id,
                            product_id=product.product_id,
                            media_type=MediaType.VIDEO,
                            media_format=MediaFormat.VIMEO,
                            media_url=vimeo_url,
                            sequence_order=video_sequence,
                            metadata={
                                "vimeo_video_id": video_id,
                                "extracted_from": "product_content",
                                "original_match": match.group(0)
                            }
                        )
                        
                        videos.append(video_item)
                        video_sequence += 1
                        
                    except Exception as e:
                        if self.config.verbose:
                            print(f"  Error creating video schema for {vimeo_url}: {e}")
                        continue
        
        return videos
    
    async def enhance_media_metadata(self, media_items: List[MediaSchema]) -> List[MediaSchema]:
        """
        Enhance media items with additional metadata by fetching image dimensions, etc.
        
        Args:
            media_items: List of media items to enhance
            
        Returns:
            Enhanced list of media items
        """
        if not media_items:
            return media_items
        
        enhanced_items = []
        
        for media_item in media_items:
            enhanced_item = await self._enhance_single_media_item(media_item)
            enhanced_items.append(enhanced_item)
            
            # Rate limiting
            await asyncio.sleep(0.1)
        
        return enhanced_items
    
    async def _enhance_single_media_item(self, media_item: MediaSchema) -> MediaSchema:
        """
        Enhance a single media item with additional metadata.
        
        Args:
            media_item: Media item to enhance
            
        Returns:
            Enhanced media item
        """
        try:
            if media_item.media_type == MediaType.IMAGE:
                # Try to get image dimensions using a simple HEAD request approach
                # or by loading the image in the browser
                dimensions = await self._get_image_dimensions(str(media_item.media_url))
                if dimensions:
                    media_item.dimensions = dimensions
            
            return media_item
            
        except Exception as e:
            if self.config.verbose:
                print(f"  Warning: Could not enhance media item {media_item.media_id}: {e}")
            return media_item
    
    async def _get_image_dimensions(self, image_url: str) -> Optional[MediaDimensions]:
        """
        Get image dimensions by loading the image in browser.
        
        Args:
            image_url: URL of the image
            
        Returns:
            MediaDimensions object or None if unable to determine
        """
        try:
            # Use browser to get image dimensions
            js_code = f"""
            (async () => {{
                const img = new Image();
                img.crossOrigin = 'anonymous';
                
                return new Promise((resolve) => {{
                    img.onload = function() {{
                        resolve({{
                            width: this.naturalWidth,
                            height: this.naturalHeight
                        }});
                    }};
                    img.onerror = function() {{
                        resolve(null);
                    }};
                    img.src = '{image_url}';
                    
                    // Timeout after 5 seconds
                    setTimeout(() => resolve(null), 5000);
                }});
            }})()
            """
            
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                # Create a simple HTML page to run our JS
                simple_html_url = "data:text/html,<html><body></body></html>"
                
                run_config = CrawlerRunConfig(
                    js_code=[js_code],
                    cache_mode="bypass"
                )
                
                result = await crawler.arun(url=simple_html_url, config=run_config)
                
                if result.success and hasattr(result, 'js_execution_results') and result.js_execution_results:
                    js_result = result.js_execution_results[0]
                    if js_result and isinstance(js_result, dict) and 'width' in js_result and 'height' in js_result:
                        return MediaDimensions(
                            width=js_result['width'],
                            height=js_result['height']
                        )
            
        except Exception as e:
            if self.config.verbose:
                print(f"  Could not get dimensions for {image_url}: {e}")
        
        return None
    
    def filter_duplicate_media(self, media_items: List[MediaSchema]) -> List[MediaSchema]:
        """
        Filter out duplicate media items based on URL.
        
        Args:
            media_items: List of media items
            
        Returns:
            Filtered list without duplicates
        """
        seen_urls = set()
        filtered_items = []
        
        for media_item in media_items:
            media_url_str = str(media_item.media_url)
            if media_url_str not in seen_urls:
                seen_urls.add(media_url_str)
                filtered_items.append(media_item)
            elif self.config.verbose:
                print(f"  Filtering duplicate media: {media_url_str}")
        
        return filtered_items
    
    def sort_media_by_sequence(self, media_items: List[MediaSchema]) -> List[MediaSchema]:
        """
        Sort media items by their sequence order.
        
        Args:
            media_items: List of media items
            
        Returns:
            Sorted list of media items
        """
        return sorted(media_items, key=lambda x: (x.product_id, x.sequence_order))
