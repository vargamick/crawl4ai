# Client Setup Guide

This guide walks you through setting up a new client scraping configuration using the standardized template.

## Initial Setup

### 1. Copy Template Structure
```bash
# Copy the template directory
cp -r clients/template clients/your_client_name
cd clients/your_client_name
```

### 2. Update Client Configuration
Edit `config/client_config.yaml`:
```yaml
client:
  name: "Your Client Name"
  domain: "yourclient.com"
  contact: "contact@yourclient.com"
  created_date: "2025-10-26"
```

### 3. Configure Scraping Rules
Update `config/scraping_rules.yaml` with client-specific selectors:
```yaml
selectors:
  product_name: ".product-title h1"
  product_price: ".price-current"
  # ... add client-specific selectors
```

## Directory Structure Overview

```
your_client_name/
├── config/                    # Configuration files
│   ├── client_config.yaml     # Client-specific settings
│   ├── scraping_rules.yaml    # Extraction rules
│   └── output_formats.yaml    # Output specifications
├── scripts/                   # Execution scripts
│   ├── run_tests.py           # Main test runner
│   ├── custom_extractors.py   # Client-specific logic
│   └── comparison_tools.py    # Run comparison utilities
├── runs/                      # Timestamped outputs
│   ├── 20251026_143000_test/  # Example run directory
│   └── latest -> most_recent/ # Symlink to latest
├── templates/                 # Reusable patterns
└── docs/                      # Documentation
```

## Running Your First Test

```bash
# From the client directory
python scripts/run_tests.py --client your_client_name --run-name initial_test
```

This will create a timestamped run directory with all outputs organized properly.

## Customization Points

### Custom Extractors
Create client-specific extraction logic in `scripts/custom_extractors.py`:
```python
def extract_custom_field(page_content):
    # Your custom extraction logic
    pass
```

### Validation Rules
Update validation criteria in `config/client_config.yaml`:
```yaml
validation:
  min_products: 50
  required_fields: ["name", "price", "category"]
```

### Output Formats
Customize output in `config/output_formats.yaml` (if created).

## Best Practices

1. **Always test changes**: Run tests after any configuration updates
2. **Document customizations**: Update this setup.md with client-specific notes
3. **Version configurations**: Keep track of working configurations
4. **Monitor runs**: Regular comparison between runs to track improvements

## Troubleshooting

### Common Issues
- **No products found**: Check URL patterns and selectors
- **Missing fields**: Verify selector accuracy with browser dev tools
- **Rate limiting**: Increase delays in client_config.yaml

### Debug Steps
1. Check logs in `runs/latest/logs/`
2. Examine raw output in `runs/latest/raw_output/`
3. Compare with previous working runs using comparison tools

## Support

For issues or questions, refer to the main project documentation at `../../docs/client_setup_rules.md`.
