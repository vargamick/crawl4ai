# Agar URL Extractor Guide

## Overview

The **Agar URL Extractor** is a focused tool for building comprehensive Agar product URL extraction files. It extracts the category discovery and URL generation components from the full processing pipeline to create a streamlined solution specifically for building product URL files that can be consumed by other scraping tools.

## Key Features

- **Discovers product categories** from Agar website navigation automatically
- **Generates comprehensive product URL lists** with category associations  
- **Handles pagination automatically** to find all products in each category
- **Outputs clean JSON files** ready for consumption by scraping systems
- **Configurable processing parameters** (batch sizes, limits, delays, etc.)
- **Robust error handling** with detailed logging
- **CLI interface** with comprehensive argument parsing

## Installation & Requirements

### Prerequisites

- Python 3.8+
- crawl4ai library installed
- PyYAML for configuration file support

### Install Dependencies

```bash
pip install crawl4ai pyyaml
```

## Usage

### Basic Usage

```bash
# Run with default settings
python clients/agar/scripts/agar_url_extractor.py

# Specify output directory
python clients/agar/scripts/agar_url_extractor.py --output-dir my_agar_urls

# Use configuration file
python clients/agar/scripts/agar_url_extractor.py --config clients/agar/config/url_extraction_config.yaml

# Enable verbose logging
python clients/agar/scripts/agar_url_extractor.py --verbose
```

### Advanced Usage

```bash
# Limit categories and products for testing
python clients/agar/scripts/agar_url_extractor.py --max-categories 10 --max-products 100

# Adjust processing parameters
python clients/agar/scripts/agar_url_extractor.py --batch-size 25 --delay 2.0 --max-pages 10

# Create sample configuration file
python clients/agar/scripts/agar_url_extractor.py --create-config
```

## Command Line Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--config`, `-c` | str | None | Configuration file (YAML or JSON) |
| `--create-config` | flag | False | Create sample configuration file |
| `--output-dir` | str | `agar_url_data` | Output directory for URL extraction data |
| `--base-url` | str | `https://agar.com.au` | Base URL for Agar website |
| `--batch-size` | int | 50 | Batch size for processing |
| `--max-categories` | int | 50 | Maximum number of categories to discover |
| `--max-products` | int | 1000 | Maximum products per category |
| `--max-pages` | int | 20 | Maximum pages per category |
| `--delay` | float | 1.0 | Delay between requests (seconds) |
| `--verbose`, `-v` | flag | False | Enable verbose logging |

## Configuration File

### Sample Configuration (`url_extraction_config.yaml`)

```yaml
# Agar URL Extractor Configuration
base_url: "https://agar.com.au"
output_dir: "clients/agar/agar_url_data"

# Category Discovery Settings
max_categories: 50
common_category_paths:
  - "/products"
  - "/categories" 
  - "/cleaning-products"
  - "/professional-cleaning"
  - "/commercial-cleaning"

# Fallback categories if automatic discovery fails
fallback_categories:
  "Floor Care": "https://agar.com.au/products?category=floor-care"
  "Kitchen Cleaning": "https://agar.com.au/products?category=kitchen"
  "Carpet Care": "https://agar.com.au/products?category=carpet"
  "Bathroom Cleaning": "https://agar.com.au/products?category=bathroom"
  "Glass & Surface": "https://agar.com.au/products?category=glass"
  "Sanitizers": "https://agar.com.au/products?category=sanitizer"

# URL Generation Settings
batch_size: 50
max_products_per_category: 1000
max_pages_per_category: 20
delay: 1.0

# Output Settings
verbose: false
```

### Configuration Priority

1. **CLI arguments** (highest priority)
2. **Configuration file** values
3. **Default values** (lowest priority)

## Output Structure

The tool now creates organized run-specific directories for better pipeline management. Each extraction run generates a unique folder structure:

```
output_dir/
└── run_YYYYMMDD_HHMMSS/
    ├── categories.json              # Discovered categories
    ├── product_urls.json           # Generated product URLs  
    ├── extraction_results.json     # Complete extraction summary
    ├── logs/
    │   └── url_extraction.log      # Detailed processing logs
    └── metadata/
        ├── run_config.json         # Run configuration and setup
        └── run_completion.json     # Completion metrics and file outputs
```

## Output Files

The URL extractor generates several organized files in run-specific directories:

### Main Data Files

#### 1. `categories.json` (in run directory)

Contains discovered product categories with metadata:

```json
{
  "discovery_metadata": {
    "discovered_at": "2025-10-26T15:30:00.000Z",
    "base_url": "https://agar.com.au",
    "total_categories": 12,
    "discovery_method": "navigation_analysis",
    "tool_version": "Agar URL Extractor v1.0"
  },
  "categories": {
    "Floor Care": {
      "url": "https://agar.com.au/products/floor-care",
      "discovered_at": "2025-10-26T15:30:05.000Z",
      "source": "main_navigation"
    },
    "Kitchen Cleaning": {
      "url": "https://agar.com.au/products/kitchen",
      "discovered_at": "2025-10-26T15:30:08.000Z",
      "source": "common_paths"
    }
  }
}
```

#### 2. `product_urls.json` (in run directory)

Contains comprehensive product URL data:

```json
{
  "generation_metadata": {
    "generated_at": "2025-10-26T15:45:00.000Z",
    "total_categories": 12,
    "total_unique_products": 245,
    "total_products_with_duplicates": 267,
    "generation_method": "category_crawling_with_pagination",
    "tool_version": "Agar URL Extractor v1.0"
  },
  "category_results": {
    "Floor Care": {
      "total_products": 45,
      "pages_processed": 3,
      "category_url": "https://agar.com.au/products/floor-care"
    }
  },
  "product_urls_by_category": {
    "Floor Care": [
      {
        "url": "https://agar.com.au/product/floor-cleaner-concentrate",
        "category": "Floor Care",
        "discovered_at": "2025-10-26T15:45:12.000Z"
      }
    ]
  },
  "all_unique_product_urls": [
    "https://agar.com.au/product/floor-cleaner-concentrate",
    "https://agar.com.au/product/kitchen-degreaser"
  ],
  "product_category_mapping": {
    "https://agar.com.au/product/floor-cleaner-concentrate": ["Floor Care"],
    "https://agar.com.au/product/kitchen-degreaser": ["Kitchen Cleaning", "Commercial"]
  }
}
```

#### 3. `extraction_results.json` (in run directory)

Contains complete extraction run summary with run-specific metadata:

```json
{
  "extraction_metadata": {
    "tool_version": "Agar URL Extractor v1.1",
    "run_id": "run_20251026_160013",
    "start_time": "2025-10-26T15:30:00.000Z",
    "end_time": "2025-10-26T15:45:30.000Z",
    "total_duration_seconds": 930,
    "base_output_directory": "clients/agar/agar_url_data",
    "run_directory": "clients/agar/agar_url_data/run_20251026_160013",
    "extraction_successful": true
  },
  "summary": {
    "categories_discovered": 12,
    "total_unique_products": 245,
    "total_products_with_duplicates": 267,
    "categories_processed": 12,
    "product_urls_file": "clients/agar/agar_url_data/run_20251026_160013/product_urls.json",
    "categories_file": "clients/agar/agar_url_data/run_20251026_160013/categories.json"
  }
}
```

### Organized Support Files

#### 4. `logs/url_extraction.log`

Detailed processing log with timestamps and progress tracking, organized in dedicated logs directory.

#### 5. `metadata/run_config.json`

Run configuration and setup information:

```json
{
  "run_info": {
    "run_id": "run_20251026_160013",
    "run_timestamp": "20251026_160013",
    "start_time": "2025-10-26T16:00:13.139Z",
    "tool_version": "Agar URL Extractor v1.1",
    "run_directory": "test_organized_structure/run_20251026_160013",
    "base_output_directory": "test_organized_structure"
  },
  "configuration": { "..." },
  "directory_structure": { "..." }
}
```

#### 6. `metadata/run_completion.json`

Completion metrics and performance data:

```json
{
  "completion_info": {
    "completed_at": "2025-10-26T16:00:32.733Z",
    "extraction_successful": true,
    "run_id": "run_20251026_160013",
    "summary": { "..." }
  },
  "file_outputs": { "..." },
  "performance_metrics": { "..." }
}
```

### Benefits of Organized Structure

- **Run Isolation**: Each extraction run is contained in its own directory
- **Easy Management**: Clear separation between data files, logs, and metadata
- **Historical Tracking**: Multiple runs can coexist without conflicts
- **Pipeline Integration**: Organized structure supports better automation
- **Debugging**: Logs and metadata are easily accessible per run

## Process Flow

### Phase 1: Category Discovery

1. **Main Navigation Analysis**: Crawls the Agar homepage to extract navigation links
2. **CSS Selector Extraction**: Uses specific selectors to find category links:
   - `nav a, .navigation a, .main-nav a, .menu a`
   - `.categories a, .category-link, .product-categories a`
   - `a[href*='category'], a[href*='products'], a[href*='cleaning']`
3. **URL Validation**: Filters valid category URLs and converts relative to absolute
4. **Common Path Checking**: Tests predefined category paths as fallback
5. **Manual Fallback**: Uses configured fallback categories if automatic discovery fails

### Phase 2: URL Generation

1. **Category Processing**: Iterates through each discovered category
2. **Page Analysis**: Crawls category pages with CSS selectors:
   - `a[href*='product'], .product-link, .product a` (product links)
   - `.pagination a, .pager a, .next, .more` (pagination links)
3. **Pagination Handling**: Automatically follows pagination links
4. **URL Filtering**: Validates product URLs and removes invalid/duplicate links
5. **Data Aggregation**: Combines results and creates unified URL structure

## Technical Implementation

### Core Components

#### `AgarCategoryDiscovery`
- Discovers product categories from website navigation
- Uses AsyncWebCrawler with JsonCssExtractionStrategy
- Handles fallback mechanisms for category discovery
- Generates `categories.json` output file

#### `AgarURLGeneration`
- Processes category pages to find product URLs
- Implements pagination handling with visited page tracking
- Filters and validates product vs non-product URLs
- Creates comprehensive URL mappings with category associations

#### `AgarURLExtractor`
- Main orchestrator class
- Manages logging configuration and output directory
- Coordinates category discovery and URL generation phases
- Produces final results and summary files

### URL Validation Logic

#### Product URL Indicators
- `product`, `item`, `/p/`, `/products/`
- `sku=`, `id=`, `pid=`

#### Invalid URL Indicators  
- `contact`, `about`, `privacy`, `terms`, `login`
- `register`, `account`, `cart`, `checkout`, `search`
- `mailto:`, `tel:`, `#`, `javascript:`
- `category`, `page=`, `sort=`, `filter=`

#### Pagination URL Indicators
- `page=`, `p=`, `next`, `more`, `continue`

## Error Handling

### Prerequisite Checking
- Validates categories file exists before URL generation
- Provides clear error messages for missing dependencies

### Graceful Failure Handling
- Individual category failures don't stop entire process
- Network errors logged with retry-friendly structure
- JSON parsing errors handled with meaningful warnings

### Rate Limiting
- Configurable delays between requests
- Respectful crawling with built-in pauses
- Page limits prevent infinite pagination loops

## Integration with Other Tools

### Using URLs with Universal Scraper

```bash
# Extract URLs first
python clients/agar/scripts/agar_url_extractor.py --config url_extraction_config.yaml

# Use URLs with universal scraper
python src/pipeline/universal_scraper.py \
  --urls-file clients/agar/agar_url_data/product_urls.json \
  --mode enhanced \
  --batch-size 10
```

### Using URLs with Processing Pipeline

```bash
# Skip URL extraction steps in main pipeline
python clients/agar/scripts/processing_pipeline.py \
  --step scraping validation \
  --config pipeline_config.yaml
```

## Performance Considerations

### Optimization Settings

| Setting | Conservative | Balanced | Aggressive |
|---------|-------------|----------|------------|
| `batch_size` | 25 | 50 | 100 |
| `delay` | 2.0s | 1.0s | 0.5s |
| `max_pages_per_category` | 10 | 20 | 50 |
| `max_products_per_category` | 500 | 1000 | 2000 |

### Expected Performance

- **Categories Discovery**: 30-60 seconds
- **URL Generation**: 5-15 minutes (depends on catalog size)
- **Total Runtime**: 10-20 minutes for full Agar catalog
- **Output Size**: 200-500 unique product URLs (estimated)

## Troubleshooting

### Common Issues

#### No Categories Discovered
- **Cause**: Website structure changes or network issues
- **Solution**: Check fallback_categories in config, verify base_url accessibility

#### Low Product Count
- **Cause**: CSS selectors not matching current site structure
- **Solution**: Enable verbose logging to inspect extraction results

#### Timeouts or Failures
- **Cause**: Network issues or rate limiting
- **Solution**: Increase delay, reduce batch_size, check network connectivity

### Debug Steps

1. **Enable verbose logging**: `--verbose`
2. **Check log file**: Review detailed processing logs
3. **Test with limits**: Use `--max-categories 5 --max-products 50`
4. **Verify output**: Inspect generated JSON files
5. **Manual verification**: Test category URLs in browser

## Best Practices

### Configuration Management
- Use configuration files for consistent settings
- Version control your config files
- Document custom configurations

### Output File Management
- Regular backup of URL extraction results
- Archive timestamped extraction files
- Monitor output file sizes for anomalies

### Integration Workflow
- Run URL extraction separately from scraping
- Validate URL files before feeding to scrapers
- Use extraction results as input for batch processing

## Changelog

### v1.0 - Initial Release
- Extracted from processing pipeline v1.0
- Focused URL extraction functionality
- Comprehensive CLI interface
- YAML configuration support
- Robust error handling and logging
