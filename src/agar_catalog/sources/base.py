"""Source protocol. Every source yields the same normalized ProductSchema objects."""
from __future__ import annotations
from typing import Protocol, Optional
from ..model import AgarCatalogData


class CatalogSource(Protocol):
    """A data-acquisition mechanism for a product catalogue.

    Implementations build the shared AgarCatalogData (products + media + categories +
    relationships). Documents are added afterwards by the DocumentEnricher, since not
    every source (e.g. the Store API) carries them.
    """
    name: str

    def harvest(self, limit: Optional[int] = None) -> AgarCatalogData:
        ...
