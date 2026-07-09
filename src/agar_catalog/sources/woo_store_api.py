"""
WooCommerceStoreAPISource — the PRIMARY Agar catalogue source.

Reads the public WooCommerce Store API (`/wp-json/wc/store/v1/products`) — no auth — and builds the
shared AgarCatalogData: products (with sku / price / attributes), media (full image gallery), categories
(all of them) and product-category relationships. Documents are added later by the DocumentEnricher.
"""
from __future__ import annotations
import html
import re
from typing import Optional

import httpx

from ..model import (
    AgarCatalogData, ProductSchema, MediaSchema, MediaType, MediaFormat,
    CategorySchema, ProductCategoryRelation,
)
from ..util import (
    generate_product_id, generate_media_id, generate_category_id,
    detect_media_format, clean_text, create_slug,
)

_TAGS = re.compile(r"<[^>]+>")
_VALID_FORMATS = {f.value for f in MediaFormat}


def _strip(s: str | None) -> str:
    return clean_text(html.unescape(_TAGS.sub(" ", s or ""))) if s else ""


class WooCommerceStoreAPISource:
    name = "store_api"

    def __init__(self, base_url: str, path: str = "/wp-json/wc/store/v1/products",
                 per_page: int = 100, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.endpoint = f"{self.base_url}{path}"
        self.per_page = per_page
        self.timeout = timeout

    def _pages(self):
        # trust_env=True → honour HTTPS_PROXY; SSL_CERT_FILE is read by the default SSL context.
        with httpx.Client(trust_env=True, timeout=self.timeout,
                          headers={"User-Agent": "agar-catalog/1.0"}) as client:
            page = 1
            while True:
                r = client.get(self.endpoint, params={"per_page": self.per_page, "page": page})
                r.raise_for_status()
                batch = r.json()
                if not batch:
                    return
                yield from batch
                total_pages = int(r.headers.get("X-WP-TotalPages", page))
                if page >= total_pages:
                    return
                page += 1

    def harvest(self, limit: Optional[int] = None) -> AgarCatalogData:
        products: list[ProductSchema] = []
        media: list[MediaSchema] = []
        categories: dict[str, CategorySchema] = {}       # dedup by category_id
        relations: list[ProductCategoryRelation] = []

        for i, p in enumerate(self._pages()):
            if limit and len(products) >= limit:
                break
            permalink = p.get("permalink") or f"{self.base_url}/product/{p.get('slug','')}/"
            pid = generate_product_id(permalink)

            attributes = {
                a.get("name"): [html.unescape(t.get("name", "")) for t in a.get("terms", [])]
                for a in p.get("attributes", []) if a.get("name")
            }
            description = _strip(p.get("description")) or _strip(p.get("short_description"))

            # categories (all of them) + relationships
            cat_ids: list[str] = []
            for j, c in enumerate(p.get("categories", [])):
                cname = html.unescape(c.get("name", "")).strip()
                if not cname:
                    continue
                cid = generate_category_id(cname)
                cat_ids.append(cid)
                categories.setdefault(cid, CategorySchema(
                    category_id=cid, category_name=cname, slug=create_slug(cname), level=0))
                relations.append(ProductCategoryRelation(
                    product_id=pid, category_id=cid, primary=(j == 0)))

            products.append(ProductSchema(
                product_id=pid,
                product_name=_strip(p.get("name")) or p.get("slug", ""),
                product_url=permalink,
                description=description or None,
                category_ids=cat_ids,
                sku=(p.get("sku") or None),
                price=(_strip(p.get("price_html")) or None),
                attributes=attributes,
                metadata={"source": self.name, "wc_id": p.get("id")},
            ))

            # media — full gallery
            for seq, img in enumerate(p.get("images", []), start=1):
                src = img.get("src")
                if not src:
                    continue
                fmt = (detect_media_format(src) or "jpg")
                if fmt not in _VALID_FORMATS:
                    fmt = "jpg"
                media.append(MediaSchema(
                    media_id=generate_media_id(pid, src, seq),
                    product_id=pid, media_type=MediaType.IMAGE, media_format=fmt,
                    media_url=src, sequence_order=seq, alt_text=(img.get("alt") or None),
                ))

        return AgarCatalogData(
            products=products, media=media, documents=[],
            categories=list(categories.values()), product_categories=relations,
            metadata={"source": self.name, "base_url": self.base_url},
        )
