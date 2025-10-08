# 🧪 Agar Website Product Scraping - API Call Documentation

This document provides complete API call configurations for scraping the Agar product catalog using the Crawl4AI Docker deployment endpoints. Updated to reflect **actual data usage patterns** from the Enhanced Agar Scraper implementation with 189 discovered product URLs.

## 🎯 Target Information

**Agar Website**: https://agar.com.au  
**Products Base URL**: https://agar.com.au/products/  
**Total Discovered Products**: 189 verified URLs  
**Sample Product**: https://agar.com.au/product/first-base/  
**API Endpoint**: http://localhost:8000/api/scraper/trigger  
**Enhanced Scraper**: Technical Brief v1.0 compliant with modal handling & tab navigation

## 📋 Basic Agar Product Scraping

### 1. Discovery Phase - Main Product Listing

**Purpose**: Discover all product URLs from the main catalog page

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://agar.com.au/products/"],
    "max_items": 1,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": true,
    "chunking_strategy": "regex"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "job_id": "job_agar_discovery_001",
  "message": "Scraping job queued successfully"
}
```

### 2. Sample Product Testing - Single Product

**Purpose**: Test extraction on a known product (First Base floor cleaner)

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://agar.com.au/product/first-base/"],
    "max_items": 1,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": true,
    "include_documents": true
  }'
```

## 🏭 Industrial Product Categories

### 3. Floor Care Products (Real Discovered URLs)

**Purpose**: Target actual floor cleaning and maintenance products from discovered data

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/first-base/",
      "https://agar.com.au/product/autoscrub/",
      "https://agar.com.au/product/fresh-mop/",
      "https://agar.com.au/product/florprep/",
      "https://agar.com.au/product/ultrastrip/"
    ],
    "max_items": 5,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": true,
    "include_documents": true,
    "chunking_strategy": "regex"
  }'
```

### 4. Kitchen & Food Service Products (Real Discovered URLs)

**Purpose**: Extract actual kitchen cleaning products from discovered categories

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/oven-clean/",
      "https://agar.com.au/product/grill-clean/",
      "https://agar.com.au/product/dish-power/",
      "https://agar.com.au/product/autodish/",
      "https://agar.com.au/product/potwash/"
    ],
    "max_items": 5,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": true,
    "include_documents": true
  }'
```

### 5. Bathroom & Washroom Products (Real Discovered URLs)

**Purpose**: Target actual bathroom cleaning products from toilet-bathroom-cleaners category

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/bowl-clean/",
      "https://agar.com.au/product/shower-star/",
      "https://agar.com.au/product/all-fresh/",
      "https://agar.com.au/product/fresco/",
      "https://agar.com.au/product/sequal/"
    ],
    "max_items": 5,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": true,
    "include_documents": true
  }'
```

## 🔬 Advanced Content Extraction

### 6. Technical Data Extraction with AI

**Purpose**: Extract technical specifications using cosine similarity for better content filtering

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/first-base/",
      "https://agar.com.au/product/bio-lab/",
      "https://agar.com.au/product/enzyme-wizard/"
    ],
    "max_items": 3,
    "extraction_strategy": "cosine",
    "include_metadata": true,
    "include_media": true,
    "include_documents": true,
    "chunking_strategy": "regex"
  }'
```

### 7. Media-Heavy Product Pages

**Purpose**: Focus on products with extensive image galleries and technical videos

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/pressure-clean/",
      "https://agar.com.au/product/carpet-fresh/",
      "https://agar.com.au/product/window-clean/"
    ],
    "max_items": 3,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": true,
    "include_documents": false
  }'
```

## 📋 Product Documentation Focus

### 8. Product Data Sheets (PDS) Extraction

**Purpose**: Target products with extensive documentation (safety sheets, technical specs)

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/industrial-degreaser/",
      "https://agar.com.au/product/heavy-duty-cleaner/",
      "https://agar.com.au/product/chemical-stripper/"
    ],
    "max_items": 3,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": false,
    "include_documents": true,
    "chunking_strategy": "regex"
  }'
```

### 9. Safety Data Sheets (SDS) Focus

**Purpose**: Extract safety and regulatory information

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/caustic-cleaner/",
      "https://agar.com.au/product/acid-cleaner/",
      "https://agar.com.au/product/solvent-based/"
    ],
    "max_items": 3,
    "extraction_strategy": "cosine",
    "include_metadata": true,
    "include_media": false,
    "include_documents": true
  }'
```

## 🎯 Comprehensive Product Catalog Scraping

### 10. Full Catalog Discovery (Batch 1 - Testing with Real URLs)

**Purpose**: Limited batch for testing full catalog scraping with actual discovered product URLs

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/first-base/",
      "https://agar.com.au/product/bowl-clean/", 
      "https://agar.com.au/product/breeze/",
      "https://agar.com.au/product/chloradet/",
      "https://agar.com.au/product/exit/",
      "https://agar.com.au/product/flash-dry/",
      "https://agar.com.au/product/handpass/",
      "https://agar.com.au/product/mould-x/",
      "https://agar.com.au/product/ready-2-go/",
      "https://agar.com.au/product/ultrastrip/"
    ],
    "max_items": 10,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": true,
    "include_documents": true,
    "chunking_strategy": "regex"
  }'
```

**Expected Results**: 10 products extracted from diverse categories including floor care, bathroom cleaners, air fresheners, and strippers - representing the actual variety in the discovered 189 URL dataset.

### 11. Production Scale Catalog Scraping

**Purpose**: Full-scale production scraping with rate limiting

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/products/",
      "https://agar.com.au/product-category/floor-care/",
      "https://agar.com.au/product-category/kitchen/",
      "https://agar.com.au/product-category/bathroom/",
      "https://agar.com.au/product-category/laundry/",
      "https://agar.com.au/product-category/industrial/",
      "https://agar.com.au/product-category/automotive/",
      "https://agar.com.au/product-category/hospitality/"
    ],
    "max_items": 100,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": true,
    "include_documents": true,
    "chunking_strategy": "regex"
  }'
```

## 📊 Monitoring and Management Calls

### 12. Check Scraping Progress

**Purpose**: Monitor job status and progress for long-running agar scraping jobs

```bash
# Check current job status
curl "http://localhost:8000/api/scraper/status"

# Get specific job details (replace with actual job_id)
curl "http://localhost:8000/api/scraper/jobs/job_agar_discovery_001"

# Get all recent jobs
curl "http://localhost:8000/api/scraper/jobs?limit=10"
```

### 13. Retrieve Agar Product Results

**Purpose**: Access scraped agar product data with search and filtering

```bash
# Get all results (paginated)
curl "http://localhost:8000/api/scraper/results?page=1&limit=20"

# Search for specific products
curl "http://localhost:8000/api/scraper/search?q=first%20base&limit=5"

# Search by product category
curl "http://localhost:8000/api/scraper/search?q=floor%20cleaner&limit=10"

# Search for industrial products
curl "http://localhost:8000/api/scraper/search?q=industrial&limit=15"
```

### 14. Get Scraping Statistics

**Purpose**: Monitor overall scraping performance and results

```bash
# Get overall scraping stats
curl "http://localhost:8000/api/scraper/stats"

# Get available categories discovered
curl "http://localhost:8000/api/scraper/categories"
```

## 🔧 Specialized Configuration Examples

### 15. High-Quality Image Extraction

**Purpose**: Focus on extracting high-quality product images and media

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/first-base/",
      "https://agar.com.au/product/bio-lab/"
    ],
    "max_items": 2,
    "extraction_strategy": "basic",
    "include_metadata": false,
    "include_media": true,
    "include_documents": false,
    "chunking_strategy": null
  }'
```

### 16. Document-Only Extraction

**Purpose**: Extract only PDFs, safety sheets, and technical documentation

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/caustic-cleaner/",
      "https://agar.com.au/product/acid-cleaner/"
    ],
    "max_items": 2,
    "extraction_strategy": "basic",
    "include_metadata": true,
    "include_media": false,
    "include_documents": true,
    "chunking_strategy": "regex"
  }'
```

### 17. Minimal Content Extraction

**Purpose**: Fast extraction with minimal resource usage

```bash
curl -X POST "http://localhost:8000/api/scraper/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://agar.com.au/product/window-clean/",
      "https://agar.com.au/product/carpet-fresh/"
    ],
    "max_items": 2,
    "extraction_strategy": "basic",
    "include_metadata": false,
    "include_media": false,
    "include_documents": false,
    "chunking_strategy": null
  }'
```

## 🧪 Python Integration Examples

### 18. Python Script for Agar Scraping

**Purpose**: Complete Python integration for programmatic agar product extraction

```python
import requests
import json
import time

class AgarProductScraper:
    def __init__(self, api_base_url="http://localhost:8000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
    
    def trigger_agar_scraping(self, product_urls, config=None):
        """Trigger scraping for agar products"""
        default_config = {
            "urls": product_urls,
            "max_items": len(product_urls),
            "extraction_strategy": "basic",
            "include_metadata": True,
            "include_media": True,
            "include_documents": True,
            "chunking_strategy": "regex"
        }
        
        if config:
            default_config.update(config)
        
        response = self.session.post(
            f"{self.api_base_url}/api/scraper/trigger",
            json=default_config
        )
        
        return response.json()
    
    def wait_for_completion(self, job_id, timeout=300):
        """Wait for scraping job to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_response = self.session.get(
                f"{self.api_base_url}/api/scraper/jobs/{job_id}"
            )
            
            if status_response.status_code == 200:
                job_data = status_response.json()
                status = job_data.get("status")
                
                if status == "completed":
                    return job_data
                elif status == "failed":
                    raise Exception(f"Job failed: {job_data.get('error')}")
            
            time.sleep(5)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
    
    def get_results(self, search_term=None, limit=20):
        """Get scraping results"""
        params = {"limit": limit}
        if search_term:
            params["search"] = search_term
        
        response = self.session.get(
            f"{self.api_base_url}/api/scraper/results",
            params=params
        )
        
        return response.json()

# Usage Example
def scrape_agar_floor_care_products():
    scraper = AgarProductScraper()
    
    # Floor care products
    floor_care_urls = [
        "https://agar.com.au/product/first-base/",
        "https://agar.com.au/product/clean-slate/",
        "https://agar.com.au/product/vinyl-fresh/",
        "https://agar.com.au/product/concrete-clean/",
        "https://agar.com.au/product/strip-ease/"
    ]
    
    # Trigger scraping
    job = scraper.trigger_agar_scraping(floor_care_urls)
    print(f"Started job: {job['job_id']}")
    
    # Wait for completion
    completed_job = scraper.wait_for_completion(job['job_id'])
    print(f"Job completed with {completed_job['results_count']} results")
    
    # Get results
    results = scraper.get_results(search_term="floor")
    return results

# Run the scraping
if __name__ == "__main__":
    results = scrape_agar_floor_care_products()
    print(f"Extracted {len(results['results'])} floor care products")
    
    for product in results['results']:
        print(f"- {product['title']}: {product['url']}")
```

## 🎯 Expected Data Structure (Enhanced Scraper Output)

### Sample Product Result Structure - Technical Brief v1.0 Compliant

```json
{
  "product_id": "first-base-agar-prod-fb001",
  "product_name": "First Base",
  "product_url": "https://agar.com.au/product/first-base/",
  "description": "Industrial strength floor cleaner and degreaser suitable for all hard floor surfaces...",
  "metadata": {
    "raw_extracted_data": { "...": "complete extraction data" },
    "extraction_timestamp": "2025-01-08T15:30:00Z",
    "codes": ["FB", "FB5", "FB20"],
    "skus": ["FB5", "FB20"],
    "categories": ["Floor Care", "Base Sealers"],
    "tags": ["Industrial", "Commercial"],
    "sizes": ["5L", "20L"],
    "specifications": {
      "ph_level": "12.5 +/- 0.5",
      "perfume": "None"
    },
    "key_benefits": [
      "Powerful alkaline cleaner",
      "Suitable for all hard floors",
      "Removes stubborn dirt and grime"
    ],
    "documents": [
      {
        "type": "SDS",
        "name": "Safety Data Sheet",
        "url": "https://agar.com.au/wp-content/uploads/first-base-sds.pdf"
      },
      {
        "type": "PDS", 
        "name": "Product Data Sheet",
        "url": "https://agar.com.au/wp-content/uploads/first-base-pds.pdf"
      }
    ],
    "reviews": {
      "rating": 4.8,
      "count": 12
    },
    "brief_compliance": "v1.0"
  }
}
```

### Enhanced Scraper Statistics Response

```json
{
  "success": true,
  "scraping_metadata": {
    "total_products_extracted": 15,
    "total_products_attempted": 17,
    "success_rate": "88.2%",
    "extraction_time": "00:04:23",
    "errors_encountered": 2,
    "categories_discovered": [
      "Floor Care",
      "Kitchen Care", 
      "Bathroom Cleaners",
      "Carpet Cleaners",
      "Personal Care"
    ],
    "modal_closures_handled": 8,
    "tab_navigations_performed": 45,
    "documents_extracted": 28,
    "images_processed": 67
  }
}
```

### Real Category Distribution (from 189 discovered URLs)

```json
{
  "categories_summary": {
    "hot-products": 22,
    "green-cleaning-products": 20,
    "heavy-duty-detergents": 13,
    "kitchen-care/ware-washing": 13,
    "kitchen-care/cleaning-and-sanitising": 12,
    "disinfectant-antibacterial-detergent": 9,
    "carpet-cleaners/carpet-spotters-and-stain-removers": 9,
    "all-purpose-floor-cleaners": 9,
    "cleansave-concentrated-chemicals": 8,
    "air-fresheners/detergent-deodorisers": 8,
    "specialty-cleaning/special-purpose-heavy-duty-detergents": 8,
    "specialty-cleaning/vehicle-cleaning": 7,
    "personal-care/liquid-soap": 6,
    "carpet-cleaners": 6,
    "toilet-bathroom-cleaners": 6,
    "kitchen-care/oven-and-grill-cleaners": 5,
    "chlorinated-cleaners-sanitisers": 5
  },
  "total_categories": 57,
  "total_products": 189,
  "success_rate": "87.5%"
}
```

## 📝 Implementation Workflow

### Recommended Scraping Sequence

1. **Start with Discovery** (#1) - Map main product pages
2. **Test Single Product** (#2) - Validate extraction on known product  
3. **Test Category Batches** (#3-5) - Test different product categories
4. **Advanced Extraction** (#6-7) - Test AI-powered extraction strategies
5. **Documentation Focus** (#8-9) - Extract technical documentation
6. **Scale Up** (#10-11) - Implement full catalog scraping
7. **Monitor & Retrieve** (#12-14) - Ongoing monitoring and data retrieval

### Best Practices for Agar Scraping

1. **Rate Limiting**: Include delays between requests to respect the website
2. **Error Handling**: Monitor job status and handle failures gracefully
3. **Data Validation**: Verify extracted product information for accuracy
4. **Resource Management**: Use appropriate limits for large-scale scraping
5. **Documentation**: Keep track of successful URL patterns and configurations

## 🚨 Important Considerations

- **Website Policies**: Ensure compliance with Agar's robots.txt and terms of service
- **Rate Limiting**: Implement appropriate delays to avoid overwhelming the server
- **Data Accuracy**: Validate extracted product information against known data
- **Legal Compliance**: Ensure scraping activities comply with relevant laws and regulations
- **Resource Usage**: Monitor Docker container resources during large-scale scraping

---

**Note**: These API calls are designed for the Docker-deployed Crawl4AI system. Ensure both frontend and API containers are running before executing these commands.

**API Base URL**: http://localhost:8000  
**Frontend Interface**: http://localhost:3001  
**Health Check**: http://localhost:8000/health
