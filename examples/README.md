# Universal Crawl4AI Scraper

A single, configurable Python script that consolidates all the various scraping examples into one unified tool with multiple modes and extensive configuration options.

## Overview

This universal scraper replaces multiple similar example scripts with a single parameterized approach, supporting:

- **Multiple extraction modes** (simple, enhanced, LLM, API)
- **Configurable batch processing**
- **Content exclusion capabilities**  
- **Multiple output formats** (JSON, Markdown, Documents)
- **Environment detection** (Docker/Local)
- **Comprehensive CLI and config file support**

## Quick Start

### Basic Usage

```bash
# Simple mode with content exclusion
python universal_scraper.py --mode simple --urls product_urls.json --content-exclusion --limit 10

# Enhanced mode (requires Enhanced Agar Scraper)
python universal_scraper.py --mode enhanced --urls urls.json --batch-size 5 --output results/

# LLM mode with document generation
python universal_scraper.py --mode llm --urls urls.json --format document --delay 3

# API mode for Docker environments
python universal_scraper.py --mode api --urls urls.json --docker --crawl4ai-url http://localhost:11235
```

### Configuration File

Create a configuration file for complex setups:

```bash
# Generate sample configuration
python universal_scraper.py --create-config

# Use configuration file
python universal_scraper.py --config scraper_config.yaml
```

## Extraction Modes

### 1. Simple Mode (`--mode simple`)
- Uses CSS selectors for extraction
- Fast and lightweight
- Good for structured websites
- **Replaces**: `docker_simple_batch.py`, `docker_simple_llm_test.py`

### 2. Enhanced Mode (`--mode enhanced`)  
- Uses Enhanced Agar Scraper (if available)
- Advanced product extraction
- Structured schema output
- **Replaces**: `docker_batch_scrape_agar.py`, `docker_batch_scrape_agar_fixed.py`

### 3. LLM Mode (`--mode llm`)
- Uses LLM for intelligent extraction
- Structured JSON schema output
- Best for complex content
- **Replaces**: Various LLM-based examples

### 4. API Mode (`--mode api`)
- Uses Crawl4AI server API
- Perfect for Docker environments
- HTTP-based communication
- **Replaces**: `multi_product_scraper.py` functionality

## Content Exclusion

Enable advanced content filtering to remove noise:

```bash
python universal_scraper.py --mode simple --urls urls.json --content-exclusion
```

**Content Exclusion Features:**
- Navigation and header removal
- Form and overlay elimination
- Social media widget filtering
- BM25 content filtering
- **Replaces**: `docker_enhanced_agar_scraper_with_content_exclusion.py`

## Configuration Options

### Command Line Arguments

```bash
# Basic Options
--mode {simple,enhanced,llm,api}    # Extraction mode
--urls URL_FILE                     # URL file (JSON, TXT, CSV)
--batch-size INT                    # Batch size (default: 10)
--output OUTPUT_DIR                 # Output directory
--delay FLOAT                       # Delay between requests (seconds)
--limit INT                         # Limit number of URLs

# Processing Options  
--content-exclusion                 # Enable content exclusion
--format {json,markdown,document}   # Output format

# Environment Options
--docker                           # Force Docker mode
--crawl4ai-url URL                 # Crawl4AI server URL
--verbose / --quiet                # Verbosity control

# Configuration
--config CONFIG_FILE               # Use config file (YAML/JSON)
--create-config                    # Generate sample config
```

### Configuration File Format

```yaml
# Sample configuration (scraper_config.yaml)
mode: "simple"                     # enhanced, simple, llm, api
urls_file: "product_urls.json"     
batch_size: 10
output_dir: "scraping_results"
delay: 2.0
limit: null                        # No limit
content_exclusion: false
format: "json"                     # json, markdown, document
verbose: true
docker: false
crawl4ai_url: "http://localhost:11235"

# LLM Configuration
llm_provider: "openai/gpt-4o-mini"
extraction_instruction: "Extract product information focusing on name, description, benefits, and specifications."

# Content Exclusion Configuration
bm25_filter: true
bm25_threshold: 1.0
filter_query: "product information specifications features benefits"
```

## Input File Formats

### JSON Format
```json
{
  "all_product_urls": [
    "https://example.com/product1",
    "https://example.com/product2"
  ]
}
```

Or simple array:
```json
[
  "https://example.com/product1", 
  "https://example.com/product2"
]
```

### TXT/CSV Format
```
https://example.com/product1
https://example.com/product2
https://example.com/product3
```

## Output Formats

### JSON Output (Default)
- Structured product data
- Batch processing metadata
- Extraction statistics
- Individual product files

### Markdown Output (`--format markdown`)
- Human-readable documents
- Product information formatted
- Metadata included
- One file per product

### Document Output (`--format document`) 
- Complete product documents
- Structured sections
- Extraction metadata
- Professional formatting

## Output Structure

```
scraping_results/
├── universal_scraping_results_YYYYMMDD_HHMMSS.json  # Master results
├── extracted_products_YYYYMMDD_HHMMSS.json          # Products only
├── batch_001_results.json                           # Individual batches
├── batch_002_results.json
└── documents_YYYYMMDD_HHMMSS/                       # Generated docs (if requested)
    ├── product_1.md
    └── product_2.md
```

## Environment Support

### Local Environment
```bash
python universal_scraper.py --mode simple --urls urls.json
```

### Docker Environment  
```bash
# Auto-detects Docker environment
python universal_scraper.py --mode api --urls /app/urls.json --docker

# Or force Docker mode
python universal_scraper.py --docker --crawl4ai-url http://crawl4ai:11235
```

## Advanced Examples

### Batch Processing with Content Exclusion
```bash
python universal_scraper.py \
  --mode simple \
  --urls large_product_list.json \
  --batch-size 20 \
  --content-exclusion \
  --delay 1.5 \
  --output batch_results/ \
  --verbose
```

### LLM Extraction with Custom Configuration
```bash
python universal_scraper.py \
  --mode llm \
  --urls products.json \
  --format document \
  --limit 50 \
  --config custom_llm_config.yaml
```

### Production Docker Setup
```yaml
# docker_config.yaml
mode: "api"
urls_file: "/app/product_urls.json"
batch_size: 15
output_dir: "/app/results"
delay: 3.0
content_exclusion: true
format: "json"
docker: true
crawl4ai_url: "http://crawl4ai-server:11235"
bm25_threshold: 1.2
```

```bash
python universal_scraper.py --config docker_config.yaml
```

## Error Handling

The universal scraper includes comprehensive error handling:

- **Network errors**: Automatic retry logic
- **Parsing errors**: Graceful degradation  
- **Rate limiting**: Configurable delays
- **Batch failures**: Continue processing
- **Invalid URLs**: Skip and log

## Performance Considerations

- **Batch size**: Adjust based on target site capacity
- **Delay**: Respect robots.txt and rate limits
- **Content exclusion**: Reduces processing time
- **Mode selection**: Choose based on requirements
  - `simple`: Fastest
  - `enhanced`: Most accurate  
  - `llm`: Most intelligent
  - `api`: Most scalable

## Migration from Old Examples

### From `docker_batch_scrape_agar.py`
```bash
# Old
python docker_batch_scrape_agar.py

# New  
python universal_scraper.py --mode enhanced --urls /app/complete_agar_product_urls_20251008_122301.json
```

### From `docker_simple_batch.py`
```bash
# Old
python docker_simple_batch.py

# New
python universal_scraper.py --mode simple --urls /app/urls.json --batch-size 8
```

### From `docker_enhanced_agar_scraper_with_content_exclusion.py`
```bash
# Old  
python docker_enhanced_agar_scraper_with_content_exclusion.py

# New
python universal_scraper.py --mode enhanced --content-exclusion --limit 10 --urls /app/urls.json
```

### From `multi_product_scraper.py`
```bash
# Old
# (API-based scraper)

# New
python universal_scraper.py --mode api --urls product_urls.json --crawl4ai-url http://localhost:11235
```

## Dependencies

Required packages (automatically imported):
- `crawl4ai` - Core scraping functionality
- `pyyaml` - Configuration file support
- `requests` - API mode support

Optional packages:
- `crawl4ai.agar` - Enhanced Agar Scraper (for enhanced mode)

## Troubleshooting

### Common Issues

1. **"Enhanced Agar Scraper not available"**
   - Use `--mode simple` or `--mode llm` instead
   - Install Enhanced Agar Scraper if needed

2. **"URLs file not found"**  
   - Check file path with `--urls`
   - Ensure file format is supported (JSON/TXT/CSV)

3. **Docker connection failed**
   - Verify Crawl4AI server is running
   - Check `--crawl4ai-url` parameter
   - Use `--docker` flag in Docker environments

4. **LLM extraction failed**
   - Set `OPENAI_API_KEY` environment variable
   - Configure `llm_provider` in config file
   - Check API quotas and permissions

### Debug Mode
```bash
python universal_scraper.py --verbose --limit 1 --urls test_urls.json
```

## Contributing

This universal scraper consolidates multiple example files. When adding new functionality:

1. Add new modes or options rather than separate scripts
2. Maintain backward compatibility with configuration
3. Update this README with new features
4. Include error handling and logging

## Replaced Example Files

This universal scraper replaces the following files:

- ✅ `docker_batch_scrape_agar.py` → `--mode enhanced`
- ✅ `docker_batch_scrape_agar_fixed.py` → `--mode enhanced`  
- ✅ `docker_simple_batch.py` → `--mode simple`
- ✅ `docker_enhanced_agar_scraper_with_content_exclusion.py` → `--mode enhanced --content-exclusion`
- ✅ `multi_product_scraper.py` → `--mode api`
- ✅ `docker_production_scraper_fixed.py` → `--mode enhanced`
- ✅ `docker_simple_llm_test.py` → `--mode llm`
- ✅ `robust_content_exclusion_demo.py` → `--mode simple --content-exclusion`
- ✅ `standalone_content_exclusion_demo.py` → `--mode simple --content-exclusion`

The universal scraper provides all functionality from these scripts through configuration options, eliminating code duplication and maintenance overhead.
