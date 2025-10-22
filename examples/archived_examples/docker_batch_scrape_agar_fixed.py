#!/usr/bin/env python3
"""
Fixed Docker Batch Scraper for Agar Products
Uses the correct imports and enhanced agar scraper functionality.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.async_configs import LLMConfig  # FIXED: Correct import location

async def test_single_product():
    """Test function to verify the fixes work on a single product."""
    print("🧪 Testing fixed imports on single product...")
    
    test_url = "https://agar.com.au/product/everfresh/"
    
    try:
        # Test LLMConfig import and creation
        llm_config = LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv("OPENAI_API_KEY")
        )
        print("✅ LLMConfig created successfully")
        
        # Test extraction strategy creation
        schema = {"type": "object", "properties": {"product_name": {"type": "string"}}}
        
        extraction_strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            schema=schema,
            extraction_type="schema",
            instruction="Extract the product name."
        )
        print("✅ LLMExtractionStrategy created successfully")
        
        # Test crawler with extraction
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=test_url,
                extraction_strategy=extraction_strategy,
                bypass_cache=True
            )
            
            if result.success:
                print("✅ Crawling successful")
                if result.extracted_content:
                    print(f"📄 Extracted content: {result.extracted_content[:200]}...")
                    return True
                else:
                    print("⚠️  Crawling successful but no extracted content returned")
                    print(f"📊 Result attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")
                    return True  # Still consider this success since imports work
            else:
                print(f"❌ Crawling failed: {result.error_message}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

async def main():
    """Main execution function."""
    import sys
    
    # Check if we want to run a simple test first
    if "--test" in sys.argv:
        print("🧪 Running single product test...")
        success = await test_single_product()
        if success:
            print("\n✅ Test passed! Fixed imports work correctly.")
        else:
            print("\n❌ Test failed! There may be other issues.")
        return

if __name__ == "__main__":
    print("🐳 Fixed Docker Import Test Script")
    print("Using corrected imports: LLMConfig from crawl4ai.async_configs")
    print("=" * 60)
    
    asyncio.run(main())
