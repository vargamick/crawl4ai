# Client Structure Standardization - Rollout Plan

## Overview

This plan details the phased approach to implement the new standardized client scraping structure across all existing and future client setups.

## Phase 1: Foundation Setup (Week 1)

### ✅ Completed Items
- [x] Created template structure at `clients/template/`
- [x] Established configuration hierarchy with base and client configs
- [x] Documented comprehensive rules in `docs/client_setup_rules.md`
- [x] Created reusable script templates
- [x] Established naming conventions and standards

### 📋 Immediate Actions Required
1. **Test Template Structure**
   ```bash
   # Create a test client to validate template
   cp -r clients/template clients/test_client
   cd clients/test_client
   # Update config with test data
   python scripts/run_tests.py --client test_client --run-name validation_test
   ```

2. **Update .gitignore**
   ```
   # Add patterns to prevent scattered outputs
   /*_output/
   /*_test_output/
   test_*_output/
   *_results.json
   extracted_*.json
   universal_*.json
   ```

## Phase 2: Existing Data Migration (Week 2)

### Current Scattered Outputs Inventory
- `agar_test_output/` - 18 files
- `test_enhanced_output/` - 7 files  
- `test_fixed_output/` - 7 files
- `test_output/` - 3 files
- `scraper_test_output/` - 1 file

### Migration Strategy

#### Step 1: Create Agar Client Structure
```bash
# Create agar client from template
cp -r clients/template clients/agar_cleaning

# Update configuration
# Edit clients/agar_cleaning/config/client_config.yaml:
client:
  name: "Agar Cleaning Products"
  domain: "agar.com.au"
  contact: "info@agar.com.au"
  created_date: "2025-10-26"
```

#### Step 2: Migrate Scattered Files
```bash
# Create migration run directory
mkdir -p clients/agar_cleaning/runs/20251024_000000_migrated_legacy_data/{processed,raw_output,config,logs,metrics}

# Migrate agar_test_output
mv agar_test_output/* clients/agar_cleaning/runs/20251024_000000_migrated_legacy_data/processed/

# Migrate other test outputs (group by apparent run dates)
# test_enhanced_output -> 20251024_140640_enhanced_run
# test_fixed_output -> 20251024_144608_fixed_run
# test_output -> 20251023_000000_early_tests

# Create appropriate run directories and move files
```

#### Step 3: Document Migration
Create migration log in `clients/agar_cleaning/docs/migration_log.md`:
```markdown
# Migration Log - Agar Cleaning Client

## Source Data Locations
- agar_test_output/ -> 20251024_000000_migrated_legacy_data/processed/
- test_enhanced_output/ -> 20251024_140640_enhanced_run/processed/
- test_fixed_output/ -> 20251024_144608_fixed_run/processed/

## File Mappings
[Document specific file movements]

## Data Validation
[Record validation of migrated data]
```

## Phase 3: Script Updates (Week 2-3)

### Required Script Modifications

#### Update Existing Test Scripts
1. **batch_crawl_products.py** - Modify to use new structure
2. **test_*.py files** - Update all test scripts to output to proper client runs
3. **create_test_example.py** - Update to follow new patterns

#### Implementation Steps
```python
# Example modification pattern for existing scripts
import sys
from pathlib import Path
from datetime import datetime

# Add to existing scripts
def get_output_directory(client_name, run_name="automated_run"):
    """Get proper output directory following new standards"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(f"clients/{client_name}/runs/{timestamp}_{run_name}")
    
    # Create structure
    for subdir in ["raw_output", "processed", "logs", "metrics", "config"]:
        (run_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    return run_dir
```

## Phase 4: New Client Creation Process (Week 3)

### Standardized Client Creation Workflow

#### Automated Client Setup Script
```bash
# Create script: scripts/create_new_client.py
#!/usr/bin/env python3
"""
Automated client setup script
Usage: python scripts/create_new_client.py --name "Client Name" --domain "domain.com"
"""

import argparse
import shutil
from pathlib import Path
from datetime import datetime

def create_client(name, domain, contact):
    # Normalize name for directory
    client_dir = name.lower().replace(" ", "_").replace("-", "_")
    
    # Copy template
    source = Path("clients/template")
    destination = Path(f"clients/{client_dir}")
    shutil.copytree(source, destination)
    
    # Update configuration
    config_file = destination / "config" / "client_config.yaml"
    # ... update with actual client data
    
    print(f"Client '{name}' created at clients/{client_dir}/")
    print(f"Next steps:")
    print(f"1. cd clients/{client_dir}")
    print(f"2. Edit config/scraping_rules.yaml with client-specific selectors")
    print(f"3. python scripts/run_tests.py --client {client_dir} --run-name initial_test")

if __name__ == "__main__":
    # ... argument parsing and execution
```

## Phase 5: Documentation & Training (Week 3-4)

### Documentation Updates Required

1. **Main Project README.md**
   - Add section about client structure
   - Link to setup rules and templates

2. **Individual Script Documentation**
   - Update all existing script comments
   - Add usage examples following new structure

3. **Create Quick Start Guide**
   ```markdown
   # Quick Start - Adding New Client

   1. Run setup script:
      `python scripts/create_new_client.py --name "New Client" --domain "newclient.com"`

   2. Configure extraction rules:
      `edit clients/new_client/config/scraping_rules.yaml`

   3. Run initial test:
      `python clients/new_client/scripts/run_tests.py --client new_client`

   4. Review results:
      `ls clients/new_client/runs/latest/processed/`
   ```

## Phase 6: Enforcement & Monitoring (Ongoing)

### Compliance Monitoring

#### Automated Checks
Create `scripts/validate_client_structure.py`:
```python
def audit_client_compliance():
    """Audit all client directories for compliance"""
    violations = []
    
    for client_dir in Path("clients").glob("*/"):
        if client_dir.name == "template":
            continue
            
        # Check required directories
        required_dirs = ["config", "scripts", "runs", "docs"]
        for req_dir in required_dirs:
            if not (client_dir / req_dir).exists():
                violations.append(f"{client_dir}: Missing {req_dir} directory")
        
        # Check required files
        required_files = [
            "config/client_config.yaml",
            "scripts/run_tests.py", 
            "docs/setup.md"
        ]
        # ... continue checks
    
    return violations
```

#### Regular Audit Schedule
- **Weekly**: Automated compliance check
- **Monthly**: Manual review of new clients
- **Quarterly**: Full structure audit and cleanup

### Legacy Cleanup Schedule

#### Week 4: Root-Level Cleanup
Once migration is verified complete:
```bash
# Archive old directories (don't delete immediately)
mkdir archive_legacy_$(date +%Y%m%d)
mv agar_test_output archive_legacy_*/
mv test_enhanced_output archive_legacy_*/
mv test_fixed_output archive_legacy_*/
mv test_output archive_legacy_*/
mv scraper_test_output archive_legacy_*/

# Archive old scripts that don't follow new patterns
mv test_*.py archive_legacy_*/scripts/
```

## Success Metrics

### Phase Completion Criteria

**Phase 1 Complete When:**
- [ ] Template structure validated with test run
- [ ] All documentation complete and reviewed
- [ ] Rules document approved and finalized

**Phase 2 Complete When:**
- [ ] All scattered files migrated to proper structure
- [ ] Legacy data validated in new locations
- [ ] Migration documentation complete

**Phase 3 Complete When:**
- [ ] All existing scripts updated to use new structure
- [ ] No more files created at project root
- [ ] Script modification guide documented

**Phase 4 Complete When:**
- [ ] Automated client creation script working
- [ ] New client workflow documented and tested
- [ ] Training materials created

**Phase 5 Complete When:**
- [ ] All documentation updated
- [ ] Team trained on new processes
- [ ] Quick start guide validated

**Phase 6 Complete When:**
- [ ] Automated compliance checking in place
- [ ] Regular audit process established
- [ ] Legacy files safely archived

## Risk Mitigation

### Potential Issues & Solutions

1. **Data Loss During Migration**
   - **Mitigation**: Always copy, never move initially
   - **Backup**: Create full archive before any changes
   - **Validation**: Verify all files transferred correctly

2. **Script Breakage**
   - **Mitigation**: Update scripts incrementally
   - **Testing**: Test each script update thoroughly
   - **Rollback**: Keep original scripts until new ones validated

3. **Resistance to New Structure**
   - **Mitigation**: Clear documentation and training
   - **Support**: Provide examples and templates
   - **Enforcement**: Automated compliance checking

## Timeline Summary

- **Week 1**: Foundation & Testing
- **Week 2**: Migration & Script Updates  
- **Week 3**: New Workflows & Documentation
- **Week 4**: Enforcement & Cleanup
- **Ongoing**: Monitoring & Compliance

## Next Immediate Steps

1. **Validate template** with test client creation
2. **Begin Agar client migration** following documented process
3. **Update .gitignore** to prevent future scattered files
4. **Create client creation automation script**
5. **Schedule migration work** for existing scattered outputs

This rollout plan ensures systematic, safe implementation of the new structure while maintaining data integrity and minimizing disruption to existing workflows.
