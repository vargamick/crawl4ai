"""
Pipeline: source → (document enrichment) → normalized 3DN files + markdown.

Reuses the ported JSONNormalizer + MarkdownGenerator unchanged, so the SAME 8-file output contract the
old scraper produced is recreated here — just fed from the API instead of a browser crawl.
"""
from __future__ import annotations
from typing import Optional

from .config import ClientConfig
from .model import AgarCatalogData
from .sources import SOURCES
from .enrich import DocumentEnricher
from .normalizer import JSONNormalizer
from .markdown import MarkdownGenerator


def build_source(cfg: ClientConfig, source: Optional[str] = None):
    name = source or cfg.source
    if name not in SOURCES:
        raise SystemExit(f"unknown source '{name}'. available: {', '.join(SOURCES)}")
    if name == "store_api":
        return SOURCES[name](cfg.base_url, cfg.store_api_path, cfg.per_page)
    return SOURCES[name](cfg.base_url)


def harvest(cfg: ClientConfig, source: Optional[str] = None, limit: Optional[int] = None,
            include_documents: bool = True, output_dir: Optional[str] = None,
            write: bool = True) -> tuple[AgarCatalogData, dict]:
    src = build_source(cfg, source)
    catalog = src.harvest(limit=limit)

    if include_documents and cfg.documents_enabled:
        enricher = DocumentEnricher(cfg.base_url, cfg.document_patterns or None,
                                    output_dir=output_dir or cfg.output_dir)
        catalog.documents = enricher.enrich(catalog.products)

    saved: dict = {}
    if write:
        out = output_dir or cfg.output_dir
        norm = JSONNormalizer(out)
        prefix = f"{cfg.client}_"
        saved.update(norm.save_normalized_files(catalog, filename_prefix=prefix))
        saved["legacy"] = norm.save_legacy_format(catalog, filename_prefix=prefix)
        saved["summary"] = norm.save_summary_report(catalog, filename_prefix=prefix)
        md = MarkdownGenerator(out).generate_all_markdown(catalog.products)
        saved["markdown_files"] = len(md)
    return catalog, saved
