"""
Registry for client-specific implementations.

This module provides a centralized registry for managing multiple client
implementations, including automatic discovery, registration, and instantiation
of client classes across the product discovery framework.
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, Type, Optional, List, Any
from abc import ABC


class ClientRegistry:
    """
    Registry for managing multiple client implementations.
    
    Provides a centralized system for registering, discovering, and instantiating
    client implementations with automatic loading capabilities.
    """
    
    _instance = None
    _clients = {}
    _client_metadata = {}
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_client(
        cls, 
        name: str, 
        client_class: Type, 
        description: str = "",
        version: str = "1.0",
        capabilities: List[str] = None
    ):
        """
        Register a client implementation.
        
        Args:
            name: Unique client name
            client_class: Client class to register
            description: Client description
            version: Client version
            capabilities: List of client capabilities
        """
        cls._clients[name] = client_class
        cls._client_metadata[name] = {
            "class": client_class,
            "description": description,
            "version": version,
            "capabilities": capabilities or [],
            "module": client_class.__module__,
            "registered_at": cls._get_timestamp()
        }
    
    @classmethod
    def get_client(cls, name: str) -> Optional[Type]:
        """
        Get a registered client class.
        
        Args:
            name: Client name
            
        Returns:
            Client class or None if not found
        """
        if name not in cls._clients:
            # Try to auto-load from clients directory
            if cls._auto_load_client(name):
                return cls._clients.get(name)
            return None
        
        return cls._clients.get(name)
    
    @classmethod
    def get_client_info(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Get client metadata information.
        
        Args:
            name: Client name
            
        Returns:
            Client metadata dictionary or None
        """
        if name not in cls._client_metadata and name not in cls._clients:
            cls._auto_load_client(name)
        
        return cls._client_metadata.get(name)
    
    @classmethod
    def _auto_load_client(cls, name: str) -> bool:
        """
        Attempt to automatically load a client from the clients directory.
        
        Args:
            name: Client name to load
            
        Returns:
            True if successfully loaded, False otherwise
        """
        client_patterns = [
            f"src.clients.{name}.{name}_client",
            f"src.clients.{name}.client",
            f"src.clients.{name}.main"
        ]
        
        class_patterns = [
            f"{name.title()}Client",
            f"{name.upper()}Client",
            f"{name.capitalize()}Client",
            "Client"
        ]
        
        for module_pattern in client_patterns:
            try:
                module = importlib.import_module(module_pattern)
                
                # Try different class name patterns
                for class_pattern in class_patterns:
                    if hasattr(module, class_pattern):
                        client_class = getattr(module, class_pattern)
                        
                        # Verify it's a valid client class
                        if cls._is_valid_client_class(client_class):
                            # Extract metadata if available
                            description = getattr(client_class, '__description__', f"{name.title()} client")
                            version = getattr(client_class, '__version__', "1.0")
                            capabilities = getattr(client_class, '__capabilities__', [])
                            
                            cls.register_client(
                                name=name,
                                client_class=client_class,
                                description=description,
                                version=version,
                                capabilities=capabilities
                            )
                            return True
                        
            except (ImportError, AttributeError) as e:
                continue
        
        return False
    
    @classmethod
    def _is_valid_client_class(cls, client_class: Type) -> bool:
        """
        Check if a class is a valid client implementation.
        
        Args:
            client_class: Class to validate
            
        Returns:
            True if valid client class, False otherwise
        """
        try:
            # Check if it's a class
            if not inspect.isclass(client_class):
                return False
            
            # Check for required methods (basic duck typing)
            required_methods = ['setup_pipeline', 'run']
            for method in required_methods:
                if not hasattr(client_class, method):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def discover_clients(cls, clients_dir: str = "src/clients") -> int:
        """
        Automatically discover clients from the clients directory.
        
        Args:
            clients_dir: Directory to search for clients
            
        Returns:
            Number of clients discovered
        """
        clients_path = Path(clients_dir)
        if not clients_path.exists():
            return 0
        
        discovered_count = 0
        
        for client_dir in clients_path.iterdir():
            if client_dir.is_dir() and not client_dir.name.startswith("_"):
                client_name = client_dir.name
                
                if client_name not in cls._clients:
                    if cls._auto_load_client(client_name):
                        discovered_count += 1
        
        return discovered_count
    
    @classmethod
    def list_clients(cls) -> List[str]:
        """
        List all registered clients.
        
        Returns:
            List of client names
        """
        # Auto-discover clients from directory first
        cls.discover_clients()
        
        return list(cls._clients.keys())
    
    @classmethod
    def create_client(cls, name: str, config_path: Optional[str] = None, **kwargs):
        """
        Create a client instance.
        
        Args:
            name: Client name
            config_path: Optional configuration file path
            **kwargs: Additional arguments to pass to client constructor
            
        Returns:
            Client instance
            
        Raises:
            ValueError: If client not found in registry
        """
        client_class = cls.get_client(name)
        if client_class:
            try:
                # Check constructor signature
                init_signature = inspect.signature(client_class.__init__)
                params = list(init_signature.parameters.keys())
                
                # Build constructor arguments
                constructor_args = {}
                
                if "config_path" in params:
                    constructor_args["config_path"] = config_path
                
                if "client_name" in params:
                    constructor_args["client_name"] = name
                
                # Add any additional kwargs that match constructor parameters
                for param in params:
                    if param in kwargs and param not in constructor_args:
                        constructor_args[param] = kwargs[param]
                
                return client_class(**constructor_args)
                
            except Exception as e:
                raise ValueError(f"Failed to create client '{name}': {e}")
        else:
            raise ValueError(f"Client '{name}' not found in registry")
    
    @classmethod
    def unregister_client(cls, name: str) -> bool:
        """
        Unregister a client.
        
        Args:
            name: Client name
            
        Returns:
            True if successfully unregistered, False otherwise
        """
        if name in cls._clients:
            del cls._clients[name]
            if name in cls._client_metadata:
                del cls._client_metadata[name]
            return True
        return False
    
    @classmethod
    def get_clients_by_capability(cls, capability: str) -> List[str]:
        """
        Get clients that support a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of client names that support the capability
        """
        cls.discover_clients()  # Ensure all clients are discovered
        
        matching_clients = []
        for name, metadata in cls._client_metadata.items():
            if capability in metadata.get("capabilities", []):
                matching_clients.append(name)
        
        return matching_clients
    
    @classmethod
    def get_registry_statistics(cls) -> Dict[str, Any]:
        """
        Get statistics about the client registry.
        
        Returns:
            Dictionary with registry statistics
        """
        cls.discover_clients()  # Ensure all clients are discovered
        
        capabilities_count = {}
        for metadata in cls._client_metadata.values():
            for capability in metadata.get("capabilities", []):
                capabilities_count[capability] = capabilities_count.get(capability, 0) + 1
        
        return {
            "total_clients": len(cls._clients),
            "clients": list(cls._clients.keys()),
            "capabilities": capabilities_count,
            "clients_with_metadata": len(cls._client_metadata)
        }
    
    @classmethod
    def validate_client_requirements(cls, name: str) -> Dict[str, Any]:
        """
        Validate that a client meets all requirements.
        
        Args:
            name: Client name
            
        Returns:
            Validation results dictionary
        """
        client_class = cls.get_client(name)
        if not client_class:
            return {
                "valid": False,
                "errors": [f"Client '{name}' not found"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # Check for required methods
        required_methods = ['setup_pipeline', 'run']
        for method in required_methods:
            if not hasattr(client_class, method):
                errors.append(f"Missing required method: {method}")
            elif not callable(getattr(client_class, method)):
                errors.append(f"'{method}' is not callable")
        
        # Check for recommended methods
        recommended_methods = ['get_default_extraction_strategy']
        for method in recommended_methods:
            if not hasattr(client_class, method):
                warnings.append(f"Missing recommended method: {method}")
        
        # Check constructor
        try:
            init_signature = inspect.signature(client_class.__init__)
            params = list(init_signature.parameters.keys())
            
            if "client_name" not in params and len(params) < 2:
                warnings.append("Constructor should accept client_name or config_path parameter")
                
        except Exception as e:
            warnings.append(f"Could not inspect constructor: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @classmethod
    def reload_client(cls, name: str) -> bool:
        """
        Reload a client implementation (useful for development).
        
        Args:
            name: Client name
            
        Returns:
            True if successfully reloaded, False otherwise
        """
        if name not in cls._clients:
            return False
        
        try:
            # Get current client info
            client_class = cls._clients[name]
            metadata = cls._client_metadata.get(name, {})
            module_name = metadata.get("module")
            
            if not module_name:
                module_name = client_class.__module__
            
            # Reload the module
            module = importlib.import_module(module_name)
            importlib.reload(module)
            
            # Re-register the client
            new_class = getattr(module, client_class.__name__)
            
            cls.unregister_client(name)
            cls.register_client(
                name=name,
                client_class=new_class,
                description=metadata.get("description", ""),
                version=metadata.get("version", "1.0"),
                capabilities=metadata.get("capabilities", [])
            )
            
            return True
            
        except Exception as e:
            print(f"Error reloading client {name}: {e}")
            return False
    
    @classmethod
    def _get_timestamp(cls) -> str:
        """
        Get current timestamp as string.
        
        Returns:
            ISO format timestamp string
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    @classmethod
    def clear_registry(cls):
        """Clear all registered clients (useful for testing)."""
        cls._clients.clear()
        cls._client_metadata.clear()


# Decorator for marking client classes
def client(name: str, description: str = "", version: str = "1.0", capabilities: List[str] = None):
    """
    Decorator for marking client classes for automatic registration.
    
    Args:
        name: Client name
        description: Client description  
        version: Client version
        capabilities: List of client capabilities
        
    Returns:
        Decorated class with client metadata
    """
    def decorator(cls):
        cls.__client_name__ = name
        cls.__description__ = description
        cls.__version__ = version
        cls.__capabilities__ = capabilities or []
        
        # Auto-register the client
        ClientRegistry.register_client(
            name=name,
            client_class=cls,
            description=description,
            version=version,
            capabilities=capabilities
        )
        
        return cls
    return decorator
