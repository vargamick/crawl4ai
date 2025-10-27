#!/usr/bin/env python3
"""
Agar Enhanced Validation System
Implements critical validation requirements for Agar scraping configuration:
1. 404 Error Handling - Failed pages logged as failures, not successes
2. Output Validation - Verify required properties are captured in each processing run
"""

import json
import yaml
import re
import requests
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
from datetime import datetime


class AgarValidationSystem:
    """Enhanced validation system for Agar product scraping"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config"
        self.logger = self._setup_logging()
        self.validation_rules = self._load_validation_rules()
        self.required_fields = ["product_name", "product_image_url", "product_skus", "product_categories"]
        self.optional_fields = ["product_overview", "product_description", "product_sizes", "product_phlevel", "sds_urls", "pds_urls"]
        
    def _setup_logging(self):
        """Setup logging for validation system"""
        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('AgarValidation')
        
    def _load_validation_rules(self) -> Dict:
        """Load validation rules from configuration files"""
        try:
            with open(f"{self.config_path}/client_config.yaml", 'r') as f:
                client_config = yaml.safe_load(f)
            
            with open(f"{self.config_path}/scraping_rules.yaml", 'r') as f:
                scraping_rules = yaml.safe_load(f)
                
            with open("clients/agar/templates/extraction_templates/agar_product_extraction.yaml", 'r') as f:
                extraction_template = yaml.safe_load(f)
            
            return {
                'client_config': client_config,
                'scraping_rules': scraping_rules,
                'extraction_template': extraction_template
            }
        except Exception as e:
            self.logger.error(f"Failed to load validation rules: {e}")
            return {}

    def detect_404_error(self, content: str, url: str, status_code: int = None) -> Tuple[bool, str]:
        """
        CRITICAL: Detect 404 errors and failed pages
        Returns: (is_error, error_reason)
        """
        error_indicators = self.validation_rules.get('scraping_rules', {}).get('error_detection', {})
        
        # Check HTTP status code
        if status_code in [404, 410, 500, 502, 503, 504]:
            return True, f"HTTP Status Code: {status_code}"
            
        # Check title patterns
        title_patterns = error_indicators.get('page_not_found_indicators', {}).get('title_patterns', [])
        for pattern in title_patterns:
            if pattern.lower() in content.lower():
                return True, f"Title contains error pattern: {pattern}"
                
        # Check content patterns
        content_patterns = error_indicators.get('page_not_found_indicators', {}).get('content_patterns', [])
        for pattern in content_patterns:
            if pattern.lower() in content.lower():
                return True, f"Content contains error pattern: {pattern}"
                
        # Check for minimum content length
        min_length = error_indicators.get('content_validation', {}).get('min_content_length', 500)
        if len(content.strip()) < min_length:
            return True, f"Content too short ({len(content.strip())} < {min_length} chars)"
            
        # Check for required elements (basic HTML structure check)
        required_elements = error_indicators.get('content_validation', {}).get('required_elements', [])
        for element in required_elements:
            if f"<{element}" not in content.lower():
                return True, f"Missing required HTML element: {element}"
                
        return False, ""

    def validate_required_fields(self, extracted_data: Dict) -> Tuple[bool, List[str]]:
        """
        CRITICAL: Validate that all required properties are captured
        Returns: (is_valid, missing_fields)
        """
        missing_fields = []
        
        for field in self.required_fields:
            if field not in extracted_data or not extracted_data[field]:
                missing_fields.append(field)
                
        return len(missing_fields) == 0, missing_fields

    def validate_field_quality(self, field_name: str, field_value: Any) -> Tuple[bool, str]:
        """Validate individual field quality based on validation rules"""
        validation_rules = self.validation_rules.get('extraction_template', {}).get('validation_rules', {})
        field_rules = validation_rules.get(field_name, {})
        
        if not field_rules:
            return True, ""  # No rules defined
            
        # Check if field is required and empty
        if field_rules.get('required', False) and not field_value:
            return False, f"{field_name} is required but empty"
            
        # Skip validation if field is empty and not required
        if not field_value and not field_rules.get('required', False):
            return True, ""
            
        # String validation
        if isinstance(field_value, str):
            # Min/Max length validation
            min_length = field_rules.get('min_length', 0)
            max_length = field_rules.get('max_length', float('inf'))
            
            if len(field_value) < min_length:
                return False, f"{field_name} too short (min: {min_length})"
            if len(field_value) > max_length:
                return False, f"{field_name} too long (max: {max_length})"
                
            # Pattern validation
            pattern = field_rules.get('pattern')
            if pattern and not re.match(pattern, field_value):
                return False, f"{field_name} doesn't match required pattern"
                
            # Generic value check
            not_generic = field_rules.get('not_generic_values', [])
            if field_value in not_generic:
                return False, f"{field_name} contains generic/placeholder value: {field_value}"
                
        # URL validation
        if field_rules.get('format') == 'url':
            if not self._is_valid_url(field_value):
                return False, f"{field_name} is not a valid URL"
                
            # File extension validation
            extensions = field_rules.get('file_extensions', [])
            if extensions and not any(field_value.lower().endswith(ext) for ext in extensions):
                return False, f"{field_name} doesn't have valid file extension"
                
        # Collection validation
        if isinstance(field_value, list):
            min_items = field_rules.get('min_items', 0)
            if len(field_value) < min_items:
                return False, f"{field_name} has too few items (min: {min_items})"
                
        return True, ""

    def validate_extraction_output(self, extracted_data: Dict, url: str) -> Dict:
        """
        CRITICAL: Comprehensive validation of extraction output
        Returns validation report with success/failure status
        """
        validation_report = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'is_valid': True,
            'quality_score': 0,
            'validation_results': {},
            'missing_required_fields': [],
            'field_quality_issues': [],
            'warnings': [],
            'success_criteria_met': True
        }
        
        # Validate required fields
        has_required, missing_required = self.validate_required_fields(extracted_data)
        validation_report['missing_required_fields'] = missing_required
        
        if not has_required:
            validation_report['is_valid'] = False
            validation_report['success_criteria_met'] = False
            self.logger.error(f"Missing required fields for {url}: {missing_required}")
            
        # Validate individual field quality
        all_fields = self.required_fields + self.optional_fields
        field_scores = {}
        
        for field in all_fields:
            field_value = extracted_data.get(field)
            is_valid, error_msg = self.validate_field_quality(field, field_value)
            
            field_scores[field] = {
                'present': field_value is not None and field_value != "",
                'valid': is_valid,
                'error': error_msg
            }
            
            if not is_valid and error_msg:
                validation_report['field_quality_issues'].append(f"{field}: {error_msg}")
                if field in self.required_fields:
                    validation_report['is_valid'] = False
                else:
                    validation_report['warnings'].append(f"Optional field issue - {field}: {error_msg}")
                    
        validation_report['validation_results'] = field_scores
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(extracted_data, field_scores)
        validation_report['quality_score'] = quality_score
        
        # Check success criteria
        min_quality = 60  # From configuration
        if quality_score < min_quality:
            validation_report['success_criteria_met'] = False
            validation_report['warnings'].append(f"Quality score ({quality_score}) below minimum ({min_quality})")
            
        self.logger.info(f"Validation complete for {url}. Valid: {validation_report['is_valid']}, Quality: {quality_score}")
        return validation_report

    def _calculate_quality_score(self, extracted_data: Dict, field_scores: Dict) -> float:
        """Calculate overall quality score for extracted data"""
        weights = {
            'required_fields_present': 40,
            'optional_fields_present': 20,
            'data_format_validity': 25,
            'content_meaningfulness': 15
        }
        
        # Required fields score
        required_present = sum(1 for field in self.required_fields if field_scores[field]['present'])
        required_score = (required_present / len(self.required_fields)) * 100
        
        # Optional fields score
        optional_present = sum(1 for field in self.optional_fields if field_scores[field]['present'])
        optional_score = (optional_present / len(self.optional_fields)) * 100
        
        # Data validity score
        valid_fields = sum(1 for field, score in field_scores.items() if score['valid'])
        validity_score = (valid_fields / len(field_scores)) * 100
        
        # Content meaningfulness (basic heuristic)
        meaningfulness_score = 75  # Default assumption, would need more complex analysis
        
        # Calculate weighted score
        total_score = (
            (required_score * weights['required_fields_present']) +
            (optional_score * weights['optional_fields_present']) +
            (validity_score * weights['data_format_validity']) +
            (meaningfulness_score * weights['content_meaningfulness'])
        ) / 100
        
        return round(total_score, 1)

    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def process_extraction_results(self, results_file: str) -> Dict:
        """
        Process extraction results file and validate all entries
        Returns comprehensive validation summary
        """
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
                
            if not isinstance(results, list):
                results = [results]  # Handle single result
                
        except Exception as e:
            self.logger.error(f"Failed to load results file {results_file}: {e}")
            return {'error': f"Failed to load results file: {e}"}
            
        validation_summary = {
            'total_extractions': len(results),
            'successful_extractions': 0,
            'failed_extractions': 0,
            'validation_reports': [],
            'overall_quality_score': 0,
            'common_issues': {},
            'processing_timestamp': datetime.now().isoformat()
        }
        
        quality_scores = []
        issue_counts = {}
        
        for result in results:
            url = result.get('url', 'unknown')
            extracted_data = result.get('extracted_data', result)
            
            # Run validation
            validation_report = self.validate_extraction_output(extracted_data, url)
            validation_summary['validation_reports'].append(validation_report)
            
            if validation_report['is_valid'] and validation_report['success_criteria_met']:
                validation_summary['successful_extractions'] += 1
            else:
                validation_summary['failed_extractions'] += 1
                
            quality_scores.append(validation_report['quality_score'])
            
            # Count common issues
            for issue in validation_report['field_quality_issues']:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
                
        # Calculate overall metrics
        if quality_scores:
            validation_summary['overall_quality_score'] = round(sum(quality_scores) / len(quality_scores), 1)
            
        validation_summary['common_issues'] = dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Log summary
        success_rate = (validation_summary['successful_extractions'] / validation_summary['total_extractions']) * 100
        self.logger.info(f"Validation Summary: {validation_summary['successful_extractions']}/{validation_summary['total_extractions']} successful ({success_rate:.1f}%), Average Quality: {validation_summary['overall_quality_score']}")
        
        return validation_summary

    def create_validation_report(self, validation_summary: Dict, output_path: str = None):
        """Create detailed validation report file"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"clients/agar/reports/validation_report_{timestamp}.json"
            
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(validation_summary, f, indent=2)
            
        self.logger.info(f"Validation report created: {output_path}")
        return output_path


def main():
    """Test the validation system with sample data"""
    validator = AgarValidationSystem()
    
    # Test 404 detection
    print("=== Testing 404 Error Detection ===")
    
    test_404_content = """
    <!DOCTYPE html>
    <html>
    <head><title>404 - Page Not Found</title></head>
    <body>
        <h1>Oops! Page Not Found</h1>
        <p>The page you requested could not be found.</p>
    </body>
    </html>
    """
    
    is_error, reason = validator.detect_404_error(test_404_content, "https://test.com/missing", 404)
    print(f"404 Detection Result: {is_error}, Reason: {reason}")
    
    # Test validation with sample extraction data
    print("\n=== Testing Output Validation ===")
    
    sample_extraction = {
        "url": "https://agar.com.au/product/test-product/",
        "product_name": "Test Cleaning Product",
        "product_image_url": "https://agar.com.au/images/test-product.jpg",
        "product_skus": ["TCP001", "TCP002"],
        "product_categories": ["Cleaning Products", "Industrial Cleaners"],
        "product_overview": "This is a test cleaning product for industrial use.",
        "product_description": "Detailed description of the test cleaning product...",
        "product_sizes": ["500mL", "1L", "5L"],
        "product_phlevel": "10.5 ± 0.5",
        "sds_urls": ["https://agar.com.au/sds/tcp001.pdf"],
        "pds_urls": ["https://agar.com.au/pds/tcp001.pdf"]
    }
    
    validation_report = validator.validate_extraction_output(sample_extraction, sample_extraction["url"])
    print(f"Validation Result: {validation_report['is_valid']}")
    print(f"Quality Score: {validation_report['quality_score']}")
    print(f"Missing Required Fields: {validation_report['missing_required_fields']}")
    print(f"Quality Issues: {validation_report['field_quality_issues']}")
    
    # Test with incomplete data
    print("\n=== Testing Incomplete Data Validation ===")
    
    incomplete_extraction = {
        "url": "https://agar.com.au/product/incomplete/",
        "product_name": "",  # Missing required field
        "product_image_url": "not-a-url",  # Invalid URL
        "product_skus": [],  # Empty required collection
        # missing product_categories entirely
    }
    
    validation_report = validator.validate_extraction_output(incomplete_extraction, incomplete_extraction["url"])
    print(f"Incomplete Data Validation Result: {validation_report['is_valid']}")
    print(f"Quality Score: {validation_report['quality_score']}")
    print(f"Missing Required Fields: {validation_report['missing_required_fields']}")
    print(f"Quality Issues: {validation_report['field_quality_issues']}")


if __name__ == "__main__":
    main()
