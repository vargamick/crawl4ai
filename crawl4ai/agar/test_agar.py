"""
Test script for the Agar scraper implementation.

This script provides basic tests to validate the functionality of the Agar scraper
without requiring access to the actual Agar website.
"""

import asyncio
import json
import tempfile
import os
from datetime import datetime

from .schemas import ScrapingConfig, ProductSchema, MediaSchema, DocumentSchema, CategorySchema
from .utils import (
    generate_product_id, generate_media_id, generate_document_id, 
    generate_category_id, clean_text, detect_document_type, detect_media_format
)
from .json_normalizer import JSONNormalizer


def test_id_generation():
    """Test ID generation functions."""
    print("Testing ID generation...")
    
    # Test product ID generation
    product_url = "https://agar.com.au/product/first-base/"
    product_id = generate_product_id(product_url)
    print(f"  Product ID: {product_id}")
    assert product_id.startswith("prod_"), "Product ID should start with prod_"
    
    # Test media ID generation
    media_id = generate_media_id(product_id, "https://example.com/image.jpg", 1)
    print(f"  Media ID: {media_id}")
    assert media_id.startswith("med_"), "Media ID should start with med_"
    
    # Test document ID generation
    doc_id = generate_document_id(product_id, "https://example.com/datasheet.pdf")
    print(f"  Document ID: {doc_id}")
    assert doc_id.startswith("doc_"), "Document ID should start with doc_"
    
    # Test category ID generation
    cat_id = generate_category_id("Cleaning Products")
    print(f"  Category ID: {cat_id}")
    assert cat_id.startswith("cat_"), "Category ID should start with cat_"
    
    print("  ✓ ID generation tests passed")


def test_utility_functions():
    """Test utility functions."""
    print("Testing utility functions...")
    
    # Test text cleaning
    dirty_text = "  This is   dirty text  with  &nbsp; HTML entities  "
    clean = clean_text(dirty_text)
    print(f"  Clean text: '{clean}'")
    assert clean == "This is dirty text with HTML entities", "Text cleaning failed"
    
    # Test document type detection
    doc_type = detect_document_type("safety_data_sheet.pdf", "Safety Data Sheet")
    print(f"  Document type: {doc_type}")
    assert doc_type == "SDS", "Should detect SDS document type"
    
    # Test media format detection
    media_format = detect_media_format("https://example.com/image.jpg")
    print(f"  Media format: {media_format}")
    assert media_format == "jpg", "Should detect JPG format"
    
    print("  ✓ Utility function tests passed")


def test_schema_validation():
    """Test Pydantic schema validation."""
    print("Testing schema validation...")
    
    # Test ProductSchema
    try:
        product = ProductSchema(
            product_id="prod_test_123",
            product_name="Test Product",
            product_url="https://example.com/product/test",
            description="A test product"
        )
        print(f"  Product schema: {product.product_name}")
        assert product.product_id == "prod_test_123", "Product ID mismatch"
    except Exception as e:
        print(f"  ✗ Product schema validation failed: {e}")
        raise
    
    # Test MediaSchema
    try:
        media = MediaSchema(
            media_id="med_test_001",
            product_id="prod_test_123",
            media_type="image",
            media_format="jpg",
            media_url="https://example.com/image.jpg"
        )
        print(f"  Media schema: {media.media_type}/{media.media_format}")
        assert media.media_type == "image", "Media type mismatch"
    except Exception as e:
        print(f"  ✗ Media schema validation failed: {e}")
        raise
    
    # Test DocumentSchema
    try:
        document = DocumentSchema(
            document_id="doc_test_001",
            product_id="prod_test_123",
            document_type="PDS",
            document_name="Product Data Sheet",
            document_url="https://example.com/datasheet.pdf"
        )
        print(f"  Document schema: {document.document_type}")
        assert document.document_type == "PDS", "Document type mismatch"
    except Exception as e:
        print(f"  ✗ Document schema validation failed: {e}")
        raise
    
    # Test CategorySchema
    try:
        category = CategorySchema(
            category_id="cat_test_001",
            category_name="Test Category"
        )
        print(f"  Category schema: {category.category_name}")
        assert category.category_name == "Test Category", "Category name mismatch"
    except Exception as e:
        print(f"  ✗ Category schema validation failed: {e}")
        raise
    
    print("  ✓ Schema validation tests passed")


def test_json_normalization():
    """Test JSON normalization and output."""
    print("Testing JSON normalization...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        normalizer = JSONNormalizer(temp_dir)
        
        # Create test data
        products = [ProductSchema(
            product_id="prod_test_123",
            product_name="Test Product",
            product_url="https://example.com/product/test"
        )]
        
        media = [MediaSchema(
            media_id="med_test_001",
            product_id="prod_test_123",
            media_type="image",
            media_format="jpg",
            media_url="https://example.com/image.jpg"
        )]
        
        documents = [DocumentSchema(
            document_id="doc_test_001",
            product_id="prod_test_123",
            document_type="PDS",
            document_name="Test Data Sheet",
            document_url="https://example.com/datasheet.pdf"
        )]
        
        categories = [CategorySchema(
            category_id="cat_test_001",
            category_name="Test Category"
        )]
        
        product_categories = []
        
        # Test normalization
        catalog_data = normalizer.normalize_catalog_data(
            products=products,
            media=media,
            documents=documents,
            categories=categories,
            product_categories=product_categories
        )
        
        print(f"  Normalized data: {len(catalog_data.products)} products")
        assert len(catalog_data.products) == 1, "Should have 1 product"
        
        # Test file saving
        saved_files = normalizer.save_normalized_files(catalog_data)
        print(f"  Saved {len(saved_files)} files")
        assert len(saved_files) > 0, "Should save at least one file"
        
        # Verify files were created
        for file_type, filepath in saved_files.items():
            assert os.path.exists(filepath), f"File {filepath} was not created"
            
            # Test that JSON is valid
            with open(filepath, 'r') as f:
                data = json.load(f)
                assert isinstance(data, (dict, list)), "Should be valid JSON"
        
        print("  ✓ JSON normalization tests passed")


def test_configuration():
    """Test configuration handling."""
    print("Testing configuration...")
    
    # Test valid configuration
    try:
        config = ScrapingConfig(
            base_url="https://agar.com.au/products/",
            max_products=10,
            delay_seconds=1.0,
            output_dir="test_output",
            verbose=True
        )
        print(f"  Config created: base_url={config.base_url}")
        assert str(config.base_url) == "https://agar.com.au/products/", "Base URL mismatch"
        assert config.max_products == 10, "Max products mismatch"
    except Exception as e:
        print(f"  ✗ Configuration validation failed: {e}")
        raise
    
    print("  ✓ Configuration tests passed")


async def run_all_tests():
    """Run all tests."""
    print("Starting Agar scraper tests...\n")
    
    try:
        test_id_generation()
        print()
        
        test_utility_functions()
        print()
        
        test_schema_validation()
        print()
        
        test_json_normalization()
        print()
        
        test_configuration()
        print()
        
        print("🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner."""
    success = asyncio.run(run_all_tests())
    if not success:
        exit(1)


if __name__ == "__main__":
    main()
