"""
Enhanced Product extraction system for Agar catalog scraping per technical brief.

This module implements the specific requirements from the Agar Scraping Technical Brief v1.0,
including modal handling, tab navigation, and precise field extraction.
"""

import asyncio
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.extraction_strategy import ExtractionStrategy

from .schemas import ProductSchema, ScrapingConfig
from .utils import generate_product_id, clean_text


class EnhancedProductExtractor:
    """
    Enhanced product extractor implementing Agar Technical Brief v1.0 requirements.
    """
    
    def __init__(self, config: ScrapingConfig):
        """
        Initialize the Enhanced ProductExtractor.
        
        Args:
            config: Scraping configuration
        """
        self.config = config
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=config.verbose
        )
        
        # JavaScript for modal handling and tab navigation per brief requirements
        self.modal_handler_js = """
        // Handle modal/popup closure as specified in brief
        function closeModalsAndPopups() {
            // Newsletter modal selectors
            const modalSelectors = [
                '.modal-overlay',
                '.modal-backdrop', 
                '.newsletter-modal',
                '.popup-overlay',
                '.modal.show',
                '#newsletter-modal'
            ];
            
            // Close button selectors
            const closeSelectors = [
                '.close-button',
                '.modal-close',
                'button[aria-label="Close"]',
                '.close',
                '[data-dismiss="modal"]',
                '.modal-close-btn'
            ];
            
            // First try to close by clicking close buttons
            for (let selector of closeSelectors) {
                const closeBtn = document.querySelector(selector);
                if (closeBtn && closeBtn.offsetParent !== null) {
                    closeBtn.click();
                    console.log('Closed modal using:', selector);
                    return true;
                }
            }
            
            // Then try to remove modal overlays directly
            for (let selector of modalSelectors) {
                const modal = document.querySelector(selector);
                if (modal && modal.offsetParent !== null) {
                    modal.remove();
                    console.log('Removed modal using:', selector);
                    return true;
                }
            }
            
            return false;
        }
        
        closeModalsAndPopups();
        """
        
        self.tab_navigation_js = """
        // Navigate to specific tabs as required by brief
        function navigateToTab(tabName) {
            const tabSelectors = {
                'description': [
                    'a[href="#tab-description"]',
                    '.tab-description',
                    'a[data-tab="description"]',
                    '.tabs a:contains("Description")'
                ],
                'downloads': [
                    'a[href="#tab-wcpoa_product_tab"]',
                    'a[href*="download"]',
                    '.tab-downloads',
                    'a:contains("Download SDS")',
                    'a:contains("Download")'
                ],
                'reviews': [
                    'a[href="#tab-reviews"]',
                    '.tab-reviews',
                    'a[data-tab="reviews"]',
                    'a:contains("Reviews")'
                ]
            };
            
            const selectors = tabSelectors[tabName] || [];
            
            for (let selector of selectors) {
                const tab = document.querySelector(selector);
                if (tab && tab.offsetParent !== null) {
                    tab.click();
                    console.log('Navigated to tab:', tabName, 'using:', selector);
                    return true;
                }
            }
            
            console.log('Could not find tab:', tabName);
            return false;
        }
        
        return { navigateToTab };
        """
        
        # Enhanced CSS selectors per technical brief specifications
        self.product_extraction_schema = {
            "name": "agar_product_enhanced",
            "baseSelector": "body",
            "fields": [
                # Product Name - h1.product_title, h1.entry-title
                {
                    "name": "product_title",
                    "selector": "h1.product_title, h1.entry-title, .product-title h1",
                    "type": "text"
                },
                
                # Product Codes - Table row labeled "Code"  
                {
                    "name": "product_codes_text",
                    "selector": "table tr td:contains('Code') + td, .product-meta td:contains('Code') + td",
                    "type": "text"
                },
                
                # SKU Values - Table row labeled "SKU" or text after "SKU:"
                {
                    "name": "sku_values_text", 
                    "selector": "table tr td:contains('SKU') + td, .product-meta td:contains('SKU') + td, .sku",
                    "type": "text"
                },
                
                # Categories - After "Categories:" label
                {
                    "name": "categories_links",
                    "selector": ".posted_in a, .product-categories a, .product-meta .posted_in a",
                    "type": "text"
                },
                
                # Tags - After "Tag:" label  
                {
                    "name": "tags_links",
                    "selector": ".tagged_as a, .product-tags a, .product-meta .tagged_as a",
                    "type": "text"
                },
                
                # Sizes - Table row labeled "Sizes"
                {
                    "name": "sizes_text",
                    "selector": "table tr td:contains('Sizes') + td, .product-meta td:contains('Sizes') + td",
                    "type": "text"
                },
                
                # pH Level - Table row labeled "pH Level"
                {
                    "name": "ph_level_text",
                    "selector": "table tr td:contains('pH Level') + td, .product-meta td:contains('pH Level') + td",
                    "type": "text"
                },
                
                # Perfume - Table row labeled "Perfume"
                {
                    "name": "perfume_text",
                    "selector": "table tr td:contains('Perfume') + td, .product-meta td:contains('Perfume') + td",
                    "type": "text"
                },
                
                # Key Benefits - Bullet list under "Key Benefits"
                {
                    "name": "key_benefits_list",
                    "selector": ".key-benefits ul li, .benefits ul li, ul li",
                    "type": "text"
                },
                
                # Description content from tabs
                {
                    "name": "description_content",
                    "selector": "#tab-description, .product-description, .woocommerce-product-details__short-description",
                    "type": "text"
                },
                
                # Images with alt text
                {
                    "name": "product_images_src",
                    "selector": ".woocommerce-product-gallery__image img, .product-images img, .product-gallery img",
                    "type": "attribute",
                    "attribute": "src"
                },
                {
                    "name": "product_images_alt",
                    "selector": ".woocommerce-product-gallery__image img, .product-images img, .product-gallery img",
                    "type": "attribute", 
                    "attribute": "alt"
                },
                
                # Documents - Links in "Download SDS / PDS" tab
                {
                    "name": "document_links_href",
                    "selector": "a[href*='.pdf'], a[href*='attachment'], .attachments a, .product-attachments a, a[href*='download']",
                    "type": "attribute",
                    "attribute": "href"
                },
                {
                    "name": "document_links_text",
                    "selector": "a[href*='.pdf'], a[href*='attachment'], .attachments a, .product-attachments a, a[href*='download']",
                    "type": "text"
                },
                
                # Reviews - Rating and count
                {
                    "name": "star_rating",
                    "selector": ".star-rating, .rating, .product-rating",
                    "type": "attribute",
                    "attribute": "title"
                },
                {
                    "name": "review_count",
                    "selector": ".review-count, .reviews-count, .woocommerce-review-link",
                    "type": "text"
                },
                
                # Additional metadata from product page
                {
                    "name": "short_description",
                    "selector": ".woocommerce-product-details__short-description, .product-short-description",
                    "type": "text"
                }
            ]
        }
        
        self.extraction_strategy = JsonCssExtractionStrategy(
            self.product_extraction_schema,
            verbose=config.verbose
        )

    def parse_product_codes(self, codes_text: str) -> List[str]:
        """Parse product codes from text, handling multiple formats."""
        if not codes_text:
            return []
        
        # Remove extra whitespace and split by common separators
        codes = re.split(r'[,;|\n]+', codes_text.strip())
        
        # Clean each code and filter out empty ones
        cleaned_codes = []
        for code in codes:
            cleaned = re.sub(r'[^\w\d-]', '', code.strip())
            if cleaned:
                cleaned_codes.append(cleaned)
        
        return cleaned_codes

    def parse_sku_values(self, sku_text: str) -> List[str]:
        """Parse SKU values from text, handling multiple formats."""
        if not sku_text:
            return []
        
        # Handle "SKU: VALUE" format
        sku_text = re.sub(r'^SKU:\s*', '', sku_text, flags=re.IGNORECASE)
        
        # Split by common separators
        skus = re.split(r'[,;|\n]+', sku_text.strip())
        
        # Clean each SKU
        cleaned_skus = []
        for sku in skus:
            cleaned = sku.strip()
            if cleaned:
                cleaned_skus.append(cleaned)
        
        return cleaned_skus

    def parse_sizes(self, sizes_text: str) -> List[str]:
        """Parse size values, ensuring unit notation is preserved."""
        if not sizes_text:
            return []
        
        # Split by common separators
        sizes = re.split(r'[,;|\n]+', sizes_text.strip())
        
        # Clean and validate sizes
        cleaned_sizes = []
        for size in sizes:
            cleaned = size.strip()
            # Ensure it has a unit (L, kg, mL, g)
            if cleaned and re.search(r'\d+\s*(L|kg|mL|g|l)\b', cleaned, re.IGNORECASE):
                cleaned_sizes.append(cleaned)
        
        return cleaned_sizes

    def parse_key_benefits(self, benefits_data: Any) -> List[str]:
        """Parse key benefits from extracted data."""
        if not benefits_data:
            return []
        
        benefits = []
        if isinstance(benefits_data, list):
            for item in benefits_data:
                if isinstance(item, str):
                    cleaned = clean_text(item)
                    if cleaned and len(cleaned) > 10:  # Filter out very short items
                        benefits.append(cleaned)
        elif isinstance(benefits_data, str):
            # Split if it's a single string with multiple benefits
            items = re.split(r'[•\n\r]+', benefits_data)
            for item in items:
                cleaned = clean_text(item)
                if cleaned and len(cleaned) > 10:
                    benefits.append(cleaned)
        
        return benefits

    def parse_documents(self, links_href: Any, links_text: Any) -> List[Dict[str, Any]]:
        """Parse document information from links."""
        documents = []
        
        # Ensure both are lists
        if not isinstance(links_href, list):
            links_href = [links_href] if links_href else []
        if not isinstance(links_text, list):
            links_text = [links_text] if links_text else []
        
        # Pair up hrefs and texts
        for i, href in enumerate(links_href):
            if not href:
                continue
                
            text = links_text[i] if i < len(links_text) else ""
            
            # Determine document type from text or URL
            doc_type = "OTHER"
            if "sds" in text.lower() or "sds" in href.lower():
                doc_type = "SDS"
            elif "pds" in text.lower() or "pds" in href.lower():
                doc_type = "PDS"
            elif "manual" in text.lower():
                doc_type = "MANUAL"
            elif "spec" in text.lower():
                doc_type = "SPEC"
            
            documents.append({
                "type": doc_type,
                "name": clean_text(text) or "Document",
                "url": href
            })
        
        return documents

    def parse_reviews(self, star_rating: str, review_count: str) -> Dict[str, Any]:
        """Parse review information."""
        rating = None
        count = 0
        
        if star_rating:
            # Extract rating from title like "Rated 5.00 out of 5"
            rating_match = re.search(r'(\d+\.?\d*)', star_rating)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                except ValueError:
                    pass
        
        if review_count:
            # Extract count from text like "(1 customer review)"
            count_match = re.search(r'(\d+)', review_count)
            if count_match:
                try:
                    count = int(count_match.group(1))
                except ValueError:
                    pass
        
        return {
            "rating": rating,
            "count": count
        }

    async def extract_product_enhanced(self, product_url: str) -> Optional[ProductSchema]:
        """
        Extract product information using enhanced extraction per technical brief.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            ProductSchema object or None if extraction fails
        """
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            try:
                # Step 1: Handle modals and popups
                run_config = CrawlerRunConfig(
                    js_code=self.modal_handler_js,
                    wait_for="networkidle",
                    page_timeout=30000
                )
                
                result = await crawler.arun(url=product_url, config=run_config)
                
                if not result.success:
                    if self.config.verbose:
                        print(f"Failed to load page: {product_url}")
                    return None
                
                # Step 2: Extract basic product information
                run_config.extraction_strategy = self.extraction_strategy
                result = await crawler.arun(url=product_url, config=run_config)
                
                if not result.extracted_content:
                    if self.config.verbose:
                        print(f"No content extracted from {product_url}")
                    return None
                
                # Parse JSON response
                try:
                    extracted_data = json.loads(result.extracted_content)
                except json.JSONDecodeError:
                    if self.config.verbose:
                        print(f"Failed to parse JSON from {product_url}")
                    return None
                
                # Handle data structure (could be list or dict)
                if isinstance(extracted_data, list) and len(extracted_data) > 0:
                    data = extracted_data[0] if isinstance(extracted_data[0], dict) else {}
                elif isinstance(extracted_data, dict):
                    data = extracted_data
                else:
                    if self.config.verbose:
                        print(f"Unexpected data structure from {product_url}")
                    return None
                
                # Step 3: Navigate to tabs and extract additional content
                await self._extract_tab_content(crawler, product_url, data)
                
                # Step 4: Parse and structure the data
                return self._build_product_schema(product_url, data)
                
            except Exception as e:
                if self.config.verbose:
                    print(f"Error extracting product from {product_url}: {e}")
                return None

    async def _extract_tab_content(self, crawler: AsyncWebCrawler, url: str, data: Dict[str, Any]):
        """Extract content from product tabs (Description, Downloads, Reviews)."""
        try:
            # Navigate to Description tab
            tab_js = self.tab_navigation_js + """
            const tabs = navigateToTab('description');
            setTimeout(() => {
                const descContent = document.querySelector('#tab-description, .tab-pane.active');
                if (descContent) {
                    window.descriptionContent = descContent.innerText;
                }
            }, 1000);
            """
            
            run_config = CrawlerRunConfig(js_code=tab_js, wait_for="networkidle")
            await crawler.arun(url=url, config=run_config)
            
            # Navigate to Downloads tab
            downloads_js = self.tab_navigation_js + """
            const tabs = navigateToTab('downloads');
            setTimeout(() => {
                const downloadContent = document.querySelector('#tab-wcpoa_product_tab, .tab-pane.active');
                if (downloadContent) {
                    const links = downloadContent.querySelectorAll('a[href]');
                    window.downloadLinks = Array.from(links).map(a => ({
                        href: a.href,
                        text: a.textContent.trim()
                    }));
                }
            }, 1000);
            """
            
            run_config.js_code = downloads_js
            await crawler.arun(url=url, config=run_config)
            
            # Navigate to Reviews tab  
            reviews_js = self.tab_navigation_js + """
            const tabs = navigateToTab('reviews');
            setTimeout(() => {
                const reviewContent = document.querySelector('#tab-reviews, .tab-pane.active');
                if (reviewContent) {
                    const rating = reviewContent.querySelector('.star-rating');
                    const count = reviewContent.querySelector('.review-count');
                    window.reviewData = {
                        rating: rating ? rating.getAttribute('title') || rating.textContent : null,
                        count: count ? count.textContent : null
                    };
                }
            }, 1000);
            """
            
            run_config.js_code = reviews_js
            await crawler.arun(url=url, config=run_config)
            
        except Exception as e:
            if self.config.verbose:
                print(f"Error extracting tab content: {e}")

    def _build_product_schema(self, product_url: str, data: Dict[str, Any]) -> ProductSchema:
        """Build ProductSchema from extracted data."""
        
        # Generate product ID
        product_id = generate_product_id(product_url)
        
        # Extract and clean product name
        product_name = clean_text(data.get("product_title", ""))
        if not product_name:
            # Fallback: extract from URL
            product_name = urlparse(product_url).path.split('/')[-2].replace('-', ' ').title()
        
        # Parse structured fields
        codes = self.parse_product_codes(data.get("product_codes_text", ""))
        skus = self.parse_sku_values(data.get("sku_values_text", ""))
        sizes = self.parse_sizes(data.get("sizes_text", ""))
        
        # Extract categories and tags
        categories = []
        if data.get("categories_links"):
            if isinstance(data["categories_links"], list):
                categories = [clean_text(cat) for cat in data["categories_links"] if cat]
            else:
                categories = [clean_text(data["categories_links"])]
        
        tags = []
        if data.get("tags_links"):
            if isinstance(data["tags_links"], list):
                tags = [clean_text(tag) for tag in data["tags_links"] if tag]
            else:
                tags = [clean_text(data["tags_links"])]
        
        # Parse key benefits
        key_benefits = self.parse_key_benefits(data.get("key_benefits_list"))
        
        # Parse documents
        documents = self.parse_documents(
            data.get("document_links_href"),
            data.get("document_links_text")
        )
        
        # Parse reviews
        reviews = self.parse_reviews(
            data.get("star_rating", ""),
            data.get("review_count", "")
        )
        
        # Build description from available content
        description_parts = []
        if data.get("short_description"):
            description_parts.append(clean_text(data["short_description"]))
        if data.get("description_content"):
            description_parts.append(clean_text(data["description_content"]))
        
        description = " ".join(description_parts) if description_parts else None
        
        # Build specifications
        specifications = {}
        if data.get("ph_level_text"):
            specifications["ph_level"] = clean_text(data["ph_level_text"])
        if data.get("perfume_text"):
            specifications["perfume"] = clean_text(data["perfume_text"])
        
        # Create ProductSchema
        product = ProductSchema(
            product_id=product_id,
            product_name=product_name,
            product_url=product_url,
            description=description,
            metadata={
                "raw_extracted_data": data,
                "extraction_timestamp": datetime.now().isoformat(),
                "codes": codes,
                "skus": skus,
                "categories": categories,
                "tags": tags,
                "sizes": sizes,
                "specifications": specifications,
                "key_benefits": key_benefits,
                "documents": documents,
                "reviews": reviews,
                "brief_compliance": "v1.0"
            }
        )
        
        if self.config.verbose:
            print(f"Enhanced extraction completed: {product.product_name}")
        
        return product

    async def extract_products_from_urls(self, product_urls: List[str]) -> List[ProductSchema]:
        """
        Extract products from a list of URLs with enhanced processing.
        
        Args:
            product_urls: List of product URLs to process
            
        Returns:
            List of successfully extracted ProductSchema objects
        """
        products = []
        
        # Process in batches to avoid overwhelming the server
        batch_size = 3  # Reduced for more careful extraction
        for i in range(0, len(product_urls), batch_size):
            batch = product_urls[i:i + batch_size]
            
            if self.config.verbose:
                print(f"Processing enhanced batch {i//batch_size + 1}/{(len(product_urls) + batch_size - 1)//batch_size}")
            
            # Process batch with controlled concurrency
            tasks = [self.extract_product_enhanced(url) for url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter results
            for result in batch_results:
                if isinstance(result, ProductSchema):
                    products.append(result)
                elif isinstance(result, Exception) and self.config.verbose:
                    print(f"Enhanced batch processing error: {result}")
            
            # Respectful delay between batches
            if i + batch_size < len(product_urls):
                await asyncio.sleep(self.config.delay_seconds * 3)
        
        if self.config.verbose:
            print(f"Enhanced extraction complete: {len(products)} products from {len(product_urls)} URLs")
        
        return products
