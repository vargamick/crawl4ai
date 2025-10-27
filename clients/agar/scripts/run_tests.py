#!/usr/bin/env python3
"""
Client Scraping Test Runner Template
Standardized script for running scraping tests with proper organization
"""

import os
import sys
import yaml
import json
from datetime import datetime
from pathlib import Path
import shutil
import argparse
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    def __init__(self, client_name, run_name=None):
        self.client_name = client_name
        self.client_dir = Path(__file__).parent.parent
        self.run_name = run_name or "standard_test"
        
        # Create timestamped run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.client_dir / "runs" / f"{timestamp}_{self.run_name}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for this test run"""
        log_dir = self.run_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "test_run.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"client_{self.client_name}")
        
    def load_config(self):
        """Load and merge configurations"""
        # Load base config
        base_config_path = self.client_dir.parent.parent / "config" / "base_config.yaml"
        with open(base_config_path, 'r') as f:
            base_config = yaml.safe_load(f)
            
        # Load client config
        client_config_path = self.client_dir / "config" / "client_config.yaml"
        if client_config_path.exists():
            with open(client_config_path, 'r') as f:
                client_config = yaml.safe_load(f)
        else:
            client_config = {}
            
        # Merge configs (client overrides base)
        merged_config = {**base_config, **client_config}
        
        # Save config snapshot
        config_dir = self.run_dir / "config"
        config_dir.mkdir(exist_ok=True)
        with open(config_dir / "run_config.yaml", 'w') as f:
            yaml.dump(merged_config, f, default_flow_style=False)
            
        return merged_config
        
    def create_run_structure(self):
        """Create standardized run directory structure"""
        subdirs = [
            "config",
            "raw_output", 
            "processed",
            "logs",
            "metrics"
        ]
        
        for subdir in subdirs:
            (self.run_dir / subdir).mkdir(exist_ok=True)
            
    def save_run_metadata(self, config, results=None):
        """Save metadata about this run"""
        metadata = {
            "client_name": self.client_name,
            "run_name": self.run_name,
            "timestamp": datetime.now().isoformat(),
            "run_directory": str(self.run_dir),
            "config_used": config,
            "results_summary": results or {}
        }
        
        with open(self.run_dir / "run_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
            
    def run_scraping_test(self, config):
        """Execute the scraping test - override in client-specific version"""
        self.logger.info("Running scraping test...")
        
        # TODO: Implement actual scraping logic here
        # This is a template - each client should customize this method
        
        # Example structure:
        # 1. Initialize crawler with config
        # 2. Run scraping process
        # 3. Save raw results to raw_output/
        # 4. Process results and save to processed/
        # 5. Generate metrics and save to metrics/
        
        results = {
            "status": "completed",
            "pages_scraped": 0,
            "products_found": 0,
            "errors": 0
        }
        
        return results
        
    def update_latest_symlink(self):
        """Update the 'latest' symlink to point to this run"""
        latest_path = self.client_dir / "runs" / "latest"
        
        # Remove existing symlink if it exists
        if latest_path.is_symlink():
            latest_path.unlink()
        elif latest_path.exists():
            shutil.rmtree(latest_path)
            
        # Create new symlink
        latest_path.symlink_to(self.run_dir.name)
        
    def run(self):
        """Main execution method"""
        try:
            self.logger.info(f"Starting test run for client: {self.client_name}")
            self.logger.info(f"Run directory: {self.run_dir}")
            
            # Setup
            self.create_run_structure()
            config = self.load_config()
            
            # Execute test
            results = self.run_scraping_test(config)
            
            # Finalize
            self.save_run_metadata(config, results)
            self.update_latest_symlink()
            
            self.logger.info("Test run completed successfully")
            self.logger.info(f"Results saved to: {self.run_dir}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Test run failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Run client scraping tests")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--run-name", help="Custom run name")
    parser.add_argument("--config", help="Additional config file to merge")
    
    args = parser.parse_args()
    
    runner = TestRunner(args.client, args.run_name)
    results = runner.run()
    
    print(f"Test completed with results: {results}")

if __name__ == "__main__":
    main()
