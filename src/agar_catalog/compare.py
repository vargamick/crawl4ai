"""
Reconcile a fresh harvest against a knowledge store and highlight conflicting values.

conflict   = same product, same field, both non-empty but different
enrichment = harvest has a value the knowledge store lacks (e.g. sku, attributes)
regression = knowledge store had a value the harvest lost
"""
from __future__ import annotations
import glob
import html
import json
import os
import re
from urllib.parse import urlparse

from .model import AgarCatalogData

_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
SCALAR = ["name", "sku", "description"]
SETS = ["categories", "images"]


def _norm(s):
    return _WS.sub(" ", html.unescape(_TAGS.sub(" ", s or ""))).strip()


def _slug(url: str) -> str:
    return urlparse(str(url)).path.rstrip("/").split("/")[-1].lower()


def catalog_records(cat: AgarCatalogData) -> dict[str, dict]:
    cat_name = {c.category_id: c.category_name for c in cat.categories}
    imgs: dict[str, list[str]] = {}
    for m in cat.media:
        imgs.setdefault(m.product_id, []).append(str(m.media_url))
    out = {}
    for p in cat.products:
        out[_slug(p.product_url)] = {
            "name": _norm(p.product_name),
            "sku": (p.sku or "").strip(),
            "categories": sorted({cat_name.get(cid, cid) for cid in p.category_ids}),
            "images": sorted(set(imgs.get(p.product_id, []))),
            "description": _norm(p.description),
            "attributes": p.attributes,
        }
    return out


def knowledge_records(path: str) -> dict[str, dict]:
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*products_*.json")))
        prods = json.load(open(files[-1])) if files else []
    else:
        prods = json.load(open(path))
    prods = prods if isinstance(prods, list) else prods.get("products", [])
    out = {}
    for p in prods:
        raw = (p.get("metadata") or {}).get("raw_extracted_data", {})
        cats = raw.get("categories")
        imgs = raw.get("product_images")
        out[_slug(p.get("product_url", ""))] = {
            "name": _norm(p.get("product_name")),
            "sku": (p.get("sku") or raw.get("sku") or "").strip(),
            "categories": sorted(set([cats] if isinstance(cats, str) else (cats or []))),
            "images": sorted(set([imgs] if isinstance(imgs, str) else (imgs or []))),
            "description": _norm(p.get("description")),
            "attributes": {},
        }
    return out


def reconcile(harvest: dict, ks: dict) -> dict:
    h, k = set(harvest), set(ks)
    field_conflicts = {f: 0 for f in SCALAR + SETS}
    products, conflict_products = {}, 0
    for slug in sorted(h & k):
        findings = []
        for f in SCALAR:
            hv, kv = harvest[slug].get(f, ""), ks[slug].get(f, "")
            if hv and kv and hv != kv:
                findings.append((f, "CONFLICT", hv, kv)); field_conflicts[f] += 1
            elif hv and not kv:
                findings.append((f, "enrichment", hv, ""))
        for f in SETS:
            hs, kset = set(harvest[slug].get(f, [])), set(ks[slug].get(f, []))
            if hs and kset and hs != kset:
                findings.append((f, "CONFLICT", sorted(hs), sorted(kset))); field_conflicts[f] += 1
            elif hs and not kset:
                findings.append((f, "enrichment", sorted(hs), []))
        if findings:
            products[slug] = findings
        if any(x[1] == "CONFLICT" for x in findings):
            conflict_products += 1
    return {
        "counts": {"harvest": len(h), "knowledge": len(k), "both": len(h & k),
                   "harvest_only": sorted(h - k), "knowledge_only": sorted(k - h)},
        "conflict_products": conflict_products,
        "field_conflicts": field_conflicts,
        "products": products,
    }


def print_report(rep: dict) -> None:
    c = rep["counts"]
    print(f"\nharvest {c['harvest']} · knowledge {c['knowledge']} · in both {c['both']}")
    if c["harvest_only"]:
        print(f"  only in harvest: {c['harvest_only'][:8]}")
    if c["knowledge_only"]:
        print(f"  only in knowledge: {c['knowledge_only'][:8]}")
    print(f"products with conflicts: {rep['conflict_products']}")
    print("field conflicts:", {k: v for k, v in rep["field_conflicts"].items() if v})
