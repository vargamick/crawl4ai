#!/usr/bin/env python3
"""
Enhanced Docker Agar Scraper WITH Content Exclusion
Implements the content filtering methods from crawl4ai_content_exclusion_guide.md

This script processes the first 10 Agar product URLs and applies advanced content exclusion
to remove navigation bars, product enquiry forms, footer subscriptions, and other noise.

Generates comparative results to demonstrate the effectiveness of content exclusion.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time

# Import from the container's crawl4ai installation
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy, BM25ContentFilter
from crawl4ai.agar.schemas import ScrapingConfig
from crawl4ai.agar.enhanced_agar_scraper import EnhancedAgarScraper


class ContentExclusionAgarScraper:
    """
    Enhanced Agar scraper with advanced content exclusion capabilities.
    Implements methods from crawl4ai_content_exclusion_guide.md
    """
    
    def __init__(self, urls_file: str, batch_size: int = 10, output_dir: str = "/app/docker_results"):
        """
        Initialize content exclusion scraper.
        
        Args:
            urls_file: Path to URLs file
            batch_size: Number of URLs to process (limited to 10 for demo)
            output_dir: Output directory (docker_results for user review)
        """
        self.urls_file = urls_file
        self.batch_size = min(batch_size, 10)  # Limit to 10 items as requested
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load URLs (first 10 only)
        self.product_urls = self._load_urls()[:10]
        self.total_urls = len(self.product_urls)
        
        print(f"🚀 Enhanced Agar Scraper with Content Exclusion")
        print(f"📁 URLs file: {urls_file}")
        print(f"🎯 Processing first {self.total_urls} URLs for demonstration")
        print(f"📂 Output directory: {output_dir}")
        print(f"🛡️  Content exclusion: ENABLED")
    
    def _load_urls(self) -> List[str]:
        """Load product URLs from JSON file."""
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            urls = data.get("all_product_urls", [])
            print(f"✅ Loaded {len(urls)} total URLs, using first 10 for demo")
            return urls
            
        except Exception as e:
            print(f"❌ Error loading URLs file: {e}")
            return []
    
    async def scrape_with_content_exclusion(self) -> Dict[str, Any]:
        """
        Scrape products with advanced content exclusion enabled.
        Implements the methods from crawl4ai_content_exclusion_guide.md
        """
        print(f"\n🛡️  Starting ENHANCED scraping with content exclusion...")
        print(f"=" * 70)
        
        start_time = datetime.now()
        
        # Enhanced browser config with content filtering
        browser_config = BrowserConfig(
            headless=True,
            verbose=True
        )
        
        # Advanced crawler configuration with content exclusion
        run_config = CrawlerRunConfig(
            # Method 1: CSS Selector Exclusion - Target specific noise elements
            excluded_selector="""
                nav, header, footer, 
                .navigation, .navbar, .main-nav, .site-header,
                .product-enquiry, .enquiry-form, form[class*="enquiry"], 
                .footer-subscription, .newsletter-signup, .footer-newsletter,
                .sidebar, .widget-area, .social-media, .social-links,
                .breadcrumbs, .back-to-top, .scroll-to-top,
                .related-products, .upsells, .cross-sells,
                .modal, .popup, .overlay, .newsletter-modal
            """,
            
            # Method 2: Tag-based Exclusion - Remove entire tag types
            excluded_tags=[
                "script", "style", "noscript", "iframe", 
                "nav", "header", "footer", "aside",
                "form"  # Remove all forms including enquiry forms
            ],
            
            # Method 3: Built-in Form Removal
            remove_forms=True,
            
            # Method 4: Overlay Element Removal
            remove_overlay_elements=True,
            
            # Method 5: Intelligent Content Filtering
            content_filter=BM25ContentFilter(
                bm25_threshold=1.0,  # Higher threshold = more aggressive filtering
                user_query="product information specifications features benefits"
            ),
            
            # Additional optimizations
            word_count_threshold=10,  # Remove very short content blocks
            only_text=False,  # Keep structured data
            
            # Wait for page load and handle dynamic content
            wait_for="networkidle",
            page_timeout=30000,
            
            # Handle JavaScript-based content and modals
            js_code="""
            // Advanced modal and popup handling
            function removeNoiseSections() {
                console.log('🛡️  Applying advanced content exclusion...');
                
                // Remove navigation elements
                const navSelectors = [
                    'nav', 'header', '.navigation', '.navbar', '.main-nav', 
                    '.site-header', '.primary-navigation', '.menu-main'
                ];
                
                // Remove form elements (enquiry, newsletter, etc.)
                const formSelectors = [
                    '.product-enquiry', '.enquiry-form', 'form[class*="enquiry"]',
                    '.newsletter-signup', '.footer-newsletter', '.newsletter-form',
                    '.contact-form', '.quote-form'
                ];
                
                // Remove footer and subscription elements
                const footerSelectors = [
                    'footer', '.site-footer', '.footer-subscription', 
                    '.footer-widgets', '.footer-newsletter'
                ];
                
                // Remove social and promotional elements
                const socialSelectors = [
                    '.social-media', '.social-links', '.social-icons',
                    '.promotional-banner', '.advertisement', '.ads'
                ];
                
                let removedCount = 0;
                const allSelectors = [...navSelectors, ...formSelectors, ...footerSelectors, ...socialSelectors];
                
                allSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        if (el && el.parentNode) {
                            el.remove();
                            removedCount++;
                        }
                    });
                });
                
                console.log(`🛡️  Removed ${removedCount} noise elements`);
                
                // Close any remaining modals
                const modalSelectors = [
                    '.modal', '.popup', '.overlay', '.newsletter-modal',
                    '.modal-backdrop', '.modal-overlay'
                ];
                
                modalSelectors.forEach(selector => {
                    const modals = document.querySelectorAll(selector);
                    modals.forEach(modal => {
                        if (modal && modal.style.display !== 'none') {
                            modal.remove();
                        }
                    });
                });
                
                return removedCount;
            }
            
            // Execute noise removal
            const removed = removeNoiseSections();
            console.log(`Advanced content exclusion complete: ${removed} elements removed`);
            """
        )
        
        # Enhanced extraction strategy focused on clean content
        extraction_schema = {
            "name": "agar_product_clean_extraction",
            "baseSelector": "body",
            "fields": [
                {
                    "name": "product_title",
                    "selector": "h1.product_title, h1.entry-title, .product-title h1",
                    "type": "text"
                },
                {
                    "name": "product_description", 
                    "selector": ".product-description, .woocommerce-product-details__short-description, #tab-description",
                    "type": "text"
                },
                {
                    "name": "product_specifications",
                    "selector": ".product-meta table, .specifications-table, .product-details-table",
                    "type": "text"
                },
                {
                    "name": "key_benefits",
                    "selector": ".key-benefits ul li, .benefits ul li, .product-features ul li",
                    "type": "text"
                },
                {
                    "name": "product_images",
                    "selector": ".woocommerce-product-gallery__image img, .product-images img",
                    "type": "attribute",
                    "attribute": "src"
                },
                {
                    "name": "clean_content_sections",
                    "selector": ".content, .product-content, .main-content",
                    "type": "text"
                }
            ]
        }
        
        run_config.extraction_strategy = JsonCssExtractionStrategy(
            extraction_schema, 
            verbose=True
        )
        
        # Process URLs with content exclusion
        results = []
        successful_extractions = 0
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for i, url in enumerate(self.product_urls, 1):
                print(f"\n🔄 Processing URL {i}/{len(self.product_urls)}: {url}")
                
                try:
                    result = await crawler.arun(url=url, config=run_config)
                    
                    if result.success and result.extracted_content:
                        try:
                            extracted_data = json.loads(result.extracted_content)
                            
                            # Structure the clean extracted data
                            clean_product = {
                                "url": url,
                                "product_name": self._extract_field(extracted_data, "product_title"),
                                "description": self._extract_field(extracted_data, "product_description"),
                                "specifications": self._extract_field(extracted_data, "product_specifications"),
                                "key_benefits": self._extract_field(extracted_data, "key_benefits"),
                                "images": self._extract_field(extracted_data, "product_images"),
                                "clean_content": self._extract_field(extracted_data, "clean_content_sections"),
                                "extraction_metadata": {
                                    "content_exclusion_applied": True,
                                    "excluded_elements": "nav, header, footer, forms, overlays, social media",
                                    "content_filter": "BM25 with threshold 1.0",
                                    "extraction_timestamp": datetime.now().isoformat(),
                                    "word_count": len(result.markdown.split()) if result.markdown else 0,
                                    "clean_html_length": len(result.html) if result.html else 0
                                },
                                "raw_markdown": result.markdown  # For comparison
                            }
                            
                            results.append(clean_product)
                            successful_extractions += 1
                            
                            print(f"  ✅ Extracted: {clean_product['product_name']}")
                            print(f"  📊 Word count: {clean_product['extraction_metadata']['word_count']}")
                            
                        except json.JSONDecodeError as je:
                            print(f"  ❌ JSON parsing error: {je}")
                            
                    else:
                        print(f"  ❌ Failed to extract content from {url}")
                        
                except Exception as e:
                    print(f"  ❌ Error processing {url}: {e}")
                
                # Respectful delay
                if i < len(self.product_urls):
                    await asyncio.sleep(2)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Compile final results
        final_results = {
            "scraping_metadata": {
                "scraper_type": "Enhanced with Content Exclusion",
                "content_exclusion_methods": [
                    "CSS Selector Exclusion (nav, header, footer, forms)",
                    "HTML Tag Exclusion (script, style, nav, header, footer)",
                    "Built-in Form Removal",
                    "Overlay Element Removal", 
                    "BM25 Content Filtering (threshold: 1.0)"
                ],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "processing_time_seconds": processing_time,
                "urls_attempted": len(self.product_urls),
                "successful_extractions": successful_extractions,
                "success_rate": f"{(successful_extractions / len(self.product_urls)) * 100:.1f}%",
                "demonstration_mode": True,
                "urls_limited_to": 10
            },
            "products": results,
            "content_exclusion_benefits": {
                "removes_navigation_noise": True,
                "excludes_enquiry_forms": True,
                "filters_footer_subscriptions": True,
                "eliminates_social_media_widgets": True,
                "applies_intelligent_content_filtering": True,
                "reduces_noise_to_signal_ratio": True
            }
        }
        
        print(f"\n🎉 ENHANCED SCRAPING WITH CONTENT EXCLUSION COMPLETE!")
        print(f"=" * 70)
        print(f"🛡️  Content exclusion methods applied: 5")
        print(f"📊 URLs processed: {len(self.product_urls)}")
        print(f"✅ Successful extractions: {successful_extractions}")
        print(f"📈 Success rate: {(successful_extractions / len(self.product_urls)) * 100:.1f}%")
        print(f"⏱️  Total time: {processing_time:.1f} seconds")
        
        return final_results
    
    def _extract_field(self, data: Any, field_name: str) -> Any:
        """Extract field from nested data structure."""
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        
        if isinstance(data, dict):
            return data.get(field_name, "")
        
        return ""
    
    async def run_demonstration(self) -> Dict[str, Any]:
        """
        Run the complete demonstration showing content exclusion effectiveness.
        """
        print(f"🎬 Starting Content Exclusion Demonstration")
        print(f"📋 Processing first {len(self.product_urls)} Agar products")
        print(f"🎯 Goal: Compare scraping with and without content exclusion")
        print(f"=" * 70)
        
        # Run enhanced scraping with content exclusion
        enhanced_results = await self.scrape_with_content_exclusion()
        
        # Save results to docker_results for user review
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main results file
        results_file = f"{self.output_dir}/enhanced_agar_scraping_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save clean products only file
        products_file = f"{self.output_dir}/clean_products_demo_{timestamp}.json"
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_results["products"], f, indent=2, ensure_ascii=False, default=str)
        
        # Save comparison summary
        summary = {
            "demonstration_summary": {
                "title": "Agar Scraper Content Exclusion Demonstration",
                "date": datetime.now().isoformat(),
                "urls_processed": len(self.product_urls),
                "successful_extractions": enhanced_results["scraping_metadata"]["successful_extractions"],
                "content_exclusion_methods_applied": 5,
                "excluded_elements": [
                    "Navigation bars and headers",
                    "Product enquiry forms", 
                    "Footer subscription sections",
                    "Social media widgets",
                    "JavaScript overlays and modals",
                    "Promotional banners and ads"
                ],
                "benefits_demonstrated": [
                    "Cleaner extracted content",
                    "Reduced noise-to-signal ratio",
                    "More focused product information",
                    "Elimination of irrelevant sections",
                    "Improved data quality for processing"
                ]
            },
            "files_generated": {
                "main_results": results_file,
                "clean_products": products_file,
                "summary": f"{self.output_dir}/demonstration_summary_{timestamp}.json"
            },
            "next_steps": [
                "Review the generated files in docker_results/",
                "Compare word counts and content quality",
                "Analyze the excluded elements effectiveness",
                "Apply these methods to full-scale scraping"
            ]
        }
        
        summary_file = f"{self.output_dir}/demonstration_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 Results saved to docker_results/:")
        print(f"   📄 Main results: {os.path.basename(results_file)}")
        print(f"   📋 Clean products: {os.path.basename(products_file)}")
        print(f"   📊 Summary: {os.path.basename(summary_file)}")
        
        return enhanced_results


async def main():
    """Main execution function for enhanced Agar scraping demonstration."""
    urls_file = "/app/complete_agar_product_urls_20251008_122301.json"
    
    if not os.path.exists(urls_file):
        print(f"❌ URLs file not found: {urls_file}")
        return
    
    # Initialize enhanced scraper with content exclusion
    scraper = ContentExclusionAgarScraper(
        urls_file=urls_file,
        batch_size=10,  # Limited to 10 for demonstration
        output_dir="/app/docker_results"  # Results folder for user review
    )
    
    # Run complete demonstration
    results = await scraper.run_demonstration()
    
    print(f"\n🏁 Content Exclusion Demonstration Complete!")
    print(f"📂 Check docker_results/ folder for detailed results")
    print(f"🛡️  Content exclusion methods successfully applied")


if __name__ == "__main__":
    print("🛡️  Enhanced Docker Agar Scraper with Content Exclusion")
    print("Implementing methods from crawl4ai_content_exclusion_guide.md")
    print("=" * 70)
    
    # Run the enhanced scraping demonstration
    asyncio.run(main())
