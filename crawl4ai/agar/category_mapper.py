"""
Category mapping module for Agar product catalog.

This module handles the extraction and processing of product categories,
including hierarchical category structure and product-category relationships.
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from .schemas import CategorySchema, ProductCategoryRelation, ProductSchema, ScrapingConfig
from .utils import generate_category_id, normalize_category_name, clean_text, create_slug


class CategoryMapper:
    """
    Handles category extraction and mapping for product pages.
    """
    
    def __init__(self, config: ScrapingConfig):
        """
        Initialize the CategoryMapper.
        
        Args:
            config: Scraping configuration
        """
        self.config = config
        self.category_cache = {}  # Cache for category objects
        self.category_hierarchy = {}  # Cache for hierarchy relationships
    
    def extract_categories_from_product(self, product: ProductSchema, raw_extracted_data: Dict[str, Any]) -> Tuple[List[CategorySchema], List[ProductCategoryRelation]]:
        """
        Extract categories and relationships from a product's raw extracted data.
        
        Args:
            product: Product schema object
            raw_extracted_data: Raw data extracted from the product page
            
        Returns:
            Tuple of (categories list, product-category relationships list)
        """
        if not self.config.include_categories:
            return [], []
        
        categories = []
        relationships = []
        
        # Extract category names and links
        category_names = raw_extracted_data.get("categories", [])
        category_links = raw_extracted_data.get("category_links", [])
        
        # Normalize to lists
        if isinstance(category_names, str):
            category_names = [category_names]
        if isinstance(category_links, str):
            category_links = [category_links]
        
        # Ensure category_links list is same length as category_names
        while len(category_links) < len(category_names):
            category_links.append("")
        
        # Process each category
        primary_category = True  # First category is considered primary
        for cat_name, cat_link in zip(category_names, category_links):
            if not cat_name:
                continue
            
            # Clean and normalize category name
            normalized_name = normalize_category_name(cat_name)
            if not normalized_name:
                continue
            
            # Create or get existing category
            category = self._create_or_get_category(normalized_name, cat_link, str(product.product_url))
            if category:
                categories.append(category)
                
                # Create product-category relationship
                relationship = ProductCategoryRelation(
                    product_id=product.product_id,
                    category_id=category.category_id,
                    primary=primary_category
                )
                relationships.append(relationship)
                
                primary_category = False  # Only first category is primary
        
        # Also try to infer categories from product name/description
        inferred_categories, inferred_relationships = self._infer_categories_from_content(product, raw_extracted_data)
        categories.extend(inferred_categories)
        relationships.extend(inferred_relationships)
        
        if self.config.verbose and categories:
            print(f"  Found {len(categories)} categories for product: {product.product_name}")
        
        return categories, relationships
    
    def _create_or_get_category(self, category_name: str, category_link: str = "", base_url: str = "") -> Optional[CategorySchema]:
        """
        Create a new category or get existing one from cache.
        
        Args:
            category_name: Name of the category
            category_link: Optional link to the category page
            base_url: Base URL for resolving relative links
            
        Returns:
            CategorySchema object or None
        """
        # Check cache first
        cache_key = category_name.lower()
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
        
        try:
            # Generate category ID
            category_id = generate_category_id(category_name)
            
            # Create slug
            slug = create_slug(category_name)
            
            # Process category link
            category_url = None
            if category_link:
                if not category_link.startswith('http') and base_url:
                    category_link = urljoin(base_url, category_link)
                category_url = category_link
            
            # Try to determine hierarchy level from link/name
            level = self._determine_category_level(category_name, category_link)
            
            # Try to find parent category
            parent_category_id = self._find_parent_category(category_name, category_link)
            
            # Create category schema
            category = CategorySchema(
                category_id=category_id,
                category_name=category_name,
                parent_category_id=parent_category_id,
                slug=slug,
                level=level,
                metadata={
                    "category_url": category_url,
                    "extraction_source": "product_categories"
                }
            )
            
            # Cache the category
            self.category_cache[cache_key] = category
            
            return category
            
        except Exception as e:
            if self.config.verbose:
                print(f"  Error creating category for {category_name}: {e}")
            return None
    
    def _determine_category_level(self, category_name: str, category_link: str = "") -> int:
        """
        Try to determine the hierarchy level of a category.
        
        Args:
            category_name: Name of the category
            category_link: Optional category link
            
        Returns:
            Estimated hierarchy level (0 = root)
        """
        # Analyze URL path depth
        if category_link:
            parsed = urlparse(category_link)
            path_parts = [part for part in parsed.path.split('/') if part and part != 'product-category']
            
            # More path segments usually means deeper in hierarchy
            if len(path_parts) > 2:
                return min(len(path_parts) - 1, 3)  # Cap at level 3
        
        # Analyze category name for hierarchy indicators
        hierarchy_indicators = {
            'cleaning': 0,  # Root categories
            'care': 0,
            'maintenance': 0,
            'industrial': 0,
            'commercial': 0,
            
            'floor': 1,  # Second level
            'carpet': 1,
            'window': 1,
            'kitchen': 1,
            'bathroom': 1,
            'vehicle': 1,
            
            'cleaner': 2,  # Third level
            'polish': 2,
            'disinfectant': 2,
            'degreaser': 2,
        }
        
        category_lower = category_name.lower()
        for keyword, level in hierarchy_indicators.items():
            if keyword in category_lower:
                return level
        
        return 0  # Default to root level
    
    def _find_parent_category(self, category_name: str, category_link: str = "") -> Optional[str]:
        """
        Try to find the parent category ID for a given category.
        
        Args:
            category_name: Name of the category
            category_link: Optional category link
            
        Returns:
            Parent category ID or None
        """
        # Check URL-based hierarchy
        if category_link:
            parsed = urlparse(category_link)
            path_parts = [part for part in parsed.path.split('/') if part and part != 'product-category']
            
            if len(path_parts) > 1:
                # Try to find parent in cache
                parent_slug = path_parts[-2]  # Second to last part
                parent_name = parent_slug.replace('-', ' ').title()
                
                for cached_name, cached_category in self.category_cache.items():
                    if cached_category.slug == parent_slug or cached_name == parent_name.lower():
                        return cached_category.category_id
        
        # Check name-based hierarchy patterns
        hierarchy_patterns = [
            ('floor care', 'cleaning products'),
            ('carpet care', 'cleaning products'),
            ('window cleaning', 'cleaning products'),
            ('kitchen cleaning', 'cleaning products'),
            ('bathroom cleaning', 'cleaning products'),
            ('vehicle care', 'cleaning products'),
        ]
        
        category_lower = category_name.lower()
        for child_pattern, parent_name in hierarchy_patterns:
            if child_pattern in category_lower:
                parent_id = generate_category_id(parent_name)
                
                # Ensure parent exists in cache
                if parent_name.lower() not in self.category_cache:
                    parent_category = self._create_or_get_category(parent_name)
                    if parent_category:
                        return parent_category.category_id
                else:
                    return parent_id
        
        return None
    
    def _infer_categories_from_content(self, product: ProductSchema, raw_data: Dict[str, Any]) -> Tuple[List[CategorySchema], List[ProductCategoryRelation]]:
        """
        Try to infer additional categories from product name and description.
        
        Args:
            product: Product schema object
            raw_data: Raw extracted data
            
        Returns:
            Tuple of (inferred categories, relationships)
        """
        categories = []
        relationships = []
        
        # Content to analyze
        content_text = f"{product.product_name} {product.description or ''} {raw_data.get('product_description', '')}"
        content_lower = content_text.lower()
        
        # Category inference patterns
        category_patterns = {
            # Floor care
            r'\b(floor|flooring|hard\s*floor)\b': 'Floor Care',
            r'\b(carpet|rug|upholstery)\b': 'Carpet Care',
            r'\b(tile|ceramic|porcelain)\b': 'Tile Care',
            
            # Cleaning types
            r'\b(disinfect|sanitiz|antibacterial)\b': 'Disinfectants',
            r'\b(degrease|degreaser)\b': 'Degreasers',
            r'\b(polish|shine|buff)\b': 'Polishes',
            r'\b(glass|window)\b': 'Glass Cleaners',
            
            # Application areas
            r'\b(kitchen|food\s*service)\b': 'Kitchen Cleaning',
            r'\b(bathroom|restroom|toilet)\b': 'Bathroom Cleaning',
            r'\b(office|commercial)\b': 'Commercial Cleaning',
            r'\b(industrial|heavy\s*duty)\b': 'Industrial Cleaning',
            r'\b(automotive|vehicle|car)\b': 'Vehicle Care',
            
            # Product types
            r'\b(concentrate|concentrated)\b': 'Concentrates',
            r'\b(foam|foaming)\b': 'Foam Cleaners',
            r'\b(spray|aerosol)\b': 'Spray Cleaners',
        }
        
        for pattern, category_name in category_patterns.items():
            if re.search(pattern, content_lower):
                # Check if we already have this category
                existing_category_ids = [rel.category_id for rel in relationships]
                
                category = self._create_or_get_category(category_name)
                if category and category.category_id not in existing_category_ids:
                    categories.append(category)
                    
                    # Create relationship (not primary since it's inferred)
                    relationship = ProductCategoryRelation(
                        product_id=product.product_id,
                        category_id=category.category_id,
                        primary=False
                    )
                    relationships.append(relationship)
        
        return categories, relationships
    
    def build_category_hierarchy(self, all_categories: List[CategorySchema]) -> Dict[str, List[str]]:
        """
        Build a hierarchy map from all categories.
        
        Args:
            all_categories: List of all categories
            
        Returns:
            Dictionary mapping parent IDs to lists of child IDs
        """
        hierarchy = {}
        
        for category in all_categories:
            parent_id = category.parent_category_id or "root"
            
            if parent_id not in hierarchy:
                hierarchy[parent_id] = []
            hierarchy[parent_id].append(category.category_id)
        
        return hierarchy
    
    def get_category_path(self, category_id: str, all_categories: List[CategorySchema]) -> List[str]:
        """
        Get the full path from root to a specific category.
        
        Args:
            category_id: ID of the category
            all_categories: List of all categories
            
        Returns:
            List of category names from root to target category
        """
        # Build category lookup
        category_lookup = {cat.category_id: cat for cat in all_categories}
        
        if category_id not in category_lookup:
            return []
        
        path = []
        current_category = category_lookup[category_id]
        
        # Walk up the hierarchy
        while current_category:
            path.insert(0, current_category.category_name)
            
            parent_id = current_category.parent_category_id
            current_category = category_lookup.get(parent_id) if parent_id else None
        
        return path
    
    def deduplicate_categories(self, categories: List[CategorySchema]) -> List[CategorySchema]:
        """
        Remove duplicate categories based on name.
        
        Args:
            categories: List of categories
            
        Returns:
            Deduplicated list of categories
        """
        seen_names = set()
        unique_categories = []
        
        for category in categories:
            name_key = category.category_name.lower()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_categories.append(category)
            elif self.config.verbose:
                print(f"  Filtering duplicate category: {category.category_name}")
        
        return unique_categories
    
    def sort_categories_by_hierarchy(self, categories: List[CategorySchema]) -> List[CategorySchema]:
        """
        Sort categories by hierarchy level and name.
        
        Args:
            categories: List of categories
            
        Returns:
            Sorted list of categories
        """
        return sorted(categories, key=lambda x: (x.level, x.category_name))
