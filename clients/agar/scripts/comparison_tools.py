#!/usr/bin/env python3
"""
Run Comparison Tools Template
Compare results between different runs to track improvements/changes
"""

import json
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse
import logging

class RunComparator:
    def __init__(self, client_dir):
        self.client_dir = Path(client_dir)
        self.runs_dir = self.client_dir / "runs"
        
    def list_runs(self):
        """List all available runs"""
        if not self.runs_dir.exists():
            return []
            
        runs = []
        for run_dir in self.runs_dir.iterdir():
            if run_dir.is_dir() and run_dir.name != "latest":
                metadata_file = run_dir / "run_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        runs.append({
                            "name": run_dir.name,
                            "path": run_dir,
                            "metadata": metadata
                        })
        
        return sorted(runs, key=lambda x: x["name"], reverse=True)
    
    def load_run_results(self, run_path):
        """Load results from a specific run"""
        processed_dir = run_path / "processed"
        results = {}
        
        # Look for common result file patterns
        result_patterns = [
            "extracted_products_*.json",
            "processed_results.json",
            "final_results.json"
        ]
        
        for pattern in result_patterns:
            for result_file in processed_dir.glob(pattern):
                with open(result_file, 'r') as f:
                    results[result_file.name] = json.load(f)
                    
        return results
    
    def compare_runs(self, run1_name, run2_name):
        """Compare two runs and generate comparison report"""
        runs = {run["name"]: run for run in self.list_runs()}
        
        if run1_name not in runs or run2_name not in runs:
            raise ValueError("One or both run names not found")
            
        run1 = runs[run1_name]
        run2 = runs[run2_name]
        
        # Load results
        results1 = self.load_run_results(run1["path"])
        results2 = self.load_run_results(run2["path"])
        
        comparison = {
            "comparison_date": datetime.now().isoformat(),
            "run1": {
                "name": run1_name,
                "metadata": run1["metadata"],
                "result_files": list(results1.keys())
            },
            "run2": {
                "name": run2_name,
                "metadata": run2["metadata"],
                "result_files": list(results2.keys())
            },
            "differences": self._analyze_differences(results1, results2),
            "summary": {}
        }
        
        return comparison
    
    def _analyze_differences(self, results1, results2):
        """Analyze differences between two result sets"""
        differences = {}
        
        # Find common files
        common_files = set(results1.keys()) & set(results2.keys())
        
        for filename in common_files:
            file_diff = self._compare_file_results(
                results1[filename], 
                results2[filename]
            )
            differences[filename] = file_diff
            
        return differences
    
    def _compare_file_results(self, data1, data2):
        """Compare results from two files"""
        comparison = {
            "record_counts": {
                "run1": len(data1) if isinstance(data1, list) else 1,
                "run2": len(data2) if isinstance(data2, list) else 1
            },
            "data_quality": {},
            "field_coverage": {},
            "sample_differences": []
        }
        
        if isinstance(data1, list) and isinstance(data2, list):
            # Compare product data if both are lists
            comparison["data_quality"] = self._compare_data_quality(data1, data2)
            comparison["field_coverage"] = self._compare_field_coverage(data1, data2)
            comparison["sample_differences"] = self._find_sample_differences(data1, data2)
        
        return comparison
    
    def _compare_data_quality(self, data1, data2):
        """Compare data quality metrics between runs"""
        def calculate_quality(data):
            if not data:
                return {}
                
            total_fields = 0
            empty_fields = 0
            
            for item in data:
                for key, value in item.items():
                    total_fields += 1
                    if not value or str(value).strip() == "":
                        empty_fields += 1
                        
            return {
                "total_fields": total_fields,
                "empty_fields": empty_fields,
                "completeness": (total_fields - empty_fields) / total_fields if total_fields > 0 else 0
            }
        
        return {
            "run1": calculate_quality(data1),
            "run2": calculate_quality(data2)
        }
    
    def _compare_field_coverage(self, data1, data2):
        """Compare field coverage between runs"""
        def get_fields(data):
            fields = set()
            for item in data:
                fields.update(item.keys())
            return fields
        
        fields1 = get_fields(data1)
        fields2 = get_fields(data2)
        
        return {
            "run1_fields": sorted(fields1),
            "run2_fields": sorted(fields2),
            "common_fields": sorted(fields1 & fields2),
            "run1_only": sorted(fields1 - fields2),
            "run2_only": sorted(fields2 - fields1)
        }
    
    def _find_sample_differences(self, data1, data2, max_samples=5):
        """Find sample differences between datasets"""
        differences = []
        
        # Simple comparison of first few items
        min_len = min(len(data1), len(data2), max_samples)
        
        for i in range(min_len):
            item1 = data1[i]
            item2 = data2[i]
            
            if item1 != item2:
                differences.append({
                    "index": i,
                    "run1": item1,
                    "run2": item2
                })
                
        return differences
    
    def generate_comparison_report(self, comparison, output_path=None):
        """Generate a detailed comparison report"""
        if not output_path:
            output_path = self.client_dir / "runs" / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        with open(output_path, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)
            
        # Also generate a summary text report
        summary_path = output_path.with_suffix('.txt')
        with open(summary_path, 'w') as f:
            f.write("RUN COMPARISON SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Run 1: {comparison['run1']['name']}\n")
            f.write(f"Run 2: {comparison['run2']['name']}\n")
            f.write(f"Comparison Date: {comparison['comparison_date']}\n\n")
            
            for filename, diff in comparison['differences'].items():
                f.write(f"File: {filename}\n")
                f.write(f"  Record Count - Run1: {diff['record_counts']['run1']}, Run2: {diff['record_counts']['run2']}\n")
                
                if 'data_quality' in diff:
                    dq1 = diff['data_quality']['run1']
                    dq2 = diff['data_quality']['run2']
                    f.write(f"  Data Completeness - Run1: {dq1.get('completeness', 0):.2%}, Run2: {dq2.get('completeness', 0):.2%}\n")
                
                f.write("\n")
        
        return output_path, summary_path

def main():
    parser = argparse.ArgumentParser(description="Compare scraping runs")
    parser.add_argument("--client-dir", required=True, help="Client directory path")
    parser.add_argument("--run1", required=True, help="First run name")
    parser.add_argument("--run2", required=True, help="Second run name")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    comparator = RunComparator(args.client_dir)
    comparison = comparator.compare_runs(args.run1, args.run2)
    
    json_path, summary_path = comparator.generate_comparison_report(comparison, args.output)
    
    print(f"Comparison complete!")
    print(f"Detailed report: {json_path}")
    print(f"Summary report: {summary_path}")

if __name__ == "__main__":
    main()
