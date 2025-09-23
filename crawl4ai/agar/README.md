# Agar Product Catalog Scraper for crawl4ai

This module provides a specialized implementation for scraping the Agar product catalog using crawl4ai's advanced web crawling capabilities. It implements the 3DN normalized data model with separate entities for products, media, documents, and categories.

## Features

- **Async web crawling** with crawl4ai's browser automation
- **Normalized JSON output** following the 3DN product model
- **Media processing** (images, videos) with metadata extraction
- **Document handling** (PDFs, datasheets) with type detection
- **Category mapping** with hierarchical relationships
- **Legacy format support** for backward compatibility
- **Comprehensive testing** and validation

## Installation

This module is part of the crawl4ai fork. Ensure you have the required dependencies:

```bash
pip install crawl4ai pydantic
```

## Quick Start

### Basic Usage

```python
import asyncio
from crawl4ai.agar import AgarScraper, ScrapingConfig

async def scrape_agar():
    config = ScrapingConfig(
        base_url="https://agar.com.au/products/",
        max_products=10,
        delay_seconds=1.0,
        verbose=True
    )
    
    scraper = AgarScraper(config)
    catalog_data = await scraper.run_complete_scraping()
    
    print(f"Extracted {len(catalog_data.products)} products")

# Run the scraper
asyncio.run(scrape_agar())
```

### Command Line Interface

```bash
# Basic scraping
python -m crawl4ai.agar.main_agar --base-url https://agar.com.au/products/

# Limit to 10 products with verbose output
python -m crawl4ai.agar.main_agar --base-url https://agar.com.au/products/ --limit 10 --verbose

# Test a single product
python -m crawl4ai.agar.main_agar --test-product https://agar.com.au/product/first-base/ --verbose

# Custom output directory and delay
python -m crawl4ai.agar.main_agar --base-url https://agar.com.au/products/ --output-dir ./agar_data --delay 2.0
```

## Architecture

The Agar scraper is composed of several specialized modules:

### Core Components

1. **AgarScraper** (`agar_scraper.py`) - Main orchestrator
2. **ProductExtractor** (`product_extractor.py`) - Product data extraction
3. **MediaProcessor** (`media_processor.py`) - Image/video processing
4. **DocumentHandler** (`document_handler.py`) - PDF/document handling
5. **CategoryMapper** (`category_mapper.py`) - Category relationships
6. **JSONNormalizer** (`json_normalizer.py`) - Output normalization

### Data Model

The scraper implements a normalized 3DN data model:

```
Products (1) ←→ (M) Media
    ↓
    (M) ←→ (M) Categories
    ↓
    (1) ←→ (M) Documents
```

### Output Structure

The scraper generates separate JSON files:

- `products.json` - Core product information
- `media.json` - Images, videos with metadata
- `documents.json` - PDFs, datasheets with versioning
- `categories.json` - Category hierarchy
- `product_categories.json` - Many-to-many relationships
- `catalog_complete.json` - Combined normalized data
- `catalog_legacy.json` - Backward-compatible format

## Configuration

### ScrapingConfig Parameters

```python
config = ScrapingConfig(
    base_url="https://agar.com.au/products/",  # Required
    max_products=None,                         # Optional limit
    delay_seconds=1.0,                         # Rate limiting
    output_dir="output",                       # Output directory
    use_database=False,                        # Database integration
    verbose=False,                             # Detailed logging
    include_images=True,                       # Process images/videos
    include_documents=True,                    # Process documents
    include_categories=True                    # Process categories
)
```

## Data Schemas

### Product Schema

```python
{
    "product_id": "prod_first-base_a1b2c3d4",
    "product_name": "First Base",
    "product_url": "https://agar.com.au/product/first-base/",
    "description": "Industrial floor cleaner...",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-12-01T14:30:00Z",
    "category_ids": ["cat_floor_care_a1b2c3", "cat_cleaning_d4e5f6"],
    "metadata": {...}
}
```

### Media Schema

```python
{
    "media_id": "med_prod_first-base_001_a1b2c3d4",
    "product_id": "prod_first-base_a1b2c3d4",
    "media_type": "image",
    "media_format": "png",
    "media_url": "https://agar.com.au/wp-content/uploads/First-Base-5L.png",
    "sequence_order": 1,
    "alt_text": "First Base 5L product image",
    "dimensions": {"width": 800, "height": 600},
    "created_at": "2024-01-15T10:00:00Z",
    "metadata": {...}
}
```

### Document Schema

```python
{
    "document_id": "doc_prod_first-base_a1b2c3d4",
    "product_id": "prod_first-base_a1b2c3d4",
    "document_type": "PDS",
    "document_name": "Product Data Sheet",
    "document_url": "https://agar.com.au/product/first-base/?attachment_id=22088",
    "version": "2.1",
    "uploaded_at": "2024-11-20T09:00:00Z",
    "file_size_kb": 245,
    "created_at": "2024-01-15T10:00:00Z",
    "metadata": {...}
}
```

## Advanced Usage

### Single Product Testing

```python
async def test_single_product():
    config = ScrapingConfig(base_url="https://agar.com.au", verbose=True)
    scraper = AgarScraper(config)
    
    result = await scraper.scrape_single_product(
        "https://agar.com.au/product/first-base/"
    )
    
    if result:
        print(f"Product: {result['product']['product_name']}")
        print(f"Media: {len(result['media'])} items")
        print(f"Documents: {len(result['documents'])} items")
        print(f"Categories: {len(result['categories'])} items")
```

### Custom Processing

```python
from crawl4ai.agar import ProductExtractor, MediaProcessor

async def custom_processing():
    config = ScrapingConfig(base_url="https://agar.com.au")
    
    # Extract products only
    extractor = ProductExtractor(config)
    products = await extractor.run_extraction()
    
    # Process media for each product
    processor = MediaProcessor(config)
    all_media = []
    
    for product in products:
        raw_data = product.metadata.get("raw_extracted_data", {})
        media_items = await processor.extract_media_from_product(product, raw_data)
        all_media.extend(media_items)
    
    print(f"Extracted {len(products)} products and {len(all_media)} media items")
```

## Migration from Legacy Agar Scraper

### Key Differences

| Feature | Legacy Scraper | New crawl4ai Scraper |
|---------|----------------|----------------------|
| **Web Engine** | requests + BeautifulSoup | Playwright (async) |
| **Data Model** | Flat JSON structure | Normalized 3DN model |
| **Performance** | Synchronous, slower | Async, concurrent |
| **Reliability** | Basic error handling | Robust retry logic |
| **Output** | Single JSON file | Multiple normalized files |
| **Media** | Basic URL extraction | Metadata + dimensions |
| **Documents** | Simple link detection | Type detection + versioning |
| **Categories** | Basic text extraction | Hierarchical relationships |

### Migration Steps

1. **Update imports:**
   ```python
   # Old
   import catalog_builder
   
   # New
   from crawl4ai.agar import AgarScraper, ScrapingConfig
   ```

2. **Update configuration:**
   ```python
   # Old
   build_catalog(base_url, limit=10, delay=1.0, verbose=True)
   
   # New
   config = ScrapingConfig(
       base_url=base_url, 
       max_products=10, 
       delay_seconds=1.0, 
       verbose=True
   )
   scraper = AgarScraper(config)
   ```

3. **Update execution:**
   ```python
   # Old (sync)
   catalog = build_catalog(base_url)
   
   # New (async)
   catalog_data = await scraper.run_complete_scraping()
   ```

4. **Update data access:**
   ```python
   # Old flat structure
   product = catalog[0]
   images = product['images']
   attachments = product['attachments']['PDS']
   
   # New normalized structure
   product = catalog_data.products[0]
   product_media = [m for m in catalog_data.media if m.product_id == product.product_id]
   product_docs = [d for d in catalog_data.documents if d.product_id == product.product_id and d.document_type == 'PDS']
   ```

### Backward Compatibility

The scraper generates a legacy format file (`catalog_legacy.json`) that matches the old structure:

```python
# Access legacy format
normalizer = JSONNormalizer("output")
legacy_file = normalizer.save_legacy_format(catalog_data)

# Legacy format maintains old structure
with open(legacy_file, 'r') as f:
    legacy_data = json.load(f)
    
# Use with existing tools
for product in legacy_data:
    print(product['name'])  # Old field names preserved
    print(len(product['images']))
    print(len(product['attachments']['PDS']))
```

## Testing

Run the test suite to validate functionality:

```bash
python -m crawl4ai.agar.test_agar
```

The test suite covers:

- ID generation functions
- Utility functions (text cleaning, type detection)
- Schema validation
- JSON normalization
- Configuration handling

## Troubleshooting

### Common Issues

1. **Browser installation:**
   ```bash
   python -m playwright install chromium
   ```

2. **Memory issues with large catalogs:**
   ```python
   config = ScrapingConfig(
       max_products=100,  # Limit products
       delay_seconds=2.0  # Increase delay
   )
   ```

3. **Network timeouts:**
   ```python
   # Increase delays for slow networks
   config = ScrapingConfig(delay_seconds=3.0)
   ```

4. **Missing dependencies:**
   ```bash
   pip install pydantic crawl4ai playwright
   ```

### Debug Mode

Enable verbose logging for troubleshooting:

```python
config = ScrapingConfig(verbose=True)
```

This will print detailed progress information including:
- URL discovery process
- Product extraction details
- Media/document processing
- Error messages and stack traces

## Contributing

The Agar scraper module follows standard Python development practices:

- **Type hints** for all functions
- **Pydantic models** for data validation
- **Async/await** for concurrent processing
- **Error handling** with meaningful messages
- **Comprehensive logging** for debugging
- **Unit tests** for validation

## License

This module is part of the crawl4ai project and follows the same licensing terms.
