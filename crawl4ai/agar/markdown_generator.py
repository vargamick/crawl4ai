"""
Markdown generator for Agar product catalog per technical brief.

This module generates formatted Markdown documentation for each product
following the exact template specification in the Agar Scraping Technical Brief v1.0.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import os
from urllib.parse import urlparse

from .schemas import ProductSchema


class MarkdownGenerator:
    """
    Generates Markdown documentation for Agar products per technical brief template.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the MarkdownGenerator.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
    
    def generate_product_markdown(self, product: ProductSchema) -> str:
        """
        Generate Markdown content for a single product following brief template.
        
        Args:
            product: ProductSchema object
            
        Returns:
            Formatted Markdown string
        """
        # Extract data from product metadata
        metadata = product.metadata or {}
        codes = metadata.get("codes", [])
        skus = metadata.get("skus", [])
        categories = metadata.get("categories", [])
        tags = metadata.get("tags", [])
        sizes = metadata.get("sizes", [])
        specifications = metadata.get("specifications", {})
        key_benefits = metadata.get("key_benefits", [])
        documents = metadata.get("documents", [])
        reviews = metadata.get("reviews", {})
        
        # Build Markdown content following exact brief template
        markdown_lines = []
        
        # Title
        markdown_lines.append(f"# {product.product_name}")
        markdown_lines.append("")
        
        # Product Information section
        markdown_lines.append("## Product Information")
        
        if codes:
            codes_str = ", ".join(codes)
            markdown_lines.append(f"- **Product Code(s)**: {codes_str}")
        
        if skus:
            skus_str = ", ".join(skus)
            markdown_lines.append(f"- **SKU(s)**: {skus_str}")
        
        if sizes:
            sizes_str = ", ".join(sizes)
            markdown_lines.append(f"- **Available Sizes**: {sizes_str}")
        
        if categories:
            categories_str = ", ".join(categories)
            markdown_lines.append(f"- **Categories**: {categories_str}")
        
        if tags:
            tags_str = ", ".join(tags)
            markdown_lines.append(f"- **Tags**: {tags_str}")
        
        markdown_lines.append("")
        
        # Overview section
        if product.description:
            markdown_lines.append("## Overview")
            markdown_lines.append(product.description)
            markdown_lines.append("")
        
        # Key Benefits section
        if key_benefits:
            markdown_lines.append("## Key Benefits")
            for benefit in key_benefits:
                markdown_lines.append(f"- {benefit}")
            markdown_lines.append("")
        
        # Technical Details section
        markdown_lines.append("## Technical Details")
        markdown_lines.append("")
        
        # Extract detailed description sections from raw data
        raw_data = metadata.get("raw_extracted_data", {})
        description_content = raw_data.get("description_content", "")
        
        if description_content:
            # Try to extract "How Does It Work?" section
            how_it_works = self._extract_section(description_content, "How Does It Work?")
            if how_it_works:
                markdown_lines.append("### How Does It Work?")
                markdown_lines.append(how_it_works)
                markdown_lines.append("")
            
            # Try to extract "For Use On..." or "Applications" section
            applications = (
                self._extract_section(description_content, "For Use On") or
                self._extract_section(description_content, "Applications")
            )
            if applications:
                markdown_lines.append("### Applications")
                markdown_lines.append(applications)
                markdown_lines.append("")
        
        # Specifications table
        if specifications:
            markdown_lines.append("### Specifications")
            markdown_lines.append("| Property | Value |")
            markdown_lines.append("|----------|-------|")
            
            for prop, value in specifications.items():
                prop_formatted = prop.replace('_', ' ').title()
                markdown_lines.append(f"| {prop_formatted} | {value} |")
            
            markdown_lines.append("")
        
        # Documentation section
        if documents:
            markdown_lines.append("## Documentation")
            
            for doc in documents:
                doc_name = doc.get("name", "Document")
                doc_url = doc.get("url", "")
                doc_type = doc.get("type", "").upper()
                
                if doc_type in ["SDS", "PDS"]:
                    type_full = "Safety Data Sheet" if doc_type == "SDS" else "Product Data Sheet"
                    markdown_lines.append(f"- [{type_full} ({doc_type})]({doc_url})")
                else:
                    markdown_lines.append(f"- [{doc_name}]({doc_url})")
            
            markdown_lines.append("")
        
        # Customer Reviews section
        if reviews and (reviews.get("rating") or reviews.get("count", 0) > 0):
            markdown_lines.append("## Customer Reviews")
            
            rating = reviews.get("rating")
            count = reviews.get("count", 0)
            
            if rating:
                stars = "★" * int(rating) + "☆" * (5 - int(rating))
                markdown_lines.append(f"**Rating**: {stars} ({rating}/5.0) ({count} reviews)")
            else:
                markdown_lines.append(f"**Reviews**: {count} customer reviews")
            
            markdown_lines.append("")
        
        # Footer
        markdown_lines.append("---")
        markdown_lines.append(f"*Last Updated: {datetime.now().strftime('%Y-%m-%d')}*")
        
        return "\n".join(markdown_lines)
    
    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """
        Extract a specific section from description content.
        
        Args:
            content: Full description content
            section_name: Name of section to extract
            
        Returns:
            Extracted section content or None
        """
        if not content:
            return None
        
        # Try to find section by heading
        patterns = [
            rf"(?i)(?:^|\n)#+\s*{re.escape(section_name)}[?\s]*\n?(.*?)(?=\n#+|\n\n\n|\Z)",
            rf"(?i)(?:^|\n){re.escape(section_name)}[?\s]*\n?(.*?)(?=\n[A-Z][^.]*[?\n]|\n\n|\Z)",
            rf"(?i){re.escape(section_name)}[?\s]*\n?(.*?)(?=\n[A-Z]|\n\n|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                section_content = match.group(1).strip()
                if section_content and len(section_content) > 20:  # Minimum content length
                    return section_content
        
        return None
    
    def save_product_markdown(self, product: ProductSchema, product_dir: Optional[str] = None) -> str:
        """
        Save product Markdown to file following brief directory structure.
        
        Args:
            product: ProductSchema object
            product_dir: Optional custom directory name
            
        Returns:
            Path to saved Markdown file
        """
        # Generate Markdown content
        markdown_content = self.generate_product_markdown(product)
        
        # Create product directory name
        if not product_dir:
            # Extract product name from URL for directory name
            url_path = urlparse(str(product.product_url)).path
            product_dir = url_path.strip('/').split('/')[-1]
            if not product_dir or product_dir == 'product':
                # Fallback to cleaned product name
                product_dir = re.sub(r'[^\w\s-]', '', product.product_name.lower())
                product_dir = re.sub(r'[-\s]+', '-', product_dir)
        
        # Create directory structure: output/products/{product_name}/
        products_dir = os.path.join(self.output_dir, "products", product_dir)
        os.makedirs(products_dir, exist_ok=True)
        
        # Save Markdown file
        markdown_filename = f"{product_dir}.md"
        markdown_path = os.path.join(products_dir, markdown_filename)
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return markdown_path
    
    def generate_index_markdown(self, products: List[ProductSchema]) -> str:
        """
        Generate index Markdown file listing all products.
        
        Args:
            products: List of ProductSchema objects
            
        Returns:
            Formatted index Markdown string
        """
        markdown_lines = []
        
        # Title and header
        markdown_lines.append("# Agar Product Catalog")
        markdown_lines.append("")
        markdown_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        markdown_lines.append(f"Total Products: {len(products)}")
        markdown_lines.append("")
        
        # Group products by category for better organization
        categories = {}
        for product in products:
            product_categories = product.metadata.get("categories", [])
            if product_categories:
                primary_category = product_categories[0]
            else:
                primary_category = "Uncategorized"
            
            if primary_category not in categories:
                categories[primary_category] = []
            categories[primary_category].append(product)
        
        # Generate category sections
        for category, category_products in sorted(categories.items()):
            markdown_lines.append(f"## {category}")
            markdown_lines.append("")
            
            for product in sorted(category_products, key=lambda p: p.product_name):
                # Create product directory name for link
                url_path = urlparse(str(product.product_url)).path
                product_dir = url_path.strip('/').split('/')[-1]
                
                # Product link and details
                markdown_lines.append(f"### [{product.product_name}](products/{product_dir}/{product_dir}.md)")
                
                if product.description:
                    # Add shortened description
                    short_desc = product.description[:200] + "..." if len(product.description) > 200 else product.description
                    markdown_lines.append(short_desc)
                
                # Add key product info
                metadata = product.metadata or {}
                codes = metadata.get("codes", [])
                sizes = metadata.get("sizes", [])
                
                details = []
                if codes:
                    details.append(f"**Codes**: {', '.join(codes)}")
                if sizes:
                    details.append(f"**Sizes**: {', '.join(sizes)}")
                
                if details:
                    markdown_lines.append(" | ".join(details))
                
                markdown_lines.append("")
        
        return "\n".join(markdown_lines)
    
    def save_index_markdown(self, products: List[ProductSchema]) -> str:
        """
        Save index Markdown file.
        
        Args:
            products: List of ProductSchema objects
            
        Returns:
            Path to saved index file
        """
        # Generate index content
        index_content = self.generate_index_markdown(products)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save index file
        index_path = os.path.join(self.output_dir, "index.md")
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        return index_path
    
    def generate_all_markdown(self, products: List[ProductSchema]) -> Dict[str, str]:
        """
        Generate all Markdown files for a list of products.
        
        Args:
            products: List of ProductSchema objects
            
        Returns:
            Dictionary mapping product names to file paths
        """
        generated_files = {}
        
        # Generate individual product Markdown files
        for product in products:
            try:
                markdown_path = self.save_product_markdown(product)
                generated_files[product.product_name] = markdown_path
            except Exception as e:
                print(f"Error generating Markdown for {product.product_name}: {e}")
        
        # Generate index file
        try:
            index_path = self.save_index_markdown(products)
            generated_files["_index"] = index_path
        except Exception as e:
            print(f"Error generating index Markdown: {e}")
        
        return generated_files
