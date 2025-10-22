#!/usr/bin/env python3
"""
Simple LLM Test - Just basic LLM extraction without complex schema
"""

import asyncio
import json
import os
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

async def test_simple_llm():
    """Test basic LLM extraction with simple instruction."""
    print("🧪 Testing simple LLM extraction...")
    
    test_url = "https://agar.com.au/product/everfresh/"
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"🔑 API key found: {api_key[:20]}..." if api_key else "❌ No API key")
    if not api_key or api_key == "YOUR_OPENAI_API":
        print("⚠️  OPENAI_API_KEY not properly configured")
        return False
    
    try:
        # Simple LLM config
        print(f"🤖 Setting up LLM config with provider: openai/gpt-4o-mini")
        llm_config = LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=api_key
        )
        print(f"✅ LLM config created successfully")
        
        # Simple extraction strategy - just get product name
        extraction_strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            instruction="Extract the product name from this Agar cleaning product page. Return just the product name as plain text, no JSON.",
            extraction_type="text"
        )
        print(f"✅ Extraction strategy created")
        
        async with AsyncWebCrawler(verbose=True) as crawler:
            print(f"🕷️  Starting crawl with LLM extraction...")
            result = await crawler.arun(
                url=test_url,
                extraction_strategy=extraction_strategy,
                bypass_cache=True
            )
            
            print(f"🔍 Crawl completed")
            print(f"   Success: {result.success}")
            print(f"   Error: {result.error_message if result.error_message else 'None'}")
            
            if hasattr(result, 'extracted_content'):
                print(f"   Extracted content: {result.extracted_content}")
            else:
                print(f"   No extracted_content attribute")
            
            if result.success and result.extracted_content:
                print("✅ Simple LLM extraction successful!")
                print(f"📄 Extracted: {result.extracted_content}")
                return True
            else:
                print("❌ Simple LLM extraction failed")
                return False
                
    except Exception as e:
        print(f"❌ Simple LLM test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run simple LLM test."""
    print("🐳 Simple LLM Test")
    print("=" * 40)
    
    success = await test_simple_llm()
    
    print(f"\n🏁 Result: {'✅ PASS' if success else '❌ FAIL'}")

if __name__ == "__main__":
    asyncio.run(main())
