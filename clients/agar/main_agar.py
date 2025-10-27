"""
Main entry point for Agar product catalog scraping using crawl4ai.

This script provides a command-line interface that's compatible with the existing
Agar project structure while using the new crawl4ai-based scraping system.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from .schemas import ScrapingConfig
from .agar_scraper import AgarScraper


def create_config_from_args(args) -> ScrapingConfig:
    """
    Create a ScrapingConfig from command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        ScrapingConfig object
    """
    return ScrapingConfig(
        base_url=args.base_url,
        max_products=args.limit,
        delay_seconds=args.delay,
        output_dir=args.output_dir,
        use_database=args.use_db,
        verbose=args.verbose,
        include_images=not args.no_images,
        include_documents=not args.no_documents,
        include_categories=not args.no_categories
    )


async def run_scraping(config: ScrapingConfig) -> None:
    """
    Run the scraping process.
    
    Args:
        config: Scraping configuration
    """
    scraper = AgarScraper(config)
    
    try:
        catalog_data = await scraper.run_complete_scraping()
        
        # Print summary
        summary = scraper.get_extraction_summary()
        print("\n" + "="*50)
        print("EXTRACTION SUMMARY")
        print("="*50)
        print(f"Total products: {summary['total_products']}")
        print(f"Total media items: {summary['total_media']}")
        print(f"Total documents: {summary['total_documents']}")
        print(f"Total categories: {summary['total_categories']}")
        print(f"Total relationships: {summary['total_relationships']}")
        print(f"Products with media: {summary['products_with_media']}")
        print(f"Products with documents: {summary['products_with_documents']}")
        print(f"Products with categories: {summary['products_with_categories']}")
        print("="*50)
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


async def test_single_product(url: str, config: ScrapingConfig) -> None:
    """
    Test scraping a single product.
    
    Args:
        url: Product URL to test
        config: Scraping configuration
    """
    scraper = AgarScraper(config)
    
    print(f"Testing single product: {url}")
    result = await scraper.scrape_single_product(url)
    
    if result:
        print("\nTest Results:")
        print(f"Product: {result['product']['product_name']}")
        print(f"Media items: {len(result['media'])}")
        print(f"Documents: {len(result['documents'])}")
        print(f"Categories: {len(result['categories'])}")
        print(f"Relationships: {len(result['relationships'])}")
        
        if config.verbose:
            print("\nDetailed Results:")
            print(f"Product data: {result['product']}")
            if result['media']:
                print(f"Media: {result['media']}")
            if result['documents']:
                print(f"Documents: {result['documents']}")
            if result['categories']:
                print(f"Categories: {result['categories']}")
    else:
        print("Failed to extract product data")


def prompt_for_input(prompt_text: str, default: Optional[str] = None) -> str:
    """
    Prompt the user for input with an optional default value.
    
    Args:
        prompt_text: Text to display to the user
        default: Optional default value
        
    Returns:
        User input or default value
    """
    if default:
        user_input = input(f"{prompt_text} [{default}]: ")
        return user_input if user_input.strip() else default
    else:
        while True:
            user_input = input(f"{prompt_text}: ")
            if user_input.strip():
                return user_input
            print("This field is required. Please enter a value.")


def main():
    """
    Main entry point for the application.
    """
    parser = argparse.ArgumentParser(
        description="Agar Product Catalog Scraper using crawl4ai",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scraping
  python -m crawl4ai.agar.main_agar --base-url https://agar.com.au/products/

  # Limit to 10 products with verbose output
  python -m crawl4ai.agar.main_agar --base-url https://agar.com.au/products/ --limit 10 --verbose

  # Test a single product
  python -m crawl4ai.agar.main_agar --test-product https://agar.com.au/product/first-base/ --verbose

  # Custom output directory and delay
  python -m crawl4ai.agar.main_agar --base-url https://agar.com.au/products/ --output-dir ./agar_data --delay 2.0
        """
    )
    
    # URL arguments
    parser.add_argument(
        "--base-url", 
        help="Base URL to start crawling (will prompt if not provided)"
    )
    parser.add_argument(
        "--test-product", 
        help="Test scraping a single product URL"
    )
    
    # Output arguments
    parser.add_argument(
        "--output-dir", 
        default="output",
        help="Output directory for JSON files (default: output)"
    )
    
    # Scraping control
    parser.add_argument(
        "--limit", 
        type=int, 
        help="Limit the number of products to process"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)"
    )
    
    # Feature toggles
    parser.add_argument(
        "--no-images", 
        action="store_true",
        help="Skip image/media extraction"
    )
    parser.add_argument(
        "--no-documents", 
        action="store_true",
        help="Skip document extraction"
    )
    parser.add_argument(
        "--no-categories", 
        action="store_true",
        help="Skip category extraction"
    )
    
    # Database (placeholder for future implementation)
    parser.add_argument(
        "--use-db", 
        action="store_true",
        help="Use database for storage (not yet implemented)"
    )
    
    # Output control
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Print detailed progress information"
    )
    
    args = parser.parse_args()
    
    # Handle test mode
    if args.test_product:
        if not args.test_product.startswith('http'):
            print("Error: Test product URL must be a valid HTTP/HTTPS URL")
            sys.exit(1)
        
        config = ScrapingConfig(
            base_url="https://agar.com.au",  # Dummy base URL for test
            verbose=args.verbose,
            include_images=not args.no_images,
            include_documents=not args.no_documents,
            include_categories=not args.no_categories
        )
        
        asyncio.run(test_single_product(args.test_product, config))
        return
    
    # Prompt for base URL if not provided
    if not args.base_url:
        args.base_url = prompt_for_input(
            "Enter base URL to start crawling",
            "https://agar.com.au/products/"
        )
    
    # Validate base URL
    if not args.base_url.startswith('http'):
        print("Error: Base URL must be a valid HTTP/HTTPS URL")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Print configuration
    if args.verbose:
        print("Crawl4ai Agar Scraper Configuration:")
        print(f"  Base URL: {config.base_url}")
        print(f"  Max products: {config.max_products or 'unlimited'}")
        print(f"  Output directory: {config.output_dir}")
        print(f"  Delay: {config.delay_seconds}s")
        print(f"  Include images: {config.include_images}")
        print(f"  Include documents: {config.include_documents}")
        print(f"  Include categories: {config.include_categories}")
        print(f"  Database: {'enabled' if config.use_database else 'disabled'}")
        print()
    
    # Run scraping
    try:
        asyncio.run(run_scraping(config))
        print("\nScraping completed successfully!")
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
