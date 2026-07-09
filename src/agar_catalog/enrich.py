"""
DocumentEnricher — closes the one gap the Store API leaves: SDS / PDS documents.

Those aren't in the Store API; they're links on each product page (e.g. /sds/, /{slug}-pds-sds,
*.pdf). For each product we do one light HTTP GET of its page, extract candidate document links, and
hand them to the ported DocumentHandler, which classifies them into DocumentSchema records.
"""
from __future__ import annotations
import re
from typing import List

import httpx

from .model import ProductSchema, DocumentSchema, ScrapingConfig
from .documents import DocumentHandler

# href + anchor text for links that look like documents
_LINK = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
_TAGS = re.compile(r"<[^>]+>")
DEFAULT_PATTERNS = [r"\.pdf(\?|$)", r"/sds/?", r"-pds-sds", r"datasheet", r"safety"]


class DocumentEnricher:
    def __init__(self, base_url: str, patterns: list[str] | None = None,
                 output_dir: str = "output", timeout: float = 20.0):
        self._pats = [re.compile(p, re.I) for p in (patterns or DEFAULT_PATTERNS)]
        self._handler = DocumentHandler(ScrapingConfig(base_url=base_url, output_dir=output_dir))
        self.timeout = timeout

    def _extract_links(self, htmltext: str) -> tuple[list[str], list[str]]:
        links, texts = [], []
        seen = set()
        for href, label in _LINK.findall(htmltext):
            if any(p.search(href) for p in self._pats) and href not in seen:
                seen.add(href)
                links.append(href)
                texts.append(_TAGS.sub(" ", label).strip())
        return links, texts

    def enrich(self, products: List[ProductSchema]) -> List[DocumentSchema]:
        docs: List[DocumentSchema] = []
        with httpx.Client(trust_env=True, timeout=self.timeout,
                          headers={"User-Agent": "agar-catalog/1.0"}, follow_redirects=True) as client:
            for product in products:
                try:
                    r = client.get(str(product.product_url))
                    if r.status_code != 200:
                        continue
                    links, texts = self._extract_links(r.text)
                    if not links:
                        continue
                    docs.extend(self._handler.extract_documents_from_product(
                        product, {"attachment_links": links, "attachment_texts": texts}))
                except httpx.HTTPError:
                    continue
        return docs
