"""
Plugin manager for dynamic extension loading.

This module provides comprehensive plugin management capabilities including
automatic discovery, registration, and lifecycle management of plugins
across the product discovery framework.
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, List, Type, Optional, Callable
from abc import ABC, abstractmethod


class PluginManager:
    """
    Manages dynamic loading and registration of plugins.
    
    Provides capabilities for plugin discovery, registration, instantiation,
    and lifecycle management across the product discovery system.
    """
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.plugins = {}
        self.strategies = {}
        self.modules = {}
        self.hooks = {}
        self.plugin_instances = {}
    
    def discover_plugins(self, plugin_dir: str = "extensions") -> int:
        """
        Automatically discover and register plugins from a directory.
        
        Args:
            plugin_dir: Directory to search for plugins
            
        Returns:
            Number of plugins discovered
        """
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            return 0
        
        discovered_count = 0
        
        for plugin_file in plugin_path.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
                
            module_name = f"{plugin_dir}.{plugin_file.stem}"
            try:
                module = importlib.import_module(module_name)
                
                # Look for plugin classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        hasattr(obj, "__plugin__") and 
                        obj.__plugin__ is not None):
                        
                        plugin_info = obj.__plugin__
                        self.register_plugin(
                            plugin_info["name"],
                            obj,
                            plugin_info.get("type", "general"),
                            plugin_info.get("version", "1.0"),
                            plugin_info.get("description", ""),
                            plugin_info.get("dependencies", [])
                        )
                        discovered_count += 1
                        
            except Exception as e:
                print(f"Warning: Failed to load plugin from {plugin_file}: {e}")
                continue
        
        return discovered_count
    
    def register_plugin(
        self, 
        name: str, 
        plugin_class: Type, 
        plugin_type: str = "general",
        version: str = "1.0",
        description: str = "",
        dependencies: List[str] = None
    ):
        """
        Register a plugin class.
        
        Args:
            name: Unique name for the plugin
            plugin_class: Plugin class to register
            plugin_type: Type of plugin (general, strategy, module, hook)
            version: Plugin version
            description: Plugin description
            dependencies: List of required dependencies
        """
        plugin_info = {
            "class": plugin_class,
            "type": plugin_type,
            "version": version,
            "description": description,
            "dependencies": dependencies or [],
            "registered_at": self._get_timestamp()
        }
        
        if plugin_type == "strategy":
            self.strategies[name] = plugin_info
        elif plugin_type == "module":
            self.modules[name] = plugin_info
        elif plugin_type == "hook":
            self.hooks[name] = plugin_info
        else:
            self.plugins[name] = plugin_info
    
    def get_plugin(self, name: str, plugin_type: str = "general") -> Optional[Type]:
        """
        Get a registered plugin class.
        
        Args:
            name: Name of the plugin
            plugin_type: Type of plugin to search for
            
        Returns:
            Plugin class or None if not found
        """
        plugin_store = self._get_plugin_store(plugin_type)
        plugin_info = plugin_store.get(name)
        return plugin_info["class"] if plugin_info else None
    
    def get_plugin_info(self, name: str, plugin_type: str = "general") -> Optional[Dict[str, Any]]:
        """
        Get plugin information.
        
        Args:
            name: Name of the plugin
            plugin_type: Type of plugin to search for
            
        Returns:
            Plugin information dictionary or None
        """
        plugin_store = self._get_plugin_store(plugin_type)
        return plugin_store.get(name)
    
    def create_plugin_instance(
        self, 
        name: str, 
        plugin_type: str = "general", 
        pipeline=None, 
        config: Dict[str, Any] = None
    ) -> Optional[Any]:
        """
        Create an instance of a registered plugin.
        
        Args:
            name: Name of the plugin
            plugin_type: Type of plugin
            pipeline: Pipeline instance to pass to plugin
            config: Configuration for the plugin
            
        Returns:
            Plugin instance or None if creation failed
        """
        plugin_class = self.get_plugin(name, plugin_type)
        if not plugin_class:
            return None
        
        try:
            # Check if plugin requires pipeline parameter
            init_signature = inspect.signature(plugin_class.__init__)
            params = list(init_signature.parameters.keys())
            
            if "pipeline" in params:
                instance = plugin_class(pipeline, config or {})
            elif len(params) > 1:  # Has parameters other than 'self'
                instance = plugin_class(config or {})
            else:
                instance = plugin_class()
            
            # Store instance for reuse if needed
            instance_key = f"{plugin_type}:{name}"
            self.plugin_instances[instance_key] = instance
            
            return instance
            
        except Exception as e:
            print(f"Error creating plugin instance {name}: {e}")
            return None
    
    def get_plugin_instance(self, name: str, plugin_type: str = "general") -> Optional[Any]:
        """
        Get an existing plugin instance.
        
        Args:
            name: Name of the plugin
            plugin_type: Type of plugin
            
        Returns:
            Plugin instance or None if not found
        """
        instance_key = f"{plugin_type}:{name}"
        return self.plugin_instances.get(instance_key)
    
    def list_plugins(self, plugin_type: str = None) -> Dict[str, List[str]]:
        """
        List all registered plugins.
        
        Args:
            plugin_type: Optional type filter
            
        Returns:
            Dictionary mapping plugin types to lists of plugin names
        """
        if plugin_type:
            plugin_store = self._get_plugin_store(plugin_type)
            return {plugin_type: list(plugin_store.keys())}
        
        return {
            "general": list(self.plugins.keys()),
            "strategies": list(self.strategies.keys()),
            "modules": list(self.modules.keys()),
            "hooks": list(self.hooks.keys())
        }
    
    def check_dependencies(self, plugin_name: str, plugin_type: str = "general") -> Dict[str, bool]:
        """
        Check if plugin dependencies are available.
        
        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin
            
        Returns:
            Dictionary mapping dependency names to availability status
        """
        plugin_info = self.get_plugin_info(plugin_name, plugin_type)
        if not plugin_info:
            return {}
        
        dependencies = plugin_info.get("dependencies", [])
        dependency_status = {}
        
        for dep in dependencies:
            try:
                importlib.import_module(dep)
                dependency_status[dep] = True
            except ImportError:
                dependency_status[dep] = False
        
        return dependency_status
    
    def get_plugins_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Get plugins that provide a specific capability.
        
        Args:
            capability: Capability name to search for
            
        Returns:
            List of plugin information dictionaries
        """
        matching_plugins = []
        
        all_plugins = {**self.plugins, **self.strategies, **self.modules, **self.hooks}
        
        for name, plugin_info in all_plugins.items():
            plugin_class = plugin_info["class"]
            
            # Check if plugin has the capability
            if hasattr(plugin_class, "capabilities"):
                if capability in plugin_class.capabilities:
                    matching_plugins.append({
                        "name": name,
                        "type": plugin_info["type"],
                        "class": plugin_class,
                        **plugin_info
                    })
            
            # Check for capability methods
            if hasattr(plugin_class, f"supports_{capability}"):
                matching_plugins.append({
                    "name": name,
                    "type": plugin_info["type"],
                    "class": plugin_class,
                    **plugin_info
                })
        
        return matching_plugins
    
    def unregister_plugin(self, name: str, plugin_type: str = "general") -> bool:
        """
        Unregister a plugin.
        
        Args:
            name: Name of the plugin
            plugin_type: Type of plugin
            
        Returns:
            True if successfully unregistered, False otherwise
        """
        plugin_store = self._get_plugin_store(plugin_type)
        
        if name in plugin_store:
            del plugin_store[name]
            
            # Remove instance if exists
            instance_key = f"{plugin_type}:{name}"
            if instance_key in self.plugin_instances:
                del self.plugin_instances[instance_key]
            
            return True
        
        return False
    
    def reload_plugin(self, name: str, plugin_type: str = "general") -> bool:
        """
        Reload a plugin (useful for development).
        
        Args:
            name: Name of the plugin
            plugin_type: Type of plugin
            
        Returns:
            True if successfully reloaded, False otherwise
        """
        plugin_info = self.get_plugin_info(name, plugin_type)
        if not plugin_info:
            return False
        
        try:
            # Get module name from plugin class
            plugin_class = plugin_info["class"]
            module_name = plugin_class.__module__
            
            # Reload the module
            module = importlib.import_module(module_name)
            importlib.reload(module)
            
            # Re-register the plugin
            new_class = getattr(module, plugin_class.__name__)
            
            self.unregister_plugin(name, plugin_type)
            self.register_plugin(
                name=name,
                plugin_class=new_class,
                plugin_type=plugin_type,
                version=plugin_info.get("version", "1.0"),
                description=plugin_info.get("description", ""),
                dependencies=plugin_info.get("dependencies", [])
            )
            
            return True
            
        except Exception as e:
            print(f"Error reloading plugin {name}: {e}")
            return False
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about registered plugins.
        
        Returns:
            Dictionary with plugin statistics
        """
        total_plugins = (
            len(self.plugins) + 
            len(self.strategies) + 
            len(self.modules) + 
            len(self.hooks)
        )
        
        return {
            "total_plugins": total_plugins,
            "by_type": {
                "general": len(self.plugins),
                "strategies": len(self.strategies),
                "modules": len(self.modules),
                "hooks": len(self.hooks)
            },
            "instances_created": len(self.plugin_instances),
            "plugins_with_dependencies": sum(
                1 for plugin_info in {**self.plugins, **self.strategies, **self.modules, **self.hooks}.values()
                if plugin_info.get("dependencies")
            )
        }
    
    def _get_plugin_store(self, plugin_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get the appropriate plugin storage based on type.
        
        Args:
            plugin_type: Type of plugin
            
        Returns:
            Plugin storage dictionary
        """
        if plugin_type == "strategy":
            return self.strategies
        elif plugin_type == "module":
            return self.modules
        elif plugin_type == "hook":
            return self.hooks
        else:
            return self.plugins
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp as string.
        
        Returns:
            ISO format timestamp string
        """
        from datetime import datetime
        return datetime.now().isoformat()


class PluginBase(ABC):
    """
    Base class for all plugins.
    
    All plugin implementations should inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self, pipeline=None, config: Dict[str, Any] = None):
        """
        Initialize the plugin.
        
        Args:
            pipeline: Pipeline instance
            config: Plugin configuration
        """
        self.pipeline = pipeline
        self.config = config or {}
        self.setup()
    
    @abstractmethod
    def setup(self):
        """
        Setup plugin - must be implemented by subclasses.
        
        This method is called during plugin initialization and should
        contain any setup logic required by the plugin.
        """
        pass
    
    @abstractmethod
    async def process(self, data: Any) -> Any:
        """
        Process data - must be implemented by subclasses.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
        """
        pass
    
    def register_hooks(self):
        """
        Register plugin hooks with the pipeline.
        
        Override this method to register hooks with the pipeline
        for integration at various extension points.
        """
        pass
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)


def plugin(name: str, plugin_type: str = "general", version: str = "1.0", 
          description: str = "", dependencies: List[str] = None):
    """
    Decorator for marking plugin classes.
    
    Args:
        name: Plugin name
        plugin_type: Type of plugin (general, strategy, module, hook)
        version: Plugin version
        description: Plugin description
        dependencies: List of required dependencies
        
    Returns:
        Decorated class with plugin metadata
    """
    def decorator(cls):
        cls.__plugin__ = {
            "name": name,
            "type": plugin_type,
            "version": version,
            "description": description,
            "dependencies": dependencies or []
        }
        return cls
    return decorator
