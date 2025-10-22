#!/usr/bin/env python3
"""
Test script for the Multi-Product Scraper
Demonstrates the functionality and provides usage instructions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_product_scraper import MultiProductScraper
import json

def demo_functionality():
    """
    Demonstrate the multi-product scraper functionality
    """
    print("="*60)
    print("MULTI-PRODUCT SCRAPER DEMO")
    print("="*60)
    
    # Initialize scraper
    scraper = MultiProductScraper(crawl4ai_url="http://localhost:11235")
    
    print("\n1. SCRAPER INITIALIZED")
    print(f"   - Crawl4AI URL: {scraper.crawl4ai_url}")
    print(f"   - Extraction Date: {scraper.extraction_date}")
    
    print("\n2. SAMPLE CONFIGURATION")
    # Load and display sample URLs
    try:
        with open('product_urls.json', 'r') as f:
            config = json.load(f)
        
        print(f"   - Available groups: {list(config.keys())}")
        for group_name, products in config.items():
            print(f"   - {group_name}: {len(products)} products")
            
    except FileNotFoundError:
        print("   - Configuration file not found")
    
    print("\n3. USAGE EXAMPLES")
    print("   To test the scraper when Docker network is running:")
    print("   ")
    print("   # Process a specific group:")
    print("   python run_multi_product_scraper.py agar_sample_products")
    print("   ")
    print("   # Process all groups:")
    print("   python run_multi_product_scraper.py --all")
    print("   ")
    print("   # List available groups:")
    print("   python run_multi_product_scraper.py --list")
    print("   ")
    print("   # Process to custom directory:")
    print("   python run_multi_product_scraper.py floor_care_products output/floor_care")
    
    print("\n4. EXPECTED OUTPUT STRUCTURE")
    print("   Each product generates a document following the simplified template:")
    print("   - Source Information")
    print("   - Product Information (Core Details, Description, Benefits, Usage)")
    print("   - Technical Specifications Table")
    print("   - Media Assets Extracted")
    print("   - Product Categories & Related Products")
    print("   - Website Structure Analysis")
    print("   - Data Extraction Statistics")
    print("   - JSON Structure Sample")
    print("   - Recommendations")
    print("   - Conclusion")
    
    print("\n5. DOCUMENT NAMING")
    print("   Generated files follow pattern: {product_name}_extraction_report.md")
    print("   Examples:")
    print("   - autobrite_extraction_report.md")
    print("   - carpet_genie_extraction_report.md")
    print("   - shine_it_extraction_report.md")
    
    print("\n6. DOCKER NETWORK REQUIREMENT")
    print("   Before running, ensure Docker network is operational:")
    print("   docker-compose -f docker-compose-network.yml up -d")
    print("   docker-compose -f docker-compose-network.yml ps")
    
    print("\n7. KEY IMPROVEMENTS FROM ORIGINAL")
    print("   ✓ Processes multiple URLs automatically")
    print("   ✓ Generates individual documents per product")
    print("   ✓ Uses simplified template (removes executive summary, company info, SEO metadata)")
    print("   ✓ Configurable product groups")
    print("   ✓ Batch processing with error handling")
    print("   ✓ Progress tracking and status reporting")
    
    print("\n8. SUPPORTED EXTRACTION FEATURES")
    print("   ✓ Core product details (SKU, size, pH level, category)")
    print("   ✓ Product descriptions and benefits")
    print("   ✓ Usage applications and specifications") 
    print("   ✓ Media assets (product images with dimensions)")
    print("   ✓ Website structure and quality metrics")
    print("   ✓ Data extraction statistics")
    print("   ✓ JSON structure samples")
    print("   ✓ Comprehensive recommendations")
    
    print(f"\n{'='*60}")
    print("Multi-Product Scraper is ready for use!")
    print("Start Docker network and run with your desired product group.")
    print(f"{'='*60}")

def create_sample_output():
    """Create a sample output document to show expected format"""
    
    sample_product_data = {
        "url": "https://agar.com.au/product/autobrite/",
        "extraction_date": "22/10/2025",
        "product_name": "Autobrite",
        "product_details": {
            "sku": "AUB5",
            "size": "5L", 
            "ph_level": "10.6 +/- 0.5",
            "category": "Floor Maintainers",
            "product_type": "Floor cleaner and restorer",
            "description": "AUTOBRITE is a unique floor cleaner and restorer which cleans effectively and simultaneously replenishes the floor surface with acrylic polish.",
            "benefits": [
                "Convenient, two-in-one product that polishes and cleans in one operation",
                "Creates beautiful, glossy film of floor polish when used regularly"
            ],
            "usage_applications": [
                "Vinyl floors",
                "Timber floors",
                "Terrazzo floors", 
                "Quarry tile floors",
                "Ceramic-tile floors"
            ]
        },
        "media_assets": {
            "product_images": [
                {
                    "url": "https://agar.com.au/wp-content/uploads/2023/08/Autobrite-5L-1000x1000.png",
                    "dimensions": "1000x1000px",
                    "format": "PNG",
                    "description": "Main Product Image (5L)"
                }
            ]
        },
        "statistics": {
            "total_links_internal": 106,
            "total_links_external": 4,
            "images_extracted": 6,
            "tables_extracted": 1,
            "processing_time": "~2 seconds",
            "success_rate": "100%"
        }
    }
    
    scraper = MultiProductScraper()
    sample_doc = scraper.generate_document(sample_product_data)
    
    os.makedirs('sample_output', exist_ok=True)
    with open('sample_output/autobrite_sample_extraction_report.md', 'w', encoding='utf-8') as f:
        f.write(sample_doc)
    
    print(f"Sample document created: sample_output/autobrite_sample_extraction_report.md")

if __name__ == "__main__":
    demo_functionality()
    print("\nGenerating sample output document...")
    create_sample_output()
