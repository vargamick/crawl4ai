# Script Organization Plan - Root Level Python Files

## Analysis of Current Test Scripts

After reviewing all test scripts in the project root, here's the classification and recommended organization:

## 📋 Script Classification

### Agar-Specific Scripts (Move to Agar Client)
- **`test_actual_scraper.py`** - Tests Universal Scraper with existing Agar data
- **`test_enhanced_universal_scraper.py`** - Tests enhanced mode with Agar URLs
- **`test_scraper_with_clean_data.py`** - Tests with clean Agar product data
- **`batch_crawl_products.py`** - Agar batch processing script

### Framework/General Testing Scripts (Keep as Examples/Tests)
- **`test_crawl4ai_local.py`** - Tests basic crawl4ai functionality
- **`test_individual_files.py`** - Tests individual file generation (framework feature)
- **`create_test_example.py`** - General test example creator

## 🎯 Recommended Organization

### 1. Create Agar Client Structure
```bash
# Create Agar client from template
cp -r clients/template clients/agar_cleaning

# Update configuration
# clients/agar_cleaning/config/client_config.yaml:
client:
  name: "Agar Cleaning Products"
  domain: "agar.com.au" 
  contact: "info@agar.com.au"
  created_date: "2025-10-26"
```

### 2. Move Agar-Specific Scripts
```bash
# Move to Agar client scripts directory
mv test_actual_scraper.py clients/agar_cleaning/scripts/
mv test_enhanced_universal_scraper.py clients/agar_cleaning/scripts/
mv test_scraper_with_clean_data.py clients/agar_cleaning/scripts/
mv batch_crawl_products.py clients/agar_cleaning/scripts/

# Rename to follow conventions
cd clients/agar_cleaning/scripts/
mv test_actual_scraper.py test_existing_data_validation.py
mv test_enhanced_universal_scraper.py test_enhanced_extraction.py  
mv test_scraper_with_clean_data.py test_clean_data_processing.py
mv batch_crawl_products.py batch_processing.py
```

### 3. Organize Framework Tests
```bash
# Move general framework tests to tests directory
mv test_crawl4ai_local.py tests/integration/
mv test_individual_files.py tests/unit/
mv create_test_example.py examples/utilities/
```

### 4. Update Script Headers
Each moved script needs header updates to reflect new location and purpose:

**Example for Agar client scripts**:
```python
#!/usr/bin/env python3
"""
Agar Client - Enhanced Extraction Test
Tests enhanced universal scraper with Agar product URLs
Located: clients/agar_cleaning/scripts/test_enhanced_extraction.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
```

## 📁 Final Directory Structure

### Agar Client Scripts
```
clients/agar_cleaning/scripts/
├── run_tests.py                    # Standard test runner (from template)
├── comparison_tools.py             # Standard comparison tools (from template)
├── test_existing_data_validation.py # Was: test_actual_scraper.py
├── test_enhanced_extraction.py     # Was: test_enhanced_universal_scraper.py
├── test_clean_data_processing.py   # Was: test_scraper_with_clean_data.py
└── batch_processing.py             # Was: batch_crawl_products.py
```

### Framework Tests
```
tests/
├── integration/
│   └── test_crawl4ai_local.py      # Framework integration test
├── unit/
│   └── test_individual_files.py   # Unit test for file generation
└── ...

examples/
├── utilities/
│   └── create_test_example.py      # Example utility script
└── ...
```

## 🔄 Script Modifications Needed

### 1. Update Import Paths
All moved scripts need path adjustments:
```python
# Old (at root):
sys.path.append('examples')
from universal_scraper import UniversalScraper

# New (in client structure):
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.append(str(project_root / 'examples'))
from universal_scraper import UniversalScraper
```

### 2. Update Output Directories
All scripts should use the new run structure:
```python
# Old:
output_dir = "test_enhanced_output"

# New:
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"runs/{timestamp}_enhanced_test/processed"
```

### 3. Update to Use Standard Test Runner Pattern
Convert scripts to inherit from the standardized TestRunner class:
```python
from scripts.run_tests import TestRunner

class AgarEnhancedTestRunner(TestRunner):
    def run_scraping_test(self, config):
        # Custom Agar enhanced scraping logic here
        return results
```

## 📋 Implementation Steps

### Phase 1: Create Agar Client (Immediate)
1. Copy template to create `clients/agar_cleaning/`
2. Update client configuration
3. Move Agar-specific scripts to client scripts directory
4. Rename scripts following conventions

### Phase 2: Update Script Paths (Week 1)
1. Fix import paths in all moved scripts
2. Update output directories to use run structure
3. Test all moved scripts in new locations

### Phase 3: Integrate with Standard Runner (Week 2)
1. Convert scripts to use TestRunner base class
2. Ensure proper logging and metadata generation
3. Update scripts to create proper run directories

### Phase 4: Clean Framework Tests (Week 2)
1. Move general tests to appropriate locations
2. Update test suite structure
3. Ensure CI/CD can find tests in new locations

## 🛠️ Script-Specific Notes

### test_actual_scraper.py → test_existing_data_validation.py
- Purpose: Validate scraper works with existing output files
- Location: `clients/agar_cleaning/scripts/`
- Updates needed: Fix paths to existing output directories

### test_enhanced_universal_scraper.py → test_enhanced_extraction.py  
- Purpose: Test enhanced mode with Agar URLs
- Location: `clients/agar_cleaning/scripts/`
- Updates needed: Use proper run directory structure

### test_scraper_with_clean_data.py → test_clean_data_processing.py
- Purpose: Test with clean Agar product data
- Location: `clients/agar_cleaning/scripts/`
- Updates needed: Integrate with standard runner pattern

### batch_crawl_products.py → batch_processing.py
- Purpose: Batch process Agar products
- Location: `clients/agar_cleaning/scripts/`
- Updates needed: Major refactor to use new structure

### test_crawl4ai_local.py (Framework Test)
- Purpose: Test basic crawl4ai functionality
- Location: `tests/integration/`
- Updates needed: Minimal, just path adjustments

### test_individual_files.py (Framework Test) 
- Purpose: Test individual file generation feature
- Location: `tests/unit/`
- Updates needed: Convert to proper unit test

### create_test_example.py (Utility)
- Purpose: Create test examples
- Location: `examples/utilities/`
- Updates needed: Update paths and make more generic

## ✅ Success Criteria

**Organization Complete When:**
- [ ] No test scripts remain at project root
- [ ] All Agar scripts moved to `clients/agar_cleaning/scripts/`
- [ ] All framework tests in appropriate test directories
- [ ] All scripts have correct import paths
- [ ] All scripts use proper run directory structure
- [ ] All scripts integrate with standardized patterns

**Testing Complete When:**
- [ ] All moved scripts execute successfully in new locations
- [ ] Scripts create proper run directories with timestamps
- [ ] Scripts follow logging and error handling standards
- [ ] No broken imports or path issues

This organization eliminates root-level script proliferation and ensures all client-specific code is properly contained within the client structure.
