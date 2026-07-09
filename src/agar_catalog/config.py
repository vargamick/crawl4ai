"""Load a client config (YAML). A client = a config file, not new code."""
from __future__ import annotations
import pathlib
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class ClientConfig:
    client: str
    base_url: str
    source: str = "store_api"
    store_api_path: str = "/wp-json/wc/store/v1/products"
    per_page: int = 100
    documents_enabled: bool = True
    document_patterns: list[str] = field(default_factory=list)
    output_dir: str = "output"
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | pathlib.Path) -> "ClientConfig":
        data = yaml.safe_load(pathlib.Path(path).read_text()) or {}
        api = data.get("store_api", {}) or {}
        docs = data.get("documents", {}) or {}
        out = data.get("output", {}) or {}
        return cls(
            client=data["client"],
            base_url=data["base_url"],
            source=data.get("source", "store_api"),
            store_api_path=api.get("path", "/wp-json/wc/store/v1/products"),
            per_page=int(api.get("per_page", 100)),
            documents_enabled=bool(docs.get("enabled", True)),
            document_patterns=list(docs.get("link_patterns", []) or []),
            output_dir=out.get("dir", "output"),
            raw=data,
        )
