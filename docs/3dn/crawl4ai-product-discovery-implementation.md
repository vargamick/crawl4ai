# Crawl4AI Product Discovery & Download System - Implementation Guide

## Project Overview

Transform Crawl4AI into a comprehensive product discovery, categorization, and download system that maps discovered products to a structured database schema while downloading all associated files.

---

## Prompt for Cline

### Task: Implement Product Discovery Extensions for Crawl4AI

**Objective**: Extend Crawl4AI to create a specialized product discovery system that:
- Discovers and extracts product information from e-commerce/product websites
- Maps products to hierarchical categories and industries
- Downloads all product attachments (PDFs, images, specifications)
- Outputs structured data matching the provided database schema

**Base Framework**: Use Crawl4AI's existing capabilities as the foundation and extend with custom modules.

---

## Implementation Requirements

### 1. Project Structure

Create the following project structure with client extension support:

```
crawl4ai-product-discovery/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_pipeline.py
│   │   ├── plugin_manager.py
│   │   └── client_registry.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base_strategy.py
│   │   ├── product_schema_extraction.py
│   │   └── attachment_discovery.py
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── base_module.py
│   │   ├── category_builder.py
│   │   ├── industry_detector.py
│   │   └── attachment_downloader.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── product_discovery_pipeline.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schema_models.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── database_generator.py
│   │   └── file_organizer.py
│   └── clients/
│       ├── __init__.py
│       ├── base_client.py
│       ├── agar/
│       │   ├── __init__.py
│       │   ├── agar_client.py
│       │   ├── agar_strategies.py
│       │   └── agar_config.yaml
│       └── [other_clients]/
├── config/
│   ├── base_config.yaml
│   ├── crawler_config.yaml
│   ├── schema_config.json
│   └── clients/
│       ├── agar.yaml
│       └── [client_name].yaml
├── extensions/
│   ├── __init__.py
│   └── README.md
├── downloads/
│   └── [organized by client/site/product/type]
├── output/
│   ├── database/
│   └── reports/
├── tests/
│   └── test_extraction.py
├── requirements.txt
└── README.md
```

---

### 2. Core Extension Framework

#### **File: `src/core/base_pipeline.py`**
```python
"""
Base pipeline class for extensible client implementations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import importlib
import yaml
from pathlib import Path

class BasePipeline(ABC):
    """
    Abstract base class for all pipeline implementations
    """
    
    def __init__(self, client_name: str, config_path: Optional[str] = None):
        self.client_name = client_name
        self.config = self.load_config(config_path)
        self.plugins = {}
        self.hooks = {}
        self.setup_pipeline()
    
    def load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        Load configuration with client-specific overrides
        """
        # Load base configuration
        base_config_path = Path("config/base_config.yaml")
        with open(base_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Load client-specific configuration
        client_config_path = Path(f"config/clients/{self.client_name}.yaml")
        if client_config_path.exists():
            with open(client_config_path, 'r') as f:
                client_config = yaml.safe_load(f)
                config = self.merge_configs(config, client_config)
        
        # Load custom config if provided
        if config_path:
            with open(config_path, 'r') as f:
                custom_config = yaml.safe_load(f)
                config = self.merge_configs(config, custom_config)
        
        return config
    
    def merge_configs(self, base: Dict, override: Dict) -> Dict:
        """
        Deep merge configuration dictionaries
        """
        merged = base.copy()
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    @abstractmethod
    def setup_pipeline(self):
        """
        Setup pipeline components - must be implemented by client
        """
        pass
    
    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the pipeline - must be implemented by client
        """
        pass
    
    def register_hook(self, hook_name: str, callback):
        """
        Register a hook for extension points
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
    
    async def run_hooks(self, hook_name: str, data: Any) -> Any:
        """
        Run all registered hooks for a given extension point
        """
        if hook_name in self.hooks:
            for hook in self.hooks[hook_name]:
                data = await hook(data) if asyncio.iscoroutinefunction(hook) else hook(data)
        return data
    
    def load_plugin(self, plugin_name: str, plugin_config: Dict = None):
        """
        Dynamically load a plugin
        """
        try:
            module = importlib.import_module(f"extensions.{plugin_name}")
            plugin_class = getattr(module, f"{plugin_name.title()}Plugin")
            self.plugins[plugin_name] = plugin_class(self, plugin_config or {})
            return self.plugins[plugin_name]
        except Exception as e:
            raise ImportError(f"Failed to load plugin {plugin_name}: {e}")
```

#### **File: `src/core/plugin_manager.py`**
```python
"""
Plugin manager for dynamic extension loading
"""
from typing import Dict, Any, List
import importlib
import inspect
from pathlib import Path

class PluginManager:
    """
    Manages dynamic loading and registration of plugins
    """
    
    def __init__(self):
        self.plugins = {}
        self.strategies = {}
        self.modules = {}
        self.hooks = {}
    
    def discover_plugins(self, plugin_dir: str = "extensions"):
        """
        Automatically discover and register plugins
        """
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            return
        
        for plugin_file in plugin_path.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
                
            module_name = f"{plugin_dir}.{plugin_file.stem}"
            try:
                module = importlib.import_module(module_name)
                
                # Look for plugin classes
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and hasattr(obj, "__plugin__"):
                        plugin_info = obj.__plugin__
                        self.register_plugin(
                            plugin_info["name"],
                            obj,
                            plugin_info.get("type", "general")
                        )
            except Exception as e:
                print(f"Failed to load plugin from {plugin_file}: {e}")
    
    def register_plugin(self, name: str, plugin_class: type, plugin_type: str = "general"):
        """
        Register a plugin
        """
        if plugin_type == "strategy":
            self.strategies[name] = plugin_class
        elif plugin_type == "module":
            self.modules[name] = plugin_class
        else:
            self.plugins[name] = plugin_class
    
    def get_plugin(self, name: str, plugin_type: str = "general"):
        """
        Get a registered plugin
        """
        if plugin_type == "strategy":
            return self.strategies.get(name)
        elif plugin_type == "module":
            return self.modules.get(name)
        else:
            return self.plugins.get(name)
    
    def list_plugins(self) -> Dict[str, List[str]]:
        """
        List all registered plugins
        """
        return {
            "general": list(self.plugins.keys()),
            "strategies": list(self.strategies.keys()),
            "modules": list(self.modules.keys())
        }
```

#### **File: `src/core/client_registry.py`**
```python
"""
Registry for client-specific implementations
"""
from typing import Dict, Type, Optional
import importlib
from pathlib import Path

class ClientRegistry:
    """
    Registry for managing multiple client implementations
    """
    
    _instance = None
    _clients = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_client(cls, name: str, client_class: Type):
        """
        Register a client implementation
        """
        cls._clients[name] = client_class
    
    @classmethod
    def get_client(cls, name: str):
        """
        Get a registered client class
        """
        if name not in cls._clients:
            # Try to auto-load from clients directory
            cls._auto_load_client(name)
        
        return cls._clients.get(name)
    
    @classmethod
    def _auto_load_client(cls, name: str):
        """
        Attempt to automatically load a client from the clients directory
        """
        try:
            module = importlib.import_module(f"src.clients.{name}.{name}_client")
            client_class = getattr(module, f"{name.title()}Client")
            cls.register_client(name, client_class)
        except Exception as e:
            print(f"Failed to auto-load client {name}: {e}")
    
    @classmethod
    def list_clients(cls) -> List[str]:
        """
        List all registered clients
        """
        # Auto-discover clients from directory
        clients_path = Path("src/clients")
        if clients_path.exists():
            for client_dir in clients_path.iterdir():
                if client_dir.is_dir() and not client_dir.name.startswith("_"):
                    if client_dir.name not in cls._clients:
                        cls._auto_load_client(client_dir.name)
        
        return list(cls._clients.keys())
    
    @classmethod
    def create_client(cls, name: str, config_path: Optional[str] = None):
        """
        Create a client instance
        """
        client_class = cls.get_client(name)
        if client_class:
            return client_class(config_path=config_path)
        else:
            raise ValueError(f"Client '{name}' not found in registry")
```

#### **File: `src/clients/base_client.py`**
```python
"""
Base client class for all client implementations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import asyncio
from ..core.base_pipeline import BasePipeline
from ..core.plugin_manager import PluginManager

class BaseClient(BasePipeline):
    """
    Base client implementation with common functionality
    """
    
    def __init__(self, client_name: str, config_path: Optional[str] = None):
        self.plugin_manager = PluginManager()
        super().__init__(client_name, config_path)
        self.load_client_plugins()
    
    def load_client_plugins(self):
        """
        Load client-specific plugins
        """
        # Load plugins from client directory
        client_plugin_dir = f"src/clients/{self.client_name}/plugins"
        if Path(client_plugin_dir).exists():
            self.plugin_manager.discover_plugins(client_plugin_dir)
        
        # Load configured plugins
        if "plugins" in self.config:
            for plugin_name in self.config["plugins"]:
                plugin_config = self.config.get("plugin_config", {}).get(plugin_name, {})
                self.load_plugin(plugin_name, plugin_config)
    
    def get_extraction_strategy(self):
        """
        Get client-specific extraction strategy or default
        """
        strategy_name = self.config.get("extraction_strategy", "default")
        
        # Check for client-specific strategy
        client_strategy = self.plugin_manager.get_plugin(
            f"{self.client_name}_{strategy_name}", 
            "strategy"
        )
        
        if client_strategy:
            return client_strategy(self.config)
        
        # Fall back to default strategy
        return self.get_default_extraction_strategy()
    
    @abstractmethod
    def get_default_extraction_strategy(self):
        """
        Get default extraction strategy - must be implemented
        """
        pass
    
    def customize_for_client(self, component: Any) -> Any:
        """
        Apply client-specific customizations to a component
        """
        customization_method = f"customize_{component.__class__.__name__.lower()}"
        if hasattr(self, customization_method):
            return getattr(self, customization_method)(component)
        return component
```

#### **File: `src/clients/agar/agar_client.py`**
```python
"""
Agar client implementation with specialized functionality
"""
from typing import Dict, Any, List, Optional
import asyncio
from pathlib import Path
from ..base_client import BaseClient
from ...strategies.product_schema_extraction import ProductSchemaExtractionStrategy
from .agar_strategies import AgarExtractionStrategy, AgarCategoryStrategy

class AgarClient(BaseClient):
    """
    Agar-specific implementation with custom functionality
    """
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__("agar", config_path)
    
    def setup_pipeline(self):
        """
        Setup Agar-specific pipeline components
        """
        # Use Agar-specific strategies
        self.extraction_strategy = AgarExtractionStrategy(self.config)
        self.category_strategy = AgarCategoryStrategy(self.config)
        
        # Load Agar-specific modules
        from ...modules.attachment_downloader import ProductAttachmentDownloader
        from ...modules.industry_detector import IndustryDetector
        
        self.attachment_downloader = ProductAttachmentDownloader(
            base_download_path=self.config.get("download_path", f"./downloads/agar")
        )
        
        self.industry_detector = IndustryDetector(
            llm_provider=self.config.get("llm_provider")
        )
        
        # Register Agar-specific hooks
        self.register_hooks()
    
    def register_hooks(self):
        """
        Register Agar-specific processing hooks
        """
        # Hook for post-extraction processing
        self.register_hook("post_extraction", self.agar_post_extraction)
        
        # Hook for custom categorization
        self.register_hook("categorize_product", self.agar_categorize_product)
        
        # Hook for industry mapping
        self.register_hook("map_industries", self.agar_map_industries)
    
    async def agar_post_extraction(self, data: Dict) -> Dict:
        """
        Agar-specific post-extraction processing
        """
        # Add Agar-specific fields
        if "product" in data:
            # Example: Add supplier code parsing
            if "agar_code" not in data["product"]:
                data["product"]["agar_code"] = self.extract_agar_code(data["product"].get("sku", ""))
            
            # Add Agar-specific categorization
            if self.config.get("agar_features", {}).get("auto_categorize"):
                data["categories"] = await self.auto_categorize_agar_product(data["product"])
        
        return data
    
    async def agar_categorize_product(self, product: Dict) -> List[str]:
        """
        Agar-specific product categorization logic
        """
        categories = []
        
        # Agar has specific category mappings
        agar_categories = self.config.get("agar_categories", {})
        
        product_name = product.get("name", "").lower()
        for category, keywords in agar_categories.items():
            if any(keyword in product_name for keyword in keywords):
                categories.append(category)
        
        return categories
    
    async def agar_map_industries(self, product: Dict) -> List[str]:
        """
        Agar-specific industry mapping
        """
        industries = []
        
        # Agar focuses on specific industries
        agar_industries = self.config.get("agar_industries", [
            "healthcare",
            "aged-care",
            "food-service",
            "commercial-cleaning"
        ])
        
        # Use specialized detection for Agar products
        product_desc = f"{product.get('name', '')} {product.get('description', '')}"
        
        if "hospital" in product_desc.lower() or "medical" in product_desc.lower():
            industries.append("healthcare")
        
        if "aged care" in product_desc.lower() or "nursing home" in product_desc.lower():
            industries.append("aged-care")
        
        return industries
    
    def extract_agar_code(self, sku: str) -> str:
        """
        Extract Agar-specific product code
        """
        # Agar uses specific code format
        import re
        pattern = r'AG[A-Z0-9]{4,6}'
        match = re.search(pattern, sku)
        return match.group(0) if match else ""
    
    async def auto_categorize_agar_product(self, product: Dict) -> List[str]:
        """
        Auto-categorize products based on Agar's catalog structure
        """
        categories = []
        
        # Agar-specific category logic
        name = product.get("name", "").lower()
        
        if "disinfectant" in name:
            categories.append("Disinfectant & Antibacterial Detergents")
        if "floor" in name:
            categories.append("Floor Care")
        if "laundry" in name:
            categories.append("Laundry Products")
        if "kitchen" in name:
            categories.append("Kitchen & Food Service")
        
        return categories
    
    async def run(self, site_url: str, **kwargs) -> Dict[str, Any]:
        """
        Run Agar-specific discovery pipeline
        """
        from crawl4ai import AsyncWebCrawler, BrowserConfig
        
        # Use Agar-specific browser configuration
        browser_config = BrowserConfig(
            headless=self.config.get("headless", True),
            user_agent=self.config.get("agar_user_agent", None)
        )
        
        async with AsyncWebCrawler(browser_config=browser_config) as crawler:
            # Run discovery with Agar customizations
            results = await self.discover_products(crawler, site_url)
            
            # Apply Agar-specific post-processing
            results = await self.run_hooks("post_discovery", results)
            
            # Generate Agar-specific outputs
            await self.generate_agar_outputs(results)
            
            return results
    
    async def discover_products(self, crawler, site_url: str) -> Dict:
        """
        Discover products with Agar-specific logic
        """
        products = []
        
        # Use Agar-specific URL patterns
        product_patterns = self.config.get("agar_url_patterns", [
            "/products/",
            "/chemicals/",
            "/equipment/"
        ])
        
        # Discover URLs
        urls = await self.discover_urls_with_patterns(crawler, site_url, product_patterns)
        
        # Extract products with Agar strategy
        for url in urls:
            product_data = await self.extract_with_strategy(crawler, url)
            
            # Apply Agar hooks
            product_data = await self.run_hooks("post_extraction", product_data)
            
            if product_data:
                products.append(product_data)
        
        return {"products": products, "site": site_url}
    
    async def extract_with_strategy(self, crawler, url: str) -> Dict:
        """
        Extract using Agar-specific strategy
        """
        result = await crawler.arun(
            url=url,
            extraction_strategy=self.extraction_strategy
        )
        
        return result.extracted_content if result else None
    
    async def discover_urls_with_patterns(self, crawler, site_url: str, patterns: List[str]) -> List[str]:
        """
        Discover URLs matching Agar patterns
        """
        urls = set()
        
        # Implement Agar-specific URL discovery
        result = await crawler.arun(url=site_url)
        
        # Extract all links
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(result.html, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(pattern in href for pattern in patterns):
                urls.add(href if href.startswith('http') else f"{site_url}{href}")
        
        return list(urls)
    
    async def generate_agar_outputs(self, results: Dict):
        """
        Generate Agar-specific output formats
        """
        output_dir = Path(self.config.get("output_path", "./output/agar"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate Agar-specific CSV format
        import csv
        csv_path = output_dir / "agar_products.csv"
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Agar Code', 'Product Name', 'Category', 
                'Industries', 'Pack Size', 'Unit Price'
            ])
            
            for product in results.get("products", []):
                writer.writerow([
                    product.get("product", {}).get("agar_code", ""),
                    product.get("product", {}).get("name", ""),
                    ', '.join(product.get("categories", [])),
                    ', '.join(product.get("industries", [])),
                    product.get("product", {}).get("pack_size", ""),
                    product.get("product", {}).get("price", "")
                ])
        
        return csv_path
    
    def get_default_extraction_strategy(self):
        """
        Get default extraction strategy for Agar
        """
        return AgarExtractionStrategy(self.config)
```

#### **File: `src/clients/agar/agar_strategies.py`**
```python
"""
Agar-specific extraction strategies
"""
from typing import Dict, Any
from ...strategies.product_schema_extraction import ProductSchemaExtractionStrategy

class AgarExtractionStrategy(ProductSchemaExtractionStrategy):
    """
    Agar-specific product extraction strategy
    """
    
    def __init__(self, config: Dict):
        super().__init__(config.get("llm_provider", "openai/gpt-4-mini"))
        self.config = config
        
        # Agar-specific CSS selectors
        self.agar_selectors = {
            "agar_code": ".product-code, .agar-code, .item-code",
            "pack_size": ".pack-size, .size, .volume",
            "unit_price": ".unit-price, .price-per-unit",
            "chemical_name": ".chemical-name, .active-ingredient",
            "dilution_rate": ".dilution, .mix-ratio",
            "ph_level": ".ph-level, .ph-value",
            "safety_info": ".safety-warning, .hazard-statement"
        }
    
    async def extract(self, content: str, url: str) -> Dict[str, Any]:
        """
        Extract with Agar-specific enhancements
        """
        # Get base extraction
        result = await super().extract(content, url)
        
        # Add Agar-specific fields
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        agar_data = {}
        for field, selector in self.agar_selectors.items():
            element = soup.select_one(selector)
            if element:
                agar_data[field] = element.get_text(strip=True)
        
        # Merge Agar data
        if result and "product" in result:
            result["product"].update(agar_data)
        
        # Agar-specific categorization
        if self.config.get("agar_features", {}).get("chemical_classification"):
            result["chemical_class"] = self.classify_chemical(result.get("product", {}))
        
        return result
    
    def classify_chemical(self, product: Dict) -> str:
        """
        Classify chemical products according to Agar standards
        """
        name = product.get("name", "").lower()
        desc = product.get("description", "").lower()
        
        if "quaternary" in name or "quat" in name:
            return "Quaternary Ammonium"
        elif "chlorine" in name or "bleach" in name:
            return "Chlorine-based"
        elif "peroxide" in name:
            return "Peroxide-based"
        elif "alcohol" in name or "ethanol" in name:
            return "Alcohol-based"
        elif "enzyme" in name:
            return "Enzymatic"
        else:
            return "General Purpose"

class AgarCategoryStrategy:
    """
    Agar-specific category building strategy
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.agar_categories = {
            "Disinfectants": ["disinfectant", "sanitizer", "antibacterial"],
            "Floor Care": ["floor", "polish", "stripper", "sealer"],
            "Kitchen": ["kitchen", "degreaser", "oven", "dishwash"],
            "Laundry": ["laundry", "fabric", "softener", "detergent"],
            "Washroom": ["toilet", "washroom", "bathroom", "urinal"],
            "General Purpose": ["all-purpose", "multipurpose", "general"]
        }
    
    def categorize(self, product_name: str, product_desc: str) -> List[str]:
        """
        Categorize products using Agar's category structure
        """
        categories = []
        text = f"{product_name} {product_desc}".lower()
        
        for category, keywords in self.agar_categories.items():
            if any(keyword in text for keyword in keywords):
                categories.append(category)
        
        # Default category if none found
        if not categories:
            categories.append("General Purpose")
        
        return categories
```

#### **File: `config/clients/agar.yaml`**
```yaml
# Agar Client Configuration
client_name: agar
version: "1.0"

# Agar-specific features
agar_features:
  auto_categorize: true
  chemical_classification: true
  safety_data_extraction: true
  dilution_calculator: true

# Agar product categories
agar_categories:
  "Disinfectant & Antibacterial":
    - disinfectant
    - antibacterial
    - sanitizer
    - germicide
  "Floor Care":
    - floor cleaner
    - floor polish
    - floor stripper
    - floor sealer
  "Kitchen & Food Service":
    - degreaser
    - dishwash
    - oven cleaner
    - food safe
  "Laundry":
    - laundry powder
    - fabric softener
    - laundry liquid
    - stain remover
  "Washroom & Toilet":
    - toilet cleaner
    - bathroom cleaner
    - urinal blocks
    - air freshener

# Agar-specific industries
agar_industries:
  - healthcare
  - aged-care
  - food-service
  - education
  - commercial-cleaning
  - hospitality

# Agar URL patterns
agar_url_patterns:
  - "/products/"
  - "/chemicals/"
  - "/equipment/"
  - "/msds/"
  - "/technical/"

# Agar-specific extraction
extraction_strategy: agar
llm_provider: "openai/gpt-4-mini"

# Download configuration
download_path: "./downloads/agar"
output_path: "./output/agar"

# Agar-specific fields to extract
agar_fields:
  - agar_code
  - pack_size
  - unit_price
  - dilution_rate
  - ph_level
  - active_ingredients
  - safety_classification

# Plugins to load for Agar
plugins:
  - agar_safety_parser
  - agar_dilution_calculator
  - agar_compliance_checker
```

#### **File: `config/base_config.yaml`**
```yaml
# Base Configuration - Shared across all clients
version: "1.0"

# Browser settings
browser:
  headless: true
  verbose: false
  browser_type: chromium
  timeout: 30000

# Crawling settings
crawling:
  max_pages: 100
  max_depth: 5
  max_concurrent: 5
  respect_robots_txt: true

# Rate limiting
rate_limit:
  delay: 1
  max_requests_per_second: 2
  
# Extraction settings
extraction:
  enable_javascript: true
  wait_for_network: true
  scroll_to_bottom: true
  
# Download settings
downloads:
  enabled: true
  max_file_size: 100  # MB
  timeout: 30  # seconds
  retry_attempts: 3
  
# Output settings
output:
  generate_sql: true
  generate_json: true
  generate_csv: true
  
# Logging
logging:
  level: INFO
  file: "discovery.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Extension points (hooks)
hooks:
  - pre_discovery
  - post_discovery
  - pre_extraction
  - post_extraction
  - pre_download
  - post_download
  - categorize_product
  - map_industries
```

### 3. Plugin System Implementation

#### **File: `extensions/plugin_base.py`**
```python
"""
Base plugin class for creating extensions
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class Plugin(ABC):
    """
    Base class for all plugins
    """
    
    def __init__(self, pipeline, config: Dict):
        self.pipeline = pipeline
        self.config = config
        self.setup()
    
    @abstractmethod
    def setup(self):
        """
        Setup plugin - must be implemented
        """
        pass
    
    @abstractmethod
    async def process(self, data: Any) -> Any:
        """
        Process data - must be implemented
        """
        pass
    
    def register_hooks(self):
        """
        Register plugin hooks with the pipeline
        """
        pass

def plugin(name: str, plugin_type: str = "general"):
    """
    Decorator for marking plugin classes
    """
    def decorator(cls):
        cls.__plugin__ = {
            "name": name,
            "type": plugin_type
        }
        return cls
    return decorator
```

#### **File: `extensions/example_plugin.py`**
```python
"""
Example plugin implementation
"""
from .plugin_base import Plugin, plugin

@plugin(name="example_processor", plugin_type="module")
class ExampleProcessorPlugin(Plugin):
    """
    Example plugin for processing data
    """
    
    def setup(self):
        """
        Setup the plugin
        """
        self.enabled = self.config.get("enabled", True)
        self.register_hooks()
    
    def register_hooks(self):
        """
        Register processing hooks
        """
        if self.enabled:
            self.pipeline.register_hook("post_extraction", self.process)
    
    async def process(self, data: Any) -> Any:
        """
        Process extracted data
        """
        # Add custom processing
        if "product" in data:
            data["product"]["processed_by"] = "example_plugin"
        
        return data
```

### 4. Multi-Client Usage

#### **File: `main_multi_client.py`**
```python
"""
Main execution script with multi-client support
"""
import asyncio
import argparse
import logging
from pathlib import Path
from src.core.client_registry import ClientRegistry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='Crawl4AI Product Discovery - Multi-Client')
    parser.add_argument('url', help='Website URL to discover products from')
    parser.add_argument('--client', required=True, help='Client name (e.g., agar, generic)')
    parser.add_argument('--config', help='Custom config file path')
    parser.add_argument('--list-clients', action='store_true', help='List available clients')
    parser.add_argument('--plugins', nargs='+', help='Additional plugins to load')
    
    args = parser.parse_args()
    
    # List clients if requested
    if args.list_clients:
        print("\nAvailable Clients:")
        for client in ClientRegistry.list_clients():
            print(f"  - {client}")
        return 0
    
    # Create client instance
    try:
        client = ClientRegistry.create_client(
            args.client,
            config_path=args.config
        )
        
        # Load additional plugins if specified
        if args.plugins:
            for plugin_name in args.plugins:
                client.load_plugin(plugin_name)
        
        logger.info(f"Starting discovery with {args.client} client for: {args.url}")
        
        # Run client-specific discovery
        result = await client.run(site_url=args.url)
        
        # Display results
        print(f"\n{'='*50}")
        print(f"Discovery Complete - {args.client.upper()} Client")
        print(f"{'='*50}")
        print(f"Products Found: {len(result.get('products', []))}")
        
        # Client-specific output
        if hasattr(client, 'display_results'):
            client.display_results(result)
        else:
            print(f"Results saved to: {client.config.get('output_path')}")
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
```

### 5. Creating New Clients

#### **File: `src/clients/template/template_client.py`**
```python
"""
Template for creating new client implementations
"""
from typing import Dict, Any, Optional
from ..base_client import BaseClient

class TemplateClient(BaseClient):
    """
    Template client - copy this to create new clients
    """
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__("template", config_path)  # Replace 'template' with client name
    
    def setup_pipeline(self):
        """
        Setup client-specific components
        """
        # Import and initialize required modules
        from ...strategies.product_schema_extraction import ProductSchemaExtractionStrategy
        
        # Use client-specific or default strategies
        self.extraction_strategy = self.get_extraction_strategy()
        
        # Initialize other components
        self.setup_modules()
        
        # Register client-specific hooks
        self.register_hooks()
    
    def setup_modules(self):
        """
        Setup client-specific modules
        """
        # Example: Setup custom downloader
        from ...modules.attachment_downloader import ProductAttachmentDownloader
        
        self.attachment_downloader = ProductAttachmentDownloader(
            base_download_path=f"./downloads/{self.client_name}"
        )
    
    def register_hooks(self):
        """
        Register client-specific hooks
        """
        # Example hooks
        # self.register_hook("post_extraction", self.custom_post_extraction)
        pass
    
    async def run(self, site_url: str, **kwargs) -> Dict[str, Any]:
        """
        Run client-specific pipeline
        """
        # Implement client-specific discovery logic
        # Can reuse base functionality or completely customize
        results = {
            "client": self.client_name,
            "site": site_url,
            "products": []
        }
        
        # Add discovery logic here
        
        return results
    
    def get_default_extraction_strategy(self):
        """
        Return default extraction strategy for this client
        """
        from ...strategies.product_schema_extraction import ProductSchemaExtractionStrategy
        return ProductSchemaExtractionStrategy(
            self.config.get("llm_provider", "openai/gpt-4-mini")
        )
```

### 6. Usage Examples

#### **Using Different Clients:**
```bash
# Use Agar client with Agar-specific features
python main_multi_client.py https://cleaning-supplies.com --client agar

# Use a generic client
python main_multi_client.py https://products.com --client generic

# Use custom client with custom config
python main_multi_client.py https://site.com --client custom --config config/custom_client.yaml

# List available clients
python main_multi_client.py --list-clients

# Load additional plugins
python main_multi_client.py https://site.com --client agar --plugins safety_analyzer compliance_checker
```

#### **Creating a New Client:**
```bash
# 1. Copy template directory
cp -r src/clients/template src/clients/newclient

# 2. Rename and edit the client file
mv src/clients/newclient/template_client.py src/clients/newclient/newclient_client.py

# 3. Create client configuration
cp config/clients/template.yaml config/clients/newclient.yaml

# 4. Use the new client
python main_multi_client.py https://site.com --client newclient
```

### 7. Core Implementation Files

#### **File: `src/models/schema_models.py`**
```python
"""
Database schema models matching the provided structure
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import uuid

@dataclass
class Category:
    id: str
    name: str
    description: str
    slug: str
    parent_id: Optional[str] = None
    
    @classmethod
    def create(cls, name: str, description: str = "", parent_id: Optional[str] = None):
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            slug=cls.generate_slug(name),
            parent_id=parent_id
        )
    
    @staticmethod
    def generate_slug(name: str) -> str:
        return name.lower().replace(' ', '-').replace('&', 'and')

@dataclass
class Industry:
    id: str
    name: str
    slug: str
    
    @classmethod
    def create(cls, name: str):
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            slug=cls.generate_slug(name)
        )
    
    @staticmethod
    def generate_slug(name: str) -> str:
        return name.lower().replace(' ', '-')

@dataclass
class Product:
    id: str
    name: str
    description: str
    url: str
    categories: List[str] = None
    industries: List[str] = None
    
    @classmethod
    def create(cls, name: str, description: str, url: str):
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            url=url,
            categories=[],
            industries=[]
        )

@dataclass
class Attachment:
    id: str
    product_id: str
    type: str  # PDS_PDF, MSDS_PDF, TECH_SPEC, etc.
    url: str
    local_path: str
    filename: str
    
    VALID_TYPES = [
        'PDS_PDF', 'MSDS_PDF', 'TECH_SPEC', 
        'USER_MANUAL', 'CERT_PDF', 'CAD_MODEL', 
        'PRODUCT_IMAGE', 'DEMO_VIDEO'
    ]

@dataclass
class Metadata:
    timestamp: datetime
    version: str
    site: str
    record_counts: dict
```

#### **File: `src/strategies/product_schema_extraction.py`**
```python
"""
Custom extraction strategy for products matching database schema
"""
from crawl4ai.extraction_strategy import ExtractionStrategy
from crawl4ai import LLMConfig, LLMExtractionStrategy, JsonCssExtractionStrategy
import json
from typing import Dict, Any

class ProductSchemaExtractionStrategy(ExtractionStrategy):
    """
    Extract product information matching the database schema
    """
    
    def __init__(self, llm_provider: str = "openai/gpt-4-mini"):
        self.llm_provider = llm_provider
        
        # Define extraction schema
        self.schema = {
            "type": "object",
            "properties": {
                "product": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "sku": {"type": "string"},
                        "price": {"type": "string"},
                        "specifications": {"type": "object"}
                    }
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "potential_industries": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "downloadable_resources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "url": {"type": "string"},
                            "title": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        # CSS selectors for common product page elements
        self.css_extraction = JsonCssExtractionStrategy(
            schema={
                "product_name": {"selector": "h1.product-title, h1[itemprop='name'], .product-name h1", "type": "text"},
                "description": {"selector": ".product-description, [itemprop='description'], .description", "type": "text"},
                "price": {"selector": ".price, [itemprop='price'], .product-price", "type": "text"},
                "sku": {"selector": ".sku, [itemprop='sku'], .product-code", "type": "text"},
                "images": {"selector": ".product-image img, .gallery img", "type": "attribute", "attribute": "src"},
                "downloads": {
                    "selector": "a[href*='.pdf'], a[href*='download'], .downloads a",
                    "type": "list",
                    "fields": {
                        "url": {"type": "attribute", "attribute": "href"},
                        "text": {"type": "text"}
                    }
                }
            }
        )
    
    async def extract(self, content: str, url: str) -> Dict[str, Any]:
        """
        Extract product data using both CSS and LLM strategies
        """
        # First try CSS extraction for structured data
        css_result = self.css_extraction.extract(content)
        
        # Then use LLM for intelligent extraction and categorization
        llm_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider=self.llm_provider,
                schema=self.schema,
                prompt="""
                Extract product information from this page.
                Identify:
                1. Product details (name, description, SKU, specifications)
                2. Product categories (e.g., "Cleaning Supplies > Disinfectants")
                3. Relevant industries (healthcare, education, food service, etc.)
                4. All downloadable resources with their types:
                   - PDS_PDF: Product data sheets
                   - MSDS_PDF: Safety data sheets
                   - TECH_SPEC: Technical specifications
                   - USER_MANUAL: User guides
                   - CERT_PDF: Certifications
                   - CAD_MODEL: CAD/3D files
                   - PRODUCT_IMAGE: High-res images
                """
            )
        )
        
        llm_result = await llm_strategy.extract(content)
        
        # Merge results
        return self.merge_extraction_results(css_result, llm_result, url)
    
    def merge_extraction_results(self, css_result: Dict, llm_result: Dict, url: str) -> Dict:
        """
        Intelligently merge CSS and LLM extraction results
        """
        merged = {
            "url": url,
            "product": {},
            "categories": [],
            "industries": [],
            "attachments": []
        }
        
        # Merge product details (prefer CSS for structured data, LLM for interpretation)
        if css_result:
            merged["product"].update({
                "name": css_result.get("product_name", ""),
                "description": css_result.get("description", ""),
                "sku": css_result.get("sku", ""),
                "price": css_result.get("price", "")
            })
        
        if llm_result:
            # Override with LLM if CSS extraction failed
            if not merged["product"]["name"] and llm_result.get("product"):
                merged["product"] = llm_result["product"]
            
            merged["categories"] = llm_result.get("categories", [])
            merged["industries"] = llm_result.get("potential_industries", [])
            
            # Process downloadable resources
            for resource in llm_result.get("downloadable_resources", []):
                merged["attachments"].append({
                    "type": resource["type"],
                    "url": resource["url"],
                    "filename": resource.get("title", "")
                })
        
        # Add CSS-discovered downloads
        if css_result and "downloads" in css_result:
            for download in css_result["downloads"]:
                merged["attachments"].append({
                    "type": self.detect_attachment_type(download["url"], download["text"]),
                    "url": download["url"],
                    "filename": download["text"]
                })
        
        return merged
    
    def detect_attachment_type(self, url: str, text: str) -> str:
        """
        Detect attachment type from URL and link text
        """
        url_lower = url.lower()
        text_lower = text.lower()
        
        if 'msds' in url_lower or 'sds' in url_lower or 'safety' in text_lower:
            return 'MSDS_PDF'
        elif 'datasheet' in url_lower or 'pds' in url_lower or 'product data' in text_lower:
            return 'PDS_PDF'
        elif 'manual' in url_lower or 'guide' in text_lower:
            return 'USER_MANUAL'
        elif 'spec' in url_lower or 'technical' in text_lower:
            return 'TECH_SPEC'
        elif 'cert' in url_lower or 'compliance' in text_lower:
            return 'CERT_PDF'
        elif any(ext in url_lower for ext in ['.dwg', '.dxf', '.step', '.iges']):
            return 'CAD_MODEL'
        elif any(ext in url_lower for ext in ['.jpg', '.png', '.webp']):
            return 'PRODUCT_IMAGE'
        else:
            return 'PDS_PDF'  # Default type
```

#### **File: `src/modules/attachment_downloader.py`**
```python
"""
Download and organize product attachments
"""
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from urllib.parse import urlparse, urljoin
import hashlib
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ProductAttachmentDownloader:
    """
    Download and organize product attachments according to schema
    """
    
    def __init__(self, base_download_path: str = "./downloads"):
        self.base_path = Path(base_download_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def download_product_attachments(
        self, 
        product_id: str, 
        site_slug: str,
        attachments: List[Dict],
        base_url: str
    ) -> List[Dict]:
        """
        Download all attachments for a product
        """
        downloaded = []
        
        for attachment in attachments:
            try:
                # Create directory structure
                type_dir = self.base_path / site_slug / "products" / product_id / attachment['type']
                type_dir.mkdir(parents=True, exist_ok=True)
                
                # Make URL absolute if relative
                attachment_url = urljoin(base_url, attachment['url'])
                
                # Generate filename
                if not attachment.get('filename'):
                    attachment['filename'] = self.generate_filename(attachment_url, attachment['type'])
                
                local_path = type_dir / attachment['filename']
                
                # Download file
                if not local_path.exists():
                    success = await self.download_file(attachment_url, local_path)
                    if success:
                        attachment['local_path'] = str(local_path)
                        downloaded.append(attachment)
                        logger.info(f"Downloaded: {attachment['filename']} to {local_path}")
                else:
                    attachment['local_path'] = str(local_path)
                    downloaded.append(attachment)
                    logger.info(f"File exists: {local_path}")
                    
            except Exception as e:
                logger.error(f"Failed to download {attachment.get('url')}: {e}")
                
        return downloaded
    
    async def download_file(self, url: str, path: Path, chunk_size: int = 8192) -> bool:
        """
        Download file with progress tracking
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(path, 'wb') as file:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                await file.write(chunk)
                        return True
                    else:
                        logger.error(f"HTTP {response.status} for {url}")
                        return False
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    def generate_filename(self, url: str, attachment_type: str) -> str:
        """
        Generate filename from URL
        """
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        
        if not filename or filename == '/':
            # Generate from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            extension = self.get_extension_for_type(attachment_type)
            filename = f"{attachment_type.lower()}_{url_hash}{extension}"
            
        return filename
    
    def get_extension_for_type(self, attachment_type: str) -> str:
        """
        Get file extension for attachment type
        """
        extensions = {
            'PDS_PDF': '.pdf',
            'MSDS_PDF': '.pdf',
            'TECH_SPEC': '.pdf',
            'USER_MANUAL': '.pdf',
            'CERT_PDF': '.pdf',
            'CAD_MODEL': '.zip',
            'PRODUCT_IMAGE': '.jpg',
            'DEMO_VIDEO': '.mp4'
        }
        return extensions.get(attachment_type, '.pdf')
```

#### **File: `src/modules/category_builder.py`**
```python
"""
Build hierarchical category structure from site navigation
"""
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from typing import List, Dict, Optional
import logging
from ..models.schema_models import Category

logger = logging.getLogger(__name__)

class CategoryHierarchyBuilder:
    """
    Discover and build category hierarchy from website navigation
    """
    
    def __init__(self):
        self.categories = {}
        self.category_urls = {}
        
    async def discover_categories(self, crawler: AsyncWebCrawler, site_url: str) -> List[Category]:
        """
        Discover all categories from site navigation
        """
        # Multiple strategies for finding categories
        strategies = [
            self._extract_from_navigation,
            self._extract_from_sitemap,
            self._extract_from_category_pages
        ]
        
        all_categories = []
        for strategy in strategies:
            try:
                categories = await strategy(crawler, site_url)
                all_categories.extend(categories)
            except Exception as e:
                logger.warning(f"Category extraction strategy failed: {e}")
        
        # Deduplicate and build hierarchy
        return self._build_hierarchy(all_categories)
    
    async def _extract_from_navigation(self, crawler: AsyncWebCrawler, site_url: str) -> List[Dict]:
        """
        Extract categories from navigation menu
        """
        nav_schema = {
            "main_categories": {
                "selector": "nav ul.menu > li, .main-navigation > li, .product-categories > li",
                "type": "list",
                "fields": {
                    "name": {"selector": "a", "type": "text"},
                    "url": {"selector": "a", "type": "attribute", "attribute": "href"},
                    "subcategories": {
                        "selector": "ul.submenu li, .dropdown li, ul li",
                        "type": "list",
                        "fields": {
                            "name": {"selector": "a", "type": "text"},
                            "url": {"selector": "a", "type": "attribute", "attribute": "href"}
                        }
                    }
                }
            }
        }
        
        extraction_strategy = JsonCssExtractionStrategy(schema=nav_schema)
        
        result = await crawler.arun(
            url=site_url,
            extraction_strategy=extraction_strategy
        )
        
        categories = []
        if result.extracted_content:
            for main_cat in result.extracted_content.get("main_categories", []):
                parent = Category.create(name=main_cat["name"])
                categories.append(parent)
                
                for sub_cat in main_cat.get("subcategories", []):
                    child = Category.create(
                        name=sub_cat["name"],
                        parent_id=parent.id
                    )
                    categories.append(child)
        
        return categories
    
    async def _extract_from_sitemap(self, crawler: AsyncWebCrawler, site_url: str) -> List[Dict]:
        """
        Extract categories from sitemap
        """
        sitemap_urls = [
            f"{site_url}/sitemap.xml",
            f"{site_url}/sitemap_index.xml",
            f"{site_url}/product-sitemap.xml"
        ]
        
        categories = []
        for sitemap_url in sitemap_urls:
            try:
                result = await crawler.arun(url=sitemap_url)
                # Parse XML and extract category URLs
                if "category" in result.markdown or "collection" in result.markdown:
                    # Extract category information from URLs
                    categories.extend(self._parse_category_urls(result.markdown))
            except:
                continue
                
        return categories
    
    async def _extract_from_category_pages(self, crawler: AsyncWebCrawler, site_url: str) -> List[Dict]:
        """
        Look for dedicated category or collection pages
        """
        category_urls = [
            f"{site_url}/categories",
            f"{site_url}/collections",
            f"{site_url}/products/categories",
            f"{site_url}/shop"
        ]
        
        categories = []
        for cat_url in category_urls:
            try:
                result = await crawler.arun(url=cat_url)
                # Extract category listing
                extraction_strategy = JsonCssExtractionStrategy(
                    schema={
                        "categories": {
                            "selector": ".category-item, .collection-item, .product-category",
                            "type": "list",
                            "fields": {
                                "name": {"selector": "h2, h3, .title", "type": "text"},
                                "description": {"selector": ".description, p", "type": "text"},
                                "url": {"selector": "a", "type": "attribute", "attribute": "href"}
                            }
                        }
                    }
                )
                
                cat_result = await crawler.arun(
                    url=cat_url,
                    extraction_strategy=extraction_strategy
                )
                
                if cat_result.extracted_content:
                    for cat in cat_result.extracted_content.get("categories", []):
                        categories.append(Category.create(
                            name=cat["name"],
                            description=cat.get("description", "")
                        ))
                        
            except:
                continue
                
        return categories
    
    def _build_hierarchy(self, categories: List[Category]) -> List[Category]:
        """
        Build proper hierarchy from flat category list
        """
        # Deduplicate by name
        unique_categories = {}
        for cat in categories:
            if cat.name not in unique_categories:
                unique_categories[cat.name] = cat
        
        return list(unique_categories.values())
    
    def _parse_category_urls(self, sitemap_content: str) -> List[Category]:
        """
        Parse category URLs from sitemap content
        """
        categories = []
        # Extract URLs containing /category/, /collection/, etc.
        import re
        pattern = r'<loc>(.*?/(?:category|collection|categories)/.*?)</loc>'
        matches = re.findall(pattern, sitemap_content)
        
        for url in matches:
            # Extract category name from URL
            parts = url.split('/')
            for i, part in enumerate(parts):
                if part in ['category', 'collection', 'categories'] and i + 1 < len(parts):
                    cat_name = parts[i + 1].replace('-', ' ').title()
                    categories.append(Category.create(name=cat_name))
                    
        return categories
```

#### **File: `src/modules/industry_detector.py`**
```python
"""
Detect relevant industries for products
"""
from typing import List, Dict
import re
from crawl4ai import LLMConfig, LLMExtractionStrategy
from ..models.schema_models import Industry

class IndustryDetector:
    """
    Detect and map products to relevant industries
    """
    
    INDUSTRY_DEFINITIONS = {
        'healthcare': {
            'name': 'Healthcare & Medical',
            'keywords': ['medical', 'hospital', 'clinical', 'patient', 'healthcare', 
                        'surgical', 'diagnostic', 'therapeutic', 'pharmaceutical'],
            'patterns': [r'medical\s+grade', r'hospital\s+use', r'clinical\s+setting']
        },
        'aged-care': {
            'name': 'Aged Care Facilities',
            'keywords': ['elderly', 'nursing home', 'aged care', 'senior', 'retirement',
                        'geriatric', 'assisted living', 'long-term care'],
            'patterns': [r'nursing\s+home', r'aged\s+care', r'senior\s+living']
        },
        'food-service': {
            'name': 'Food Service & Hospitality',
            'keywords': ['restaurant', 'kitchen', 'food prep', 'culinary', 'catering',
                        'hospitality', 'food service', 'dining', 'chef'],
            'patterns': [r'food\s+safe', r'NSF\s+certified', r'kitchen\s+grade']
        },
        'education': {
            'name': 'Education',
            'keywords': ['school', 'classroom', 'student', 'educational', 'university',
                        'college', 'teacher', 'learning', 'academic'],
            'patterns': [r'school\s+approved', r'classroom\s+safe', r'student\s+use']
        },
        'commercial-cleaning': {
            'name': 'Commercial Cleaning',
            'keywords': ['janitorial', 'facility', 'commercial', 'office', 'building',
                        'maintenance', 'custodial', 'professional cleaning'],
            'patterns': [r'commercial\s+grade', r'industrial\s+strength']
        },
        'industrial': {
            'name': 'Industrial & Manufacturing',
            'keywords': ['industrial', 'manufacturing', 'factory', 'warehouse', 'production',
                        'machinery', 'equipment', 'heavy duty'],
            'patterns': [r'heavy\s+duty', r'industrial\s+use', r'factory\s+approved']
        }
    }
    
    def __init__(self, llm_provider: str = None):
        self.llm_provider = llm_provider
        self.industries = [Industry.create(ind['name']) for ind in self.INDUSTRY_DEFINITIONS.values()]
    
    async def detect_industries(
        self, 
        product_name: str, 
        product_description: str,
        use_llm: bool = True
    ) -> List[str]:
        """
        Detect relevant industries for a product
        """
        detected = set()
        
        # Keyword-based detection
        text = f"{product_name} {product_description}".lower()
        
        for industry_slug, industry_def in self.INDUSTRY_DEFINITIONS.items():
            # Check keywords
            if any(keyword in text for keyword in industry_def['keywords']):
                detected.add(industry_slug)
            
            # Check patterns
            for pattern in industry_def['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    detected.add(industry_slug)
        
        # LLM-based detection for better accuracy
        if use_llm and self.llm_provider:
            llm_industries = await self._detect_with_llm(product_name, product_description)
            detected.update(llm_industries)
        
        return list(detected)
    
    async def _detect_with_llm(self, product_name: str, product_description: str) -> List[str]:
        """
        Use LLM for intelligent industry detection
        """
        industry_list = list(self.INDUSTRY_DEFINITIONS.keys())
        
        llm_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider=self.llm_provider,
                prompt=f"""
                Based on this product, identify ALL relevant industries from this list:
                {', '.join(industry_list)}
                
                Product: {product_name}
                Description: {product_description}
                
                Return ONLY the industry slugs that are relevant, as a JSON array.
                Be inclusive - if a product could be used in an industry, include it.
                Example: ["healthcare", "aged-care", "education"]
                """
            )
        )
        
        try:
            result = await llm_strategy.extract(product_description)
            if isinstance(result, list):
                return [ind for ind in result if ind in self.INDUSTRY_DEFINITIONS]
        except:
            pass
            
        return []
    
    def get_industry_by_slug(self, slug: str) -> Industry:
        """
        Get industry object by slug
        """
        for industry in self.industries:
            if industry.slug == slug:
                return industry
        return None
```

#### **File: `src/pipeline/product_discovery_pipeline.py`**
```python
"""
Main pipeline orchestrating product discovery, extraction, and download
"""
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import logging
from datetime import datetime
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import AdaptiveCrawlerConfig
from crawl4ai.async_crawler_strategy import AdaptiveCrawler
from crawl4ai.discovery import AsyncUrlSeeder

from ..strategies.product_schema_extraction import ProductSchemaExtractionStrategy
from ..modules.attachment_downloader import ProductAttachmentDownloader
from ..modules.category_builder import CategoryHierarchyBuilder
from ..modules.industry_detector import IndustryDetector
from ..models.schema_models import Product, Category, Industry, Attachment, Metadata
from ..utils.database_generator import DatabaseGenerator
from ..utils.file_organizer import FileOrganizer

logger = logging.getLogger(__name__)

class ProductDiscoveryPipeline:
    """
    Complete pipeline for discovering, extracting, and downloading product data
    """
    
    def __init__(self, config_path: str = "config/crawler_config.yaml"):
        self.config = self.load_config(config_path)
        self.setup_components()
        
    def setup_components(self):
        """
        Initialize all pipeline components
        """
        # Core crawler
        self.browser_config = BrowserConfig(
            headless=self.config.get("headless", True),
            verbose=self.config.get("verbose", False),
            browser_type=self.config.get("browser_type", "chromium")
        )
        
        # Modules
        self.extraction_strategy = ProductSchemaExtractionStrategy(
            llm_provider=self.config.get("llm_provider", "openai/gpt-4-mini")
        )
        self.attachment_downloader = ProductAttachmentDownloader(
            base_download_path=self.config.get("download_path", "./downloads")
        )
        self.category_builder = CategoryHierarchyBuilder()
        self.industry_detector = IndustryDetector(
            llm_provider=self.config.get("llm_provider")
        )
        self.db_generator = DatabaseGenerator()
        self.file_organizer = FileOrganizer()
        
        # Data storage
        self.products = []
        self.categories = []
        self.industries = []
        self.attachments = []
        
    def load_config(self, config_path: str) -> Dict:
        """
        Load configuration from YAML file
        """
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except:
            # Default configuration
            return {
                "headless": True,
                "verbose": False,
                "max_pages": 100,
                "max_depth": 5,
                "download_path": "./downloads",
                "output_path": "./output",
                "llm_provider": "openai/gpt-4-mini",
                "rate_limit": {
                    "delay": 1,
                    "max_concurrent": 5
                }
            }
    
    async def discover_site(self, site_url: str) -> Dict[str, Any]:
        """
        Main entry point for site discovery
        """
        logger.info(f"Starting discovery for: {site_url}")
        
        # Parse site info
        parsed_url = urlparse(site_url)
        site_slug = parsed_url.netloc.replace('.', '-')
        
        async with AsyncWebCrawler(browser_config=self.browser_config) as crawler:
            
            # Step 1: Discover site structure and categories
            logger.info("Building category hierarchy...")
            self.categories = await self.category_builder.discover_categories(crawler, site_url)
            logger.info(f"Found {len(self.categories)} categories")
            
            # Step 2: Discover product URLs
            logger.info("Discovering product URLs...")
            product_urls = await self.discover_product_urls(crawler, site_url)
            logger.info(f"Found {len(product_urls)} potential product pages")
            
            # Step 3: Extract product data and download attachments
            logger.info("Extracting product data...")
            for i, url in enumerate(product_urls[:self.config.get("max_pages", 100)]):
                try:
                    logger.info(f"Processing product {i+1}/{len(product_urls)}: {url}")
                    
                    # Extract product data
                    product_data = await self.extract_product(crawler, url)
                    
                    if product_data and product_data.get("product", {}).get("name"):
                        # Create product object
                        product = Product.create(
                            name=product_data["product"]["name"],
                            description=product_data["product"].get("description", ""),
                            url=url
                        )
                        
                        # Map categories
                        product.categories = product_data.get("categories", [])
                        
                        # Detect industries
                        industries = await self.industry_detector.detect_industries(
                            product.name,
                            product.description
                        )
                        product.industries = industries
                        
                        # Download attachments
                        if product_data.get("attachments"):
                            downloaded = await self.attachment_downloader.download_product_attachments(
                                product_id=product.id,
                                site_slug=site_slug,
                                attachments=product_data["attachments"],
                                base_url=site_url
                            )
                            
                            # Create attachment records
                            for att in downloaded:
                                attachment = Attachment(
                                    id=str(uuid.uuid4()),
                                    product_id=product.id,
                                    type=att["type"],
                                    url=att["url"],
                                    local_path=att["local_path"],
                                    filename=att["filename"]
                                )
                                self.attachments.append(attachment)
                        
                        self.products.append(product)
                        
                        # Rate limiting
                        await asyncio.sleep(self.config["rate_limit"]["delay"])
                        
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    continue
            
            # Step 4: Generate outputs
            logger.info("Generating outputs...")
            output_data = await self.generate_outputs(site_slug)
            
            return output_data
    
    async def discover_product_urls(self, crawler: AsyncWebCrawler, site_url: str) -> List[str]:
        """
        Discover all product URLs on the site
        """
        urls = set()
        
        # Method 1: Use URL seeder with sitemap
        try:
            seeder = AsyncUrlSeeder(
                crawler=crawler,
                config={
                    "seed_urls": [site_url],
                    "check_liveness": True
                }
            )
            
            discovered_urls = await seeder.discover_urls(site_url)
            
            # Filter for product URLs
            product_patterns = [
                '/product/', '/products/', '/item/', '/p/',
                '/catalog/', '/shop/', '/store/'
            ]
            
            for url in discovered_urls:
                if any(pattern in url.lower() for pattern in product_patterns):
                    urls.add(url)
                    
        except Exception as e:
            logger.warning(f"URL seeder failed: {e}")
        
        # Method 2: Use adaptive crawler
        if len(urls) < 10:  # Fallback if sitemap didn't work
            try:
                adaptive_config = AdaptiveCrawlerConfig(
                    query="product pages with prices and specifications",
                    max_pages=self.config.get("max_pages", 100)
                )
                
                adaptive_crawler = AdaptiveCrawler(
                    crawler=crawler,
                    config=adaptive_config
                )
                
                crawl_state = await adaptive_crawler.crawl(
                    start_url=site_url,
                    max_depth=self.config.get("max_depth", 5)
                )
                
                urls.update(crawl_state.visited_urls)
                
            except Exception as e:
                logger.warning(f"Adaptive crawler failed: {e}")
        
        # Method 3: Deep crawl with BFS
        if len(urls) < 10:
            from crawl4ai.async_crawler_strategy import BFSCrawler
            
            bfs_crawler = BFSCrawler(
                crawler=crawler,
                max_depth=3
            )
            
            result = await bfs_crawler.crawl(site_url)
            urls.update(result.discovered_urls)
        
        return list(urls)
    
    async def extract_product(self, crawler: AsyncWebCrawler, url: str) -> Dict:
        """
        Extract product data from a URL
        """
        try:
            # Configure extraction
            run_config = CrawlerRunConfig(
                url=url,
                extraction_strategy=self.extraction_strategy,
                wait_for="networkidle",
                js_code="""
                // Scroll to load lazy content
                window.scrollTo(0, document.body.scrollHeight);
                
                // Click on tabs to reveal hidden content
                const tabs = document.querySelectorAll('[role="tab"], .tab-button, .accordion-header');
                tabs.forEach(tab => tab.click());
                
                // Return all downloadable links
                const downloads = Array.from(document.querySelectorAll('a[href]'))
                    .filter(a => {
                        const href = a.href.toLowerCase();
                        return href.includes('.pdf') || 
                               href.includes('.zip') ||
                               href.includes('download');
                    })
                    .map(a => ({
                        url: a.href,
                        text: a.textContent.trim()
                    }));
                    
                return downloads;
                """
            )
            
            result = await crawler.arun(**run_config)
            
            # Combine extraction results with JS-discovered downloads
            extracted = result.extracted_content
            
            if result.js_result:
                if not extracted.get("attachments"):
                    extracted["attachments"] = []
                    
                for download in result.js_result:
                    extracted["attachments"].append({
                        "type": self.extraction_strategy.detect_attachment_type(
                            download["url"], 
                            download["text"]
                        ),
                        "url": download["url"],
                        "filename": download["text"]
                    })
            
            return extracted
            
        except Exception as e:
            logger.error(f"Extraction failed for {url}: {e}")
            return None
    
    async def generate_outputs(self, site_slug: str) -> Dict:
        """
        Generate all output files
        """
        output_dir = Path(self.config.get("output_path", "./output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate metadata
        metadata = Metadata(
            timestamp=datetime.now(),
            version="1.0",
            site=site_slug,
            record_counts={
                "products": len(self.products),
                "categories": len(self.categories),
                "industries": len(set(ind for p in self.products for ind in p.industries)),
                "attachments": len(self.attachments)
            }
        )
        
        # Generate SQL
        sql_file = output_dir / f"{site_slug}_import.sql"
        self.db_generator.generate_sql(
            products=self.products,
            categories=self.categories,
            industries=self.get_unique_industries(),
            attachments=self.attachments,
            output_path=sql_file
        )
        
        # Generate JSON export
        json_file = output_dir / f"{site_slug}_products.json"
        self.export_to_json(json_file)
        
        # Generate CSV report
        csv_file = output_dir / f"{site_slug}_summary.csv"
        self.generate_csv_report(csv_file)
        
        # Return summary
        return {
            "site": site_slug,
            "products_discovered": len(self.products),
            "categories_found": len(self.categories),
            "industries_mapped": len(self.get_unique_industries()),
            "attachments_downloaded": len(self.attachments),
            "outputs": {
                "sql": str(sql_file),
                "json": str(json_file),
                "csv": str(csv_file),
                "downloads": str(self.attachment_downloader.base_path / site_slug)
            }
        }
    
    def get_unique_industries(self) -> List[Industry]:
        """
        Get unique industries from all products
        """
        industry_slugs = set()
        for product in self.products:
            industry_slugs.update(product.industries)
        
        industries = []
        for slug in industry_slugs:
            industry = self.industry_detector.get_industry_by_slug(slug)
            if industry:
                industries.append(industry)
        
        return industries
    
    def export_to_json(self, output_path: Path):
        """
        Export all data to JSON
        """
        export_data = {
            "products": [vars(p) for p in self.products],
            "categories": [vars(c) for c in self.categories],
            "industries": [vars(i) for i in self.get_unique_industries()],
            "attachments": [vars(a) for a in self.attachments]
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def generate_csv_report(self, output_path: Path):
        """
        Generate CSV summary report
        """
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Product Name', 'SKU', 'Categories', 'Industries', 'Attachments', 'URL'])
            
            for product in self.products:
                attachments = [a for a in self.attachments if a.product_id == product.id]
                writer.writerow([
                    product.name,
                    getattr(product, 'sku', ''),
                    ', '.join(product.categories),
                    ', '.join(product.industries),
                    len(attachments),
                    product.url
                ])
```

#### **File: `src/utils/database_generator.py`**
```python
"""
Generate SQL statements for database import
"""
from typing import List
from pathlib import Path
from ..models.schema_models import Product, Category, Industry, Attachment

class DatabaseGenerator:
    """
    Generate SQL insert statements matching the schema
    """
    
    def generate_sql(
        self,
        products: List[Product],
        categories: List[Category],
        industries: List[Industry],
        attachments: List[Attachment],
        output_path: Path
    ):
        """
        Generate complete SQL script
        """
        with open(output_path, 'w') as f:
            # Header
            f.write("-- Product Discovery Import\n")
            f.write("-- Generated by Crawl4AI Product Discovery\n\n")
            
            # Categories
            f.write("-- Categories\n")
            for cat in categories:
                f.write(
                    f"INSERT INTO categories (id, name, description, slug, parent_id) "
                    f"VALUES ('{cat.id}', '{self.escape(cat.name)}', "
                    f"'{self.escape(cat.description)}', '{cat.slug}', "
                    f"{'NULL' if not cat.parent_id else f\"'{cat.parent_id}'\"});\n"
                )
            
            f.write("\n-- Industries\n")
            for ind in industries:
                f.write(
                    f"INSERT INTO industries (id, name, slug) "
                    f"VALUES ('{ind.id}', '{self.escape(ind.name)}', '{ind.slug}');\n"
                )
            
            f.write("\n-- Products\n")
            for prod in products:
                f.write(
                    f"INSERT INTO products (id, name, description, url) "
                    f"VALUES ('{prod.id}', '{self.escape(prod.name)}', "
                    f"'{self.escape(prod.description)}', '{prod.url}');\n"
                )
            
            f.write("\n-- Product-Category Relations\n")
            for prod in products:
                for cat_name in prod.categories:
                    cat = next((c for c in categories if c.name == cat_name), None)
                    if cat:
                        f.write(
                            f"INSERT INTO product_categories (product_id, category_id) "
                            f"VALUES ('{prod.id}', '{cat.id}');\n"
                        )
            
            f.write("\n-- Product-Industry Relations\n")
            for prod in products:
                for ind_slug in prod.industries:
                    ind = next((i for i in industries if i.slug == ind_slug), None)
                    if ind:
                        f.write(
                            f"INSERT INTO product_industries (product_id, industry_id) "
                            f"VALUES ('{prod.id}', '{ind.id}');\n"
                        )
            
            f.write("\n-- Attachments\n")
            for att in attachments:
                f.write(
                    f"INSERT INTO attachments (id, product_id, type, url, local_path, filename) "
                    f"VALUES ('{att.id}', '{att.product_id}', '{att.type}', "
                    f"'{att.url}', '{att.local_path}', '{self.escape(att.filename)}');\n"
                )
    
    def escape(self, text: str) -> str:
        """
        Escape SQL special characters
        """
        if not text:
            return ""
        return text.replace("'", "''").replace("\n", " ").replace("\r", "")
```

### 3. Configuration Files

#### **File: `config/crawler_config.yaml`** (Now inherits from base_config.yaml)
```yaml
# Crawl4AI Product Discovery Configuration

# Browser settings
headless: true
verbose: false
browser_type: chromium  # chromium, firefox, webkit

# LLM settings
llm_provider: "openai/gpt-4-mini"  # or anthropic/claude-3, ollama/llama2, etc.

# Crawling limits
max_pages: 100
max_depth: 5
max_concurrent: 5

# Paths
download_path: "./downloads"
output_path: "./output"
cache_path: "./cache"

# Rate limiting
rate_limit:
  delay: 1  # seconds between requests
  max_concurrent: 5
  respect_robots_txt: true

# Discovery settings
discovery:
  use_sitemap: true
  use_adaptive_crawling: true
  use_url_seeding: true
  
# Extraction settings
extraction:
  enable_javascript: true
  wait_for_network: true
  scroll_to_bottom: true
  click_tabs: true
  
# Download settings
downloads:
  enabled: true
  types:
    - PDS_PDF
    - MSDS_PDF
    - TECH_SPEC
    - USER_MANUAL
    - CERT_PDF
    - PRODUCT_IMAGE
  max_file_size: 100  # MB
  timeout: 30  # seconds
  
# Industry detection
industries:
  use_llm: true
  use_keywords: true
  confidence_threshold: 0.7
```

### 4. Main Execution Script

#### **File: `main.py`**
```python
"""
Main execution script for product discovery
"""
import asyncio
import argparse
import logging
from pathlib import Path
from src.pipeline.product_discovery_pipeline import ProductDiscoveryPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('product_discovery.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='Crawl4AI Product Discovery Tool')
    parser.add_argument('url', help='Website URL to discover products from')
    parser.add_argument('--config', default='config/crawler_config.yaml', help='Config file path')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to crawl')
    parser.add_argument('--output', default='./output', help='Output directory')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = ProductDiscoveryPipeline(config_path=args.config)
    
    # Override config if needed
    if args.max_pages:
        pipeline.config['max_pages'] = args.max_pages
    if args.output:
        pipeline.config['output_path'] = args.output
    
    # Run discovery
    logger.info(f"Starting product discovery for: {args.url}")
    
    try:
        result = await pipeline.discover_site(args.url)
        
        # Print summary
        print("\n" + "="*50)
        print("DISCOVERY COMPLETE")
        print("="*50)
        print(f"Site: {result['site']}")
        print(f"Products Found: {result['products_discovered']}")
        print(f"Categories: {result['categories_found']}")
        print(f"Industries: {result['industries_mapped']}")
        print(f"Attachments Downloaded: {result['attachments_downloaded']}")
        print("\nOutput Files:")
        for key, path in result['outputs'].items():
            print(f"  {key}: {path}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
```

### 5. Testing Script

#### **File: `tests/test_extraction.py`**
```python
"""
Test product extraction on sample pages
"""
import asyncio
from crawl4ai import AsyncWebCrawler
from src.strategies.product_schema_extraction import ProductSchemaExtractionStrategy

async def test_extraction():
    # Test URLs
    test_urls = [
        "https://www.example-cleaning-supplies.com/product/disinfectant",
        "https://www.example-medical.com/products/equipment"
    ]
    
    strategy = ProductSchemaExtractionStrategy()
    
    async with AsyncWebCrawler() as crawler:
        for url in test_urls:
            print(f"\nTesting: {url}")
            result = await crawler.arun(
                url=url,
                extraction_strategy=strategy
            )
            
            if result.extracted_content:
                print(f"Product: {result.extracted_content.get('product', {}).get('name')}")
                print(f"Categories: {result.extracted_content.get('categories', [])}")
                print(f"Attachments: {len(result.extracted_content.get('attachments', []))}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
```

### 6. Requirements File

#### **File: `requirements.txt`**
```
crawl4ai>=0.4.0
aiohttp>=3.8.0
aiofiles>=23.0.0
pyyaml>=6.0
lxml>=4.9.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
```

---

## Usage Instructions for Cline

### Initial Setup:
1. Create the project structure as specified
2. Install Crawl4AI and dependencies: `pip install -r requirements.txt`
3. Configure your LLM provider API keys if using AI features
4. Adjust `config/crawler_config.yaml` for your needs

### Running the Tool:
```bash
# Basic usage
python main.py https://example-products.com

# With custom config
python main.py https://example-products.com --config my_config.yaml --max-pages 50

# Test extraction first
python tests/test_extraction.py
```

### Expected Outputs:
- SQL file with INSERT statements for all tables
- JSON export of all discovered data
- CSV summary report
- Downloaded files organized in `/downloads/{site}/{product_id}/{type}/`
- Detailed logs in `product_discovery.log`

### Key Features Implemented:
• **Smart Product Discovery**: Multiple strategies to find all products
• **Schema Compliance**: All data maps to provided database structure  
• **Intelligent Categorization**: Hierarchical categories with parent-child relationships
• **Industry Detection**: AI and keyword-based industry mapping
• **Comprehensive Downloads**: All attachment types with organized storage
• **Flexible Configuration**: YAML-based settings for easy adjustment
• **Production Ready**: Logging, error handling, rate limiting
• **Extensible Design**: Easy to add new extraction strategies or attachment types
• **Multi-Client Architecture**: Support for multiple clients with shared core functionality
• **Plugin System**: Dynamic loading of extensions and customizations
• **Client Registry**: Automatic discovery and management of client implementations
• **Configuration Inheritance**: Base config with client-specific overrides
• **Hook System**: Extension points throughout the pipeline for customization
• **Reusable Components**: Share strategies and modules across clients
• **Client Isolation**: Each client has its own download paths and outputs

## Extension Mechanism Benefits:

### 1. **Client Separation**
- Each client (Agar, etc.) has its own directory and configuration
- No interference between different client implementations
- Easy to add new clients without modifying core code

### 2. **Configuration Management**
- Base configuration provides defaults
- Client-specific configs override only what's needed
- Runtime configuration can further customize behavior

### 3. **Plugin Architecture**
- Plugins can be shared across clients
- Client-specific plugins for unique functionality
- Dynamic discovery and loading of plugins

### 4. **Hook System**
- Extension points throughout the processing pipeline
- Clients can register custom processing at any stage
- Non-invasive customization without modifying core

### 5. **Strategy Pattern**
- Extraction strategies can be swapped per client
- Fallback to default strategies if client-specific not found
- Easy to test different approaches

### 6. **Reusability**
- Core modules (downloaders, categorizers) shared across clients
- Client-specific implementations when needed
- Minimize code duplication

This implementation allows you to:
- Use the Agar functionality you've built
- Apply it to other clients by creating new client directories
- Share common functionality through the base classes
- Customize per-client through configuration and plugins
- Maintain clean separation between different client needs