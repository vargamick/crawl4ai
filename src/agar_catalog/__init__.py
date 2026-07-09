"""agar-catalog — API-first product-catalogue harvester."""
__version__ = "0.1.0"

from .config import ClientConfig
from .pipeline import harvest

__all__ = ["ClientConfig", "harvest", "__version__"]
