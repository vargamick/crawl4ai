# Client Scraping Template

This is the standardized template structure for all client scraping setups. Each new client should follow this exact structure to ensure consistency, maintainability, and proper organization.

## Directory Structure

```
clients/{client_name}/
├── config/                    # Client-specific configuration
├── scripts/                   # Test and processing scripts
├── runs/                      # Timestamped run outputs
├── templates/                 # Reusable patterns and schemas
└── docs/                      # Client documentation
```

## Quick Start

1. Copy this template directory and rename it to your client name
2. Update `config/client_config.yaml` with client-specific settings
3. Customize scripts in `scripts/` directory as needed
4. Run tests using `scripts/run_tests.py`
5. Review outputs in the timestamped `runs/` directories

## Important Rules

- **NEVER** create output files at the project root
- **ALWAYS** use timestamped run directories
- **ALWAYS** snapshot configuration for each run
- **FOLLOW** the naming conventions specified in docs/

For detailed implementation guidelines, see `../../docs/client_setup_rules.md`
