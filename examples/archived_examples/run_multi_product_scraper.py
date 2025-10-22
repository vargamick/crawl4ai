#!/usr/bin/env python3
"""
Runner script for the Multi-Product Scraper
Uses configuration file to process specific product groups
"""

import json
import sys
import os
from multi_product_scraper import MultiProductScraper

def load_product_urls(config_file: str = "product_urls.json") -> dict:
    """Load product URLs from configuration file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in configuration file '{config_file}'")
        return {}

def display_available_groups(config: dict):
    """Display available product groups"""
    print("Available product groups:")
    for group_name, products in config.items():
        print(f"  - {group_name}: {len(products)} products")
        for product in products[:3]:  # Show first 3 products
            print(f"    • {product['name']}")
        if len(products) > 3:
            print(f"    ... and {len(products) - 3} more")

def main():
    """Main execution function"""
    # Load configuration
    config = load_product_urls()
    if not config:
        return 1
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python run_multi_product_scraper.py <group_name> [output_dir]")
        print("       python run_multi_product_scraper.py --list (to show available groups)")
        print("       python run_multi_product_scraper.py --all [output_dir] (to process all groups)")
        return 1
    
    # Handle special commands
    if sys.argv[1] == "--list":
        display_available_groups(config)
        return 0
    
    # Set up parameters
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "agar_products"
    
    # Initialize scraper
    scraper = MultiProductScraper(crawl4ai_url="http://localhost:11235")
    
    # Process based on command
    if sys.argv[1] == "--all":
        # Process all groups
        all_files = []
        for group_name, products in config.items():
            print(f"\n{'='*60}")
            print(f"Processing group: {group_name}")
            print(f"{'='*60}")
            
            urls = [product['url'] for product in products]
            group_output_dir = os.path.join(output_dir, group_name)
            
            generated_files = scraper.process_multiple_urls(urls, group_output_dir)
            all_files.extend(generated_files)
            
            print(f"Completed {group_name}: {len(generated_files)} documents generated")
        
        print(f"\n{'='*60}")
        print(f"ALL GROUPS COMPLETED!")
        print(f"Total documents generated: {len(all_files)}")
        print(f"{'='*60}")
        
    else:
        # Process specific group
        group_name = sys.argv[1]
        
        if group_name not in config:
            print(f"Error: Group '{group_name}' not found in configuration")
            print("Available groups:")
            for available_group in config.keys():
                print(f"  - {available_group}")
            return 1
        
        products = config[group_name]
        urls = [product['url'] for product in products]
        
        print(f"Processing group: {group_name}")
        print(f"Products to extract: {len(urls)}")
        for product in products:
            print(f"  - {product['name']} ({product['category']})")
        
        print(f"\nStarting extraction...")
        generated_files = scraper.process_multiple_urls(urls, output_dir)
        
        print(f"\nCompleted! Generated {len(generated_files)} documents:")
        for filepath in generated_files:
            print(f"  - {filepath}")
    
    return 0

if __name__ == "__main__":
    exit(main())
