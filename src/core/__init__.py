"""
Core framework components for Crawl4AI Product Discovery System.

This package contains the base classes and core functionality that powers
the extensible multi-client product discovery framework.
"""

from .base_pipeline import BasePipeline
from .plugin_manager import PluginManager
from .client_registry import ClientRegistry

__all__ = [
    'BasePipeline',
    'PluginManager', 
    'ClientRegistry'
]
