"""
Base pipeline class for extensible client implementations.

This module provides the abstract base class that all client implementations
must inherit from, providing common functionality like configuration management,
hook system, and plugin loading.
"""

import asyncio
import importlib
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable


class BasePipeline(ABC):
    """
    Abstract base class for all pipeline implementations.
    
    This class provides the foundation for extensible client implementations
    with configuration management, hook system, and plugin architecture.
    """
    
    def __init__(self, client_name: str, config_path: Optional[str] = None):
        """
        Initialize the BasePipeline with configuration.
        
        Args:
            client_name: Name of the client implementation
            config_path: Optional path to custom configuration file
        """
        self.client_name = client_name
        self.config = self.load_config(config_path)
        self.plugins = {}
        self.hooks = {}
        self.setup_pipeline()
    
    def load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        Load configuration with client-specific overrides.
        
        Args:
            config_path: Optional path to custom configuration file
            
        Returns:
            Merged configuration dictionary
        """
        # Load base configuration
        base_config_path = Path("config/base_config.yaml")
        if base_config_path.exists():
            with open(base_config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = self._get_default_config()
        
        # Load client-specific configuration
        client_config_path = Path(f"config/clients/{self.client_name}.yaml")
        if client_config_path.exists():
            with open(client_config_path, 'r') as f:
                client_config = yaml.safe_load(f) or {}
                config = self.merge_configs(config, client_config)
        
        # Load custom config if provided
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                custom_config = yaml.safe_load(f) or {}
                config = self.merge_configs(config, custom_config)
        
        return config
    
    def _get_default_config(self) -> Dict:
        """
        Get default configuration if no config files exist.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "version": "1.0",
            "browser": {
                "headless": True,
                "verbose": False,
                "browser_type": "chromium",
                "timeout": 30000
            },
            "crawling": {
                "max_pages": 100,
                "max_depth": 5,
                "max_concurrent": 5,
                "respect_robots_txt": True
            },
            "rate_limit": {
                "delay": 1,
                "max_requests_per_second": 2
            },
            "extraction": {
                "enable_javascript": True,
                "wait_for_network": True,
                "scroll_to_bottom": True
            },
            "downloads": {
                "enabled": True,
                "max_file_size": 100,  # MB
                "timeout": 30,  # seconds
                "retry_attempts": 3
            },
            "output": {
                "generate_sql": True,
                "generate_json": True,
                "generate_csv": True
            },
            "logging": {
                "level": "INFO",
                "file": "discovery.log",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    def merge_configs(self, base: Dict, override: Dict) -> Dict:
        """
        Deep merge configuration dictionaries.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
            
        Returns:
            Merged configuration dictionary
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
        Setup pipeline components - must be implemented by client.
        
        This method should initialize all client-specific components,
        strategies, and modules required for the pipeline.
        """
        pass
    
    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the pipeline - must be implemented by client.
        
        Args:
            **kwargs: Pipeline-specific arguments
            
        Returns:
            Results dictionary with pipeline output
        """
        pass
    
    def register_hook(self, hook_name: str, callback: Callable):
        """
        Register a hook for extension points.
        
        Args:
            hook_name: Name of the hook/extension point
            callback: Callback function to execute
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
    
    async def run_hooks(self, hook_name: str, data: Any) -> Any:
        """
        Run all registered hooks for a given extension point.
        
        Args:
            hook_name: Name of the hook to execute
            data: Data to pass through the hooks
            
        Returns:
            Data after processing through all hooks
        """
        if hook_name in self.hooks:
            for hook in self.hooks[hook_name]:
                if asyncio.iscoroutinefunction(hook):
                    data = await hook(data)
                else:
                    data = hook(data)
        return data
    
    def load_plugin(self, plugin_name: str, plugin_config: Dict = None):
        """
        Dynamically load a plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            plugin_config: Configuration for the plugin
            
        Returns:
            Loaded plugin instance
            
        Raises:
            ImportError: If plugin cannot be loaded
        """
        try:
            # Try loading from extensions directory first
            module = importlib.import_module(f"extensions.{plugin_name}")
            plugin_class = getattr(module, f"{plugin_name.title()}Plugin")
            self.plugins[plugin_name] = plugin_class(self, plugin_config or {})
            return self.plugins[plugin_name]
        except (ImportError, AttributeError):
            try:
                # Try loading from client-specific plugins
                module = importlib.import_module(f"src.clients.{self.client_name}.plugins.{plugin_name}")
                plugin_class = getattr(module, f"{plugin_name.title()}Plugin")
                self.plugins[plugin_name] = plugin_class(self, plugin_config or {})
                return self.plugins[plugin_name]
            except (ImportError, AttributeError) as e:
                raise ImportError(f"Failed to load plugin {plugin_name}: {e}")
    
    def get_plugin(self, plugin_name: str):
        """
        Get a loaded plugin instance.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None if not loaded
        """
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """
        List all loaded plugins.
        
        Returns:
            List of loaded plugin names
        """
        return list(self.plugins.keys())
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration value (e.g., 'browser.headless')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config_value(self, key_path: str, value: Any):
        """
        Set a configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration value
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_output_path(self, filename: str = "") -> Path:
        """
        Get output path for files.
        
        Args:
            filename: Optional filename to append
            
        Returns:
            Path object for output location
        """
        output_dir = Path(self.get_config_value("output.path", "./output"))
        client_dir = output_dir / self.client_name
        client_dir.mkdir(parents=True, exist_ok=True)
        
        if filename:
            return client_dir / filename
        return client_dir
    
    def get_download_path(self, *path_parts) -> Path:
        """
        Get download path for files.
        
        Args:
            *path_parts: Path components to append
            
        Returns:
            Path object for download location
        """
        download_dir = Path(self.get_config_value("downloads.path", "./downloads"))
        client_dir = download_dir / self.client_name
        
        if path_parts:
            full_path = client_dir.joinpath(*path_parts)
        else:
            full_path = client_dir
            
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
    
    async def log_info(self, message: str):
        """
        Log an info message.
        
        Args:
            message: Message to log
        """
        # Basic logging - can be enhanced with proper logger
        if self.get_config_value("logging.level") in ["INFO", "DEBUG"]:
            print(f"[{self.client_name.upper()}] INFO: {message}")
    
    async def log_error(self, message: str):
        """
        Log an error message.
        
        Args:
            message: Error message to log
        """
        print(f"[{self.client_name.upper()}] ERROR: {message}")
    
    async def log_debug(self, message: str):
        """
        Log a debug message.
        
        Args:
            message: Debug message to log
        """
        if self.get_config_value("logging.level") == "DEBUG":
            print(f"[{self.client_name.upper()}] DEBUG: {message}")
