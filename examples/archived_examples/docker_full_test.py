#!/usr/bin/env python3
"""
Complete Docker Test - Shows basic crawling + full LLM extraction
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.async_configs import LLMConfig

def load_env_file(env_file_path="/app/.llm.env"):
    """Load environment variables from .llm.env file."""
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print(f"✅ Loaded environment variables from {env_file_path}")
    else:
        print(f"⚠️  Environment file not found: {env_file_path}")

# Load environment variables at script start
load_env_file()

async def test_basic_crawling():
    """Test basic crawling without LLM extraction."""
    print("🧪 Testing basic crawling (no LLM extraction)...")
    
    test_url = "https://agar.com.au/product/everfresh/"
    
    try:
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=test_url,
                bypass_cache=True,
                only_text=True
            )
            
            if result.success:
                print("✅ Basic crawling successful")
                print(f"📊 Content length: {len(result.cleaned_html)} characters")
                print(f"📄 First 300 chars: {result.cleaned_html[:300]}...")
                
                # Look for product-specific content
                if "everfresh" in result.cleaned_html.lower():
                    print("✅ Product content detected")
                else:
                    print("⚠️  Product content not clearly detected")
                
                return True
            else:
                print(f"❌ Basic crawling failed: {result.error_message}")
                return False
                
    except Exception as e:
        print(f"❌ Basic crawling test failed: {e}")
        return False

async def test_llm_extraction():
    """Test full LLM extraction with Technical Brief v1.0 schema."""
    print("\n🧪 Testing LLM extraction with Technical Brief v1.0 schema...")
    
    test_url = "https://agar.com.au/product/everfresh/"
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"🔑 API key found: {api_key[:20]}..." if api_key else "❌ No API key")
    if not api_key or api_key == "YOUR_OPENAI_API":
        print("⚠️  OPENAI_API_KEY not properly configured")
        print("💡 To enable LLM extraction, set your API key in .llm.env file")
        return False
    
    try:
        # Technical Brief v1.0 Schema
        schema = {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "product_url": {"type": "string"},
                "codes": {"type": "array", "items": {"type": "string"}},
                "skus": {"type": "array", "items": {"type": "string"}},
                "categories": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}},
                "sizes": {"type": "array", "items": {"type": "string"}},
                "specifications": {"type": "object"},
                "key_benefits": {"type": "array", "items": {"type": "string"}},
                "description": {
                    "type": "object",
                    "properties": {
                        "overview": {"type": "string"},
                        "how_it_works": {"type": "string"},
                        "applications": {"type": "string"}
                    }
                },
                "images": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "url": {"type": "string"},
                            "alt_text": {"type": "string"}
                        }
                    }
                },
                "scraped_at": {"type": "string"}
            }
        }
        
        # Create LLM config
        print(f"🤖 Setting up LLM config with provider: openai/gpt-4o-mini")
        llm_config = LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=api_key
        )
        print(f"✅ LLM config created successfully")
        
        extraction_strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            schema=schema,
            extraction_type="schema",
            instruction="""
            Extract structured product information from this Agar cleaning product page following Technical Brief v1.0 requirements.
            
            Focus on extracting:
            1. Product name and complete description
            2. All product codes, SKUs, and categories
            3. Key benefits (bullet points from the page)
            4. Technical specifications (pH, perfume, etc.)
            5. Available sizes and packaging options
            6. Product images with alt text
            7. Usage instructions and applications
            
            Structure the description into:
            - overview: Main product description
            - how_it_works: Technical explanation if available
            - applications: Usage scenarios and surfaces
            
            Return valid JSON matching the exact schema provided.
            """
        )
        
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=test_url,
                extraction_strategy=extraction_strategy,
                bypass_cache=True,
                process_iframes=False,
                remove_overlay_elements=True,
                simulate_user=True,
                override_navigator=True
            )
            
            print(f"🔍 Extraction result - Success: {result.success}")
            if result.error_message:
                print(f"❌ Error message: {result.error_message}")
            if hasattr(result, 'extracted_content'):
                print(f"📄 Extracted content length: {len(result.extracted_content) if result.extracted_content else 0}")
                if result.extracted_content:
                    print(f"📄 First 200 chars: {result.extracted_content[:200]}...")
            
            if result.success and result.extracted_content:
                print("✅ LLM extraction successful")
                
                try:
                    product_data = json.loads(result.extracted_content)
                    
                    print(f"📊 Technical Brief v1.0 Schema Compliance Check:")
                    print(f"   ✅ Product Name: {product_data.get('product_name', 'N/A')}")
                    print(f"   ✅ Product URL: {product_data.get('product_url', 'N/A')}")
                    print(f"   ✅ Categories: {len(product_data.get('categories', []))} items")
                    print(f"   ✅ Key Benefits: {len(product_data.get('key_benefits', []))} items")
                    print(f"   ✅ Specifications: {len(product_data.get('specifications', {}))} items")
                    print(f"   ✅ Images: {len(product_data.get('images', []))} items")
                    
                    # Save the extracted data
                    output_file = "/app/agar_batch_output/test_extraction_technical_brief_v1.json"
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(product_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"💾 Full extraction saved to: {output_file}")
                    print(f"\n📄 Sample extracted data:")
                    print(json.dumps(product_data, indent=2)[:500] + "...")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"📄 Raw extracted content: {result.extracted_content}")
                    return False
            else:
                print(f"❌ LLM extraction failed")
                print(f"   Success: {result.success}")
                print(f"   Error: {result.error_message if result.error_message else 'No error message'}")
                print(f"   Content: {result.extracted_content if hasattr(result, 'extracted_content') else 'No content'}")
                return False
                
    except Exception as e:
        print(f"❌ LLM extraction test failed: {e}")
        return False

async def main():
    """Run comprehensive Docker tests."""
    print("🐳 Comprehensive Docker Test Suite")
    print("=" * 60)
    
    # Test 1: Basic crawling
    basic_success = await test_basic_crawling()
    
    # Test 2: LLM extraction
    llm_success = await test_llm_extraction()
    
    print(f"\n🏁 Test Results Summary:")
    print(f"   Basic crawling: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"   LLM extraction: {'✅ PASS' if llm_success else '❌ FAIL (likely API key issue)'}")
    
    if basic_success and llm_success:
        print(f"\n🎉 ALL TESTS PASSED - Ready for batch processing 189 URLs!")
    elif basic_success:
        print(f"\n⚠️  Crawling works, but LLM extraction needs API key setup")
        print(f"💡 Edit .llm.env and replace 'YOUR_OPENAI_API' with your actual OpenAI API key")
    else:
        print(f"\n❌ Basic crawling issues need investigation")

if __name__ == "__main__":
    asyncio.run(main())
