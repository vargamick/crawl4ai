# Agar Processing Pipeline Guide

## Overview

The Agar Processing Pipeline is a comprehensive, parameterized system built upon the universal_scraper.py foundation to provide end-to-end automated scraping of the Agar Cleaning Systems website. It implements all the requirements specified in your request for a pipeline that is "parameterized but common across various client projects" with "multiple independent steps."

## Architecture

### Foundation
- **Built upon**: `src/pipeline/universal_scraper.py` as the core scraping foundation
- **Integrates with**: Existing validation system (`validation_system.py`)
- **Extends**: Client-based configuration system with YAML files

### Key Features
✅ **Category Discovery**: Automatically navigates Agar website to discover product categories  
✅ **URL Generation**: Creates comprehensive lists of product URLs for each category  
✅ **Independent Step Processing**: Each step can run independently with graceful failure handling  
✅ **Batch Processing**: Configurable batch sizes for optimal performance  
✅ **Category-Based Organization**: Outputs organized by category folders with one file per product  
✅ **Validation Integration**: Real-time validation using existing validation system  
✅ **Comprehensive Logging**: Detailed logging and monitoring throughout the process  

## Pipeline Steps

### 1. Category Discovery (`category-discovery`)
**Purpose**: Generate a list of category pages from the Agar website by navigating through the categories section

**What it does**:
- Analyzes main Agar website navigation
- Extracts category links and names using CSS selectors
- Tries common category paths as fallback
- Provides manual fallback categories if none discovered
- Stores category list in JSON document for use by scraping tool

**Output**: `pipeline_data/categories.json`

**Prerequisites**: None

**Example**:
```json
{
  "discovery_metadata": {
    "discovered_at": "2024-10-26T15:30:00",
    "base_url": "https://agar.com.au",
    "total_categories": 8,
    "discovery_method": "navigation_analysis"
  },
  "categories": {
    "Floor Care": {
      "url": "https://agar.com.au/products/floor-care",
      "discovered_at": "2024-10-26T15:30:00",
      "source": "main_navigation"
    }
  }
}
```

### 2. URL Generation (`url-generation`)
**Purpose**: Create a file containing one URL for every product page to be scraped

**What it does**:
- Processes each category page to find product links
- Handles pagination to find all products in each category
- Creates comprehensive URL lists with category mappings
- Removes duplicates while preserving category associations
- Includes all products in categories regardless of duplication across categories

**Output**: `pipeline_data/product_urls.json`

**Prerequisites**: `categories.json` must exist (run `category-discovery` first)

**Example**:
```json
{
  "generation_metadata": {
    "total_unique_products": 245,
    "total_categories": 8
  },
  "product_urls_by_category": {
    "Floor Care": [
      {
        "url": "https://agar.com.au/product/presto",
        "category": "Floor Care",
        "discovered_at": "2024-10-26T15:35:00"
      }
    ]
  },
  "all_unique_product_urls": ["https://agar.com.au/product/presto", ...],
  "product_category_mapping": {
    "https://agar.com.au/product/presto": ["Floor Care", "Kitchen Cleaning"]
  }
}
```

### 3. Scraping (`scraping`)
**Purpose**: Process one category at a time using universal_scraper.py as the foundation

**What it does**:
- Uses universal_scraper.py for actual scraping operations
- Processes one category at a time with individual file outputs
- Creates category-specific output directories
- Stores individual file outputs as one file per product within specific category folders
- Includes every product within the category regardless of duplication
- Enables parameters to drive batch sizes and other configuration

**Output**: `pipeline_data/scraped_products/{category_name}/` with individual product JSON files

**Prerequisites**: `product_urls.json` must exist (run `url-generation` first)

**Configuration Options**:
```yaml
scraping:
  scraping_mode: "enhanced"  # enhanced, simple, llm, api
  batch_size: 10             # configurable batch size
  delay: 2.0                 # delay between requests
  limit: null                # overall limit across categories
  content_exclusion: true    # enable content filtering
  selected_categories: []    # specific categories to process
```

### 4. Validation (`validation`)
**Purpose**: Validate scraped products using the existing validation system

**What it does**:
- Integrates with existing `validation_system.py`
- Validates each scraped product file
- Generates quality scores and validation reports
- Identifies missing required fields
- Provides category-level and overall statistics

**Output**: `pipeline_data/validation_reports/validation_report_{timestamp}.json`

**Prerequisites**: Scraped products must exist (run `scraping` first)

## Usage Examples

### Run Complete Pipeline
```bash
cd clients/agar/scripts
python processing_pipeline.py --config ../config/pipeline_config.yaml
```

### Run Individual Steps
```bash
# Discover categories only
python processing_pipeline.py --step category-discovery

# Generate URLs only (requires categories)
python processing_pipeline.py --step url-generation --batch-size 50

# Scrape specific categories only
python processing_pipeline.py --step scraping --categories "Floor Care,Kitchen Cleaning" --batch-size 10

# Validate scraped products only
python processing_pipeline.py --step validation
```

### Run Multiple Steps
```bash
# Run discovery and URL generation only
python processing_pipeline.py --step category-discovery url-generation --output-dir my_pipeline_data
```

### Generate Sample Configuration
```bash
python processing_pipeline.py --create-config
```

## Configuration

### Main Configuration File: `pipeline_config.yaml`

```yaml
# Base configuration
base_url: "https://agar.com.au"
output_dir: "clients/agar/pipeline_data"
steps: ["all"]

# Category Discovery Settings
category_discovery:
  max_categories: 50

# URL Generation Settings  
url_generation:
  batch_size: 50
  max_products_per_category: 1000
  max_pages_per_category: 20

# Scraping Settings (builds upon universal_scraper.py)
scraping:
  scraping_mode: "enhanced"
  batch_size: 10
  delay: 2.0
  limit: null
  content_exclusion: true
  selected_categories: []

# Validation Settings
validation:
  enabled: true
  generate_reports: true
  quality_thresholds:
    excellent: 90
    good: 75
    acceptable: 60
    poor: 40
```

### Command Line Options

```bash
python processing_pipeline.py [options]

Pipeline Options:
  --config CONFIG           Configuration file (YAML or JSON)
  --create-config          Create sample configuration file
  --step STEPS             Pipeline steps to run: all, category-discovery, 
                          url-generation, scraping, validation
  --output-dir DIR         Output directory for pipeline data

Step-specific Options:
  --base-url URL          Base URL for Agar website
  --batch-size SIZE       Batch size for processing
  --categories CATS       Comma-separated list of categories to process
  --scraping-mode MODE    Scraping mode: simple, enhanced, llm, api
  --delay SECONDS         Delay between requests
  --limit NUMBER          Overall limit of products to process
```

## Independent Step Processing

### Graceful Failure Handling
Each step implements sophisticated prerequisite checking:

```python
def check_prerequisites(self) -> tuple[bool, str]:
    """Check if prerequisites for this step are met."""
    if not os.path.exists(self.required_file):
        return False, f"Required file not found: {self.required_file}. Run {self.prerequisite_step} step first."
    return True, ""
```

**Step Dependencies**:
- `category-discovery` → No prerequisites
- `url-generation` → Requires `categories.json`
- `scraping` → Requires `product_urls.json`
- `validation` → Requires scraped products directory

**Failure Behavior**:
- If a step's prerequisites are not met, it fails gracefully with a clear message
- Pipeline stops at failed step unless `continue_on_failure` is enabled
- Each step can be re-run independently after fixing issues
- Comprehensive error logging helps identify and resolve problems

### Step Status Tracking
```json
{
  "pipeline_metadata": {
    "steps_executed": ["category-discovery", "url-generation"],
    "all_steps_successful": false
  },
  "step_results": {
    "category-discovery": {
      "success": true,
      "duration_seconds": 45.2
    },
    "url-generation": {
      "success": false,
      "error": "Prerequisites not met: categories.json not found"
    }
  }
}
```

## Output Structure

```
clients/agar/pipeline_data/
├── categories.json                    # Category discovery output
├── product_urls.json                 # URL generation output
├── pipeline_log_{timestamp}.log      # Comprehensive pipeline logs
├── pipeline_results_{timestamp}.json # Overall pipeline results
├── scraped_products/                 # Scraping outputs organized by category
│   ├── Floor_Care/
│   │   ├── Presto.json               # Individual product files
│   │   ├── Active_Break.json
│   │   └── universal_scraping_results_{timestamp}.json
│   ├── Kitchen_Cleaning/
│   │   ├── Hook_Clean.json
│   │   └── Speed_Detergent.json
│   └── Carpet_Care/
│       └── React_Detergent.json
└── validation_reports/               # Validation outputs
    └── validation_report_{timestamp}.json
```

## Integration with Existing Systems

### Universal Scraper Integration
The scraping step creates a temporary configuration for universal_scraper.py:

```python
scraper_config = {
    'mode': self.scraping_mode,
    'urls_file': temp_urls_file,
    'batch_size': self.batch_size,
    'output_dir': category_output_dir,
    'delay': self.delay,
    'content_exclusion': True,
    'format': 'json'
}

scraper = UniversalScraper(scraper_config)
results = await scraper.run_scraping()
```

### Validation System Integration
The validation step uses the existing validation system:

```python
validator = AgarValidationSystem(
    output_dir=self.validation_output_dir,
    verbose=True
)

validation_result = validator.validate_product(product_data)
```

### Client Configuration Integration
The pipeline respects the existing client configuration structure:
- Uses existing validation rules from `scraping_rules.yaml`
- Applies validation criteria from `client_config.yaml`
- Maintains compatibility with extraction templates

## Performance and Scalability

### Batch Processing
- Configurable batch sizes for all steps
- Memory-efficient processing of large category lists
- Pagination handling for unlimited product discovery

### Respect for Website Resources
- Configurable delays between requests (default: 2 seconds)
- Sequential category processing to avoid overwhelming the server
- Comprehensive rate limiting and respectful crawling practices

### Error Recovery
- Automatic retry mechanisms for transient failures
- Graceful handling of individual product failures
- Continue processing even if some products fail

## Monitoring and Logging

### Comprehensive Logging
```
2024-10-26 15:30:15 - INFO - 🚀 AGAR PROCESSING PIPELINE STARTED
2024-10-26 15:30:15 - INFO - 📁 Output directory: clients/agar/pipeline_data
2024-10-26 15:30:15 - INFO - 🎯 Steps to run: all
2024-10-26 15:30:15 - INFO - 📋 Executing steps: category-discovery, url-generation, scraping, validation
2024-10-26 15:30:15 - INFO - ==================== STEP: CATEGORY-DISCOVERY ====================
2024-10-26 15:30:16 - INFO - 🚀 Starting step: category-discovery
```

### Progress Tracking
- Real-time progress updates for each step
- Category-by-category progress in URL generation and scraping
- Success/failure rates for validation
- Processing time tracking for performance monitoring

### Results Reporting
Each pipeline run generates comprehensive results:
- Step-by-step execution summary
- Processing times and success rates
- Error details and troubleshooting information
- Output file locations and statistics

## Best Practices

### Configuration Management
1. Use configuration files for repeated runs
2. Store configurations in version control
3. Use environment-specific configurations for different deployment scenarios

### Step Execution
1. Run discovery step first to understand category structure
2. Use URL generation with appropriate limits for testing
3. Test scraping on small category subsets before full runs
4. Always run validation to ensure quality

### Error Handling
1. Check logs for detailed error information
2. Re-run individual failed steps after fixing issues
3. Use smaller batch sizes if encountering timeout issues
4. Monitor website changes that might affect category/product structure

### Performance Optimization
1. Adjust batch sizes based on system capabilities
2. Use appropriate delays to balance speed with respectfulness
3. Consider running during off-peak hours for large scraping operations
4. Monitor and adjust limits based on actual website structure

## Troubleshooting

### Common Issues

**Categories not discovered**:
- Check base_url configuration
- Verify website accessibility
- Review category discovery logs for parsing errors
- Consider manual fallback categories

**URLs not generated**:
- Ensure categories.json exists and is valid
- Check product URL patterns in logs
- Adjust max_pages_per_category if needed
- Verify pagination selectors are working

**Scraping failures**:
- Check universal_scraper.py compatibility
- Verify batch sizes aren't too large
- Review delay settings for rate limiting
- Check for website structure changes

**Validation issues**:
- Ensure validation_system.py is available
- Check scraped product file format
- Review validation criteria configuration
- Verify required fields are being extracted

### Recovery Strategies

**Partial Pipeline Failures**:
1. Identify failed step from logs
2. Fix configuration or prerequisite issues
3. Re-run from failed step: `--step failed-step-name`
4. Continue with remaining steps

**Data Quality Issues**:
1. Run validation step to identify problems
2. Adjust scraping configuration based on validation results
3. Re-run scraping with improved settings
4. Use validation reports to monitor quality improvements

## Integration Examples

### Workflow Integration
```bash
#!/bin/bash
# Complete Agar scraping workflow

echo "Starting Agar product scraping pipeline..."

# Run complete pipeline
cd clients/agar/scripts
python processing_pipeline.py --config ../config/pipeline_config.yaml

# Check results
if [ $? -eq 0 ]; then
    echo "Pipeline completed successfully"
    echo "Results available in clients/agar/pipeline_data/"
else
    echo "Pipeline failed - check logs for details"
    exit 1
fi
```

### Configuration for Different Scenarios
```yaml
# Development configuration - limited scope
scraping:
  limit: 50
  selected_categories: ["Floor Care"]
  batch_size: 5

# Production configuration - full scope
scraping:
  limit: null
  selected_categories: []
  batch_size: 10
```

## Future Enhancements

The pipeline architecture is designed for extensibility:

### Additional Steps
- **Content Analysis Step**: Analyze scraped content for insights
- **Image Processing Step**: Download and process product images
- **Data Export Step**: Export to different formats (CSV, Excel, Database)

### Enhanced Category Discovery
- Machine learning-based category classification
- Dynamic category pattern recognition
- Multi-language category support

### Advanced Validation
- Content quality scoring beyond field validation
- Duplicate detection across categories
- Historical data comparison

### Performance Improvements
- Parallel category processing
- Distributed scraping across multiple instances
- Intelligent caching and incremental updates

## Conclusion

The Agar Processing Pipeline provides a comprehensive, parameterized solution that addresses all your specified requirements:

✅ **Parameterized but common across client projects**: Highly configurable with YAML files  
✅ **Built upon universal_scraper.py**: Uses it as the foundation for all scraping operations  
✅ **Multiple independent steps**: 4 distinct steps that can run independently  
✅ **Category discovery**: Automatically navigates and discovers categories  
✅ **URL generation**: Creates comprehensive product URL lists  
✅ **Batch processing**: Configurable batch sizes throughout  
✅ **Individual file outputs**: One file per product in category-specific folders  
✅ **Graceful failure handling**: Sophisticated error handling and recovery  
✅ **Integration ready**: Works with existing validation and configuration systems  

The pipeline is production-ready and provides a solid foundation for automated Agar website scraping with comprehensive monitoring, validation, and error handling capabilities.
