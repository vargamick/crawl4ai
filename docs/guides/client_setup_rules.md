# Client Scraping Setup Rules & Standards

**MANDATORY COMPLIANCE REQUIRED FOR ALL CLIENT IMPLEMENTATIONS**

This document defines the strict rules and standards that **MUST** be followed every time new client scraping setups are created or existing ones are modified.

## 1. FOLDER STRUCTURE RULES

### 1.1 Mandatory Directory Structure
```
clients/{client_name}/
├── config/                    # REQUIRED - Configuration files
│   ├── client_config.yaml     # REQUIRED - Client-specific overrides
│   ├── scraping_rules.yaml    # REQUIRED - Extraction patterns
│   ├── url_patterns.yaml      # OPTIONAL - URL discovery rules
│   └── output_formats.yaml    # OPTIONAL - Output specifications
├── scripts/                   # REQUIRED - Execution scripts
│   ├── run_tests.py           # REQUIRED - Main test runner
│   ├── custom_extractors.py   # OPTIONAL - Client-specific logic
│   ├── data_validators.py     # OPTIONAL - Validation scripts
│   └── comparison_tools.py    # REQUIRED - Run comparison utilities
├── runs/                      # REQUIRED - Timestamped outputs
│   ├── {YYYYMMDD_HHMMSS}_{run_name}/  # Auto-created run directories
│   └── latest -> {recent}/    # REQUIRED - Symlink to latest run
├── templates/                 # OPTIONAL - Reusable patterns
│   ├── extraction_templates/  # Templates for extraction patterns
│   ├── validation_schemas/    # Data validation schemas
│   └── report_templates/      # Output report formats
└── docs/                      # REQUIRED - Client documentation
    ├── setup.md               # REQUIRED - Setup instructions
    ├── testing_guide.md       # OPTIONAL - Testing procedures
    ├── data_dictionary.md     # OPTIONAL - Field definitions
    └── troubleshooting.md     # OPTIONAL - Common issues
```

### 1.2 Run Directory Structure (Auto-Created)
```
runs/{YYYYMMDD_HHMMSS}_{run_name}/
├── config/                    # REQUIRED - Config snapshot
│   └── run_config.yaml        # Merged configuration used
├── raw_output/               # REQUIRED - Raw scraping results
├── processed/                # REQUIRED - Cleaned/processed data
├── logs/                     # REQUIRED - Run-specific logs
│   └── test_run.log          # Main log file
├── metrics/                  # REQUIRED - Performance metrics
└── run_metadata.json         # REQUIRED - Run parameters/stats
```

## 2. NAMING CONVENTIONS

### 2.1 Client Directory Names
- **Format**: `{client_name}` (lowercase, underscores for spaces)
- **Examples**: `agar_cleaning`, `automotive_parts`, `electronics_retailer`
- **FORBIDDEN**: Spaces, special characters, uppercase

### 2.2 Run Directory Names
- **Format**: `{YYYYMMDD}_{HHMMSS}_{run_name}`
- **Examples**: `20251026_143000_initial_test`, `20251026_150000_production_run`
- **REQUIRED**: Timestamp must be first, run_name must be descriptive

### 2.3 File Naming Standards
- Configuration files: `snake_case.yaml`
- Script files: `snake_case.py`
- Output files: Include timestamp when generated
- Log files: `descriptive_name.log`

## 3. CONFIGURATION MANAGEMENT RULES

### 3.1 Configuration Hierarchy (MANDATORY)
1. **Base Configuration**: `config/base_config.yaml` (project-wide defaults)
2. **Client Configuration**: `clients/{client}/config/client_config.yaml` (client overrides)
3. **Run Configuration**: Snapshot saved to each run's config/ directory

### 3.2 Required Configuration Fields
Every `client_config.yaml` MUST contain:
```yaml
client:
  name: "Client Name"           # REQUIRED
  domain: "domain.com"          # REQUIRED
  contact: "email@domain.com"   # REQUIRED
  created_date: "YYYY-MM-DD"    # REQUIRED

# Override sections (inherit from base if not specified)
browser: {}                     # Browser-specific settings
crawling: {}                    # Crawling parameters
rate_limit: {}                  # Rate limiting rules
extraction: {}                  # Extraction settings
output: {}                      # Output preferences
validation: {}                  # Validation rules
```

### 3.3 Configuration Validation Rules
- **NEVER** hardcode URLs, credentials, or sensitive data in config files
- **ALWAYS** use environment variables for secrets
- **ALWAYS** provide defaults for optional fields
- **VALIDATE** all configuration on startup

## 4. OUTPUT FILE ORGANIZATION RULES

### 4.1 Prohibited Practices
- **NEVER** create output files at project root
- **NEVER** create output directories outside the client structure
- **NEVER** overwrite existing run directories
- **NEVER** create files without timestamps in production runs

### 4.2 Mandatory Practices
- **ALWAYS** use timestamped run directories
- **ALWAYS** snapshot configuration for each run
- **ALWAYS** create symlink to latest run
- **ALWAYS** separate raw and processed outputs
- **ALWAYS** include run metadata

### 4.3 File Organization Standards
```
runs/{timestamp}_{run_name}/
├── raw_output/
│   ├── raw_scraping_results.json      # Direct scraper output
│   └── {product_name}_raw.json        # Individual raw files
├── processed/
│   ├── extracted_products_{timestamp}.json  # Clean product data
│   ├── {product_name}_processed.json   # Individual processed files
│   └── final_results.json             # Final aggregated results
├── metrics/
│   ├── performance_metrics.json       # Timing and performance data
│   ├── data_quality_report.json       # Quality analysis
│   └── error_summary.json             # Error tracking
└── logs/
    ├── test_run.log                   # Main execution log
    ├── crawler.log                    # Crawler-specific logs
    └── errors.log                     # Error-specific logs
```

## 5. SCRIPT IMPLEMENTATION RULES

### 5.1 Required Script Structure
Every `run_tests.py` MUST implement:
```python
class TestRunner:
    def __init__(self, client_name, run_name=None)  # REQUIRED
    def setup_logging(self)                         # REQUIRED
    def load_config(self)                          # REQUIRED
    def create_run_structure(self)                 # REQUIRED
    def save_run_metadata(self, config, results)  # REQUIRED
    def run_scraping_test(self, config)           # REQUIRED - Override this
    def update_latest_symlink(self)               # REQUIRED
    def run(self)                                 # REQUIRED - Main method
```

### 5.2 Error Handling Requirements
- **ALWAYS** implement try-catch around main execution
- **ALWAYS** log errors with full stack traces
- **ALWAYS** save partial results even on failure
- **NEVER** silently fail or ignore exceptions
- **ALWAYS** provide meaningful error messages

### 5.3 Logging Standards
- **ALWAYS** log to both file and console
- **ALWAYS** use structured logging format
- **ALWAYS** include timestamps and log levels
- **SEPARATE** different types of logs (main, crawler, errors)

## 6. DATA VALIDATION RULES

### 6.1 Mandatory Validations
- **Minimum product count**: Define in client config
- **Required fields presence**: Check all mandatory fields
- **Data format validation**: Ensure proper data types
- **Quality thresholds**: Define acceptable quality levels

### 6.2 Validation Implementation
```python
# REQUIRED in every run
def validate_results(self, results, config):
    validation_rules = config.get('validation', {})
    
    # Check minimum products
    min_products = validation_rules.get('min_products', 1)
    if len(results) < min_products:
        raise ValidationError(f"Only {len(results)} products found, minimum {min_products} required")
    
    # Check required fields
    required_fields = validation_rules.get('required_fields', [])
    # ... implement field validation
    
    return validation_report
```

## 7. MIGRATION RULES FOR EXISTING SETUPS

### 7.1 Migrating Scattered Output Files
When encountering existing scattered output files:
1. **NEVER** delete existing files immediately
2. **CREATE** new client structure following standards
3. **MIGRATE** files to appropriate run directories with timestamps
4. **DOCUMENT** the migration in client docs
5. **VERIFY** all data transferred correctly before cleanup

### 7.2 Migration Process
```bash
# Example migration process
mkdir -p clients/existing_client/runs/20251026_000000_migrated_data/processed/
mv old_output_files/* clients/existing_client/runs/20251026_000000_migrated_data/processed/
# Update symlink
cd clients/existing_client/runs/
ln -sf 20251026_000000_migrated_data latest
```

## 8. CODE QUALITY ENFORCEMENT

### 8.1 Required Code Standards
- **ALWAYS** use type hints in Python functions
- **ALWAYS** include docstrings for classes and methods
- **ALWAYS** follow PEP 8 styling guidelines
- **ALWAYS** implement proper exception handling
- **NEVER** use hardcoded paths or values

### 8.2 Documentation Requirements
- **README.md**: Required in every client directory
- **setup.md**: Required setup instructions
- **Inline comments**: For complex logic
- **Configuration comments**: Explain all config options

## 9. TESTING AND VALIDATION

### 9.1 Required Tests Before Deployment
- **Configuration loading**: Verify all configs load correctly
- **Directory creation**: Test run directory structure creation
- **Error scenarios**: Test handling of various failure modes
- **Data validation**: Verify validation rules work correctly

### 9.2 Acceptance Criteria
Before any client setup is considered complete:
- [ ] All directory structures created correctly
- [ ] Configuration files properly configured
- [ ] At least one successful test run completed
- [ ] Latest symlink working correctly
- [ ] Documentation updated and accurate
- [ ] Migration completed if applicable

## 10. ENFORCEMENT AND COMPLIANCE

### 10.1 Mandatory Review Checklist
Every new client setup MUST pass this checklist:
- [ ] Follows exact directory structure
- [ ] Uses correct naming conventions
- [ ] Configuration properly implemented
- [ ] Scripts implement required methods
- [ ] Error handling implemented
- [ ] Logging properly configured
- [ ] Data validation implemented
- [ ] Documentation complete
- [ ] No hardcoded values
- [ ] No files at project root

### 10.2 Violation Consequences
- **Non-compliant setups MUST be refactored before use**
- **All scattered files MUST be organized into proper structure**
- **No exceptions allowed for convenience or speed**

---

**This document is MANDATORY and applies to ALL client scraping implementations.**

**Any deviation from these rules must be explicitly documented and justified.**

**Regular audits will be conducted to ensure compliance.**
