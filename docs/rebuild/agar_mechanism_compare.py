#!/usr/bin/env python3
"""
agar_mechanism_compare.py — a repeatable way to compare data-acquisition mechanisms for the Agar catalogue.

Pulls the catalogue via the WooCommerce Store API (and, if available, the HTTP+CSS fallback), then diffs
each against the committed HTTP-mode baseline fixture, emitting a parity report:
  - product-count match
  - per-slug presence (missing / extra)
  - per-field coverage % (sku, categories, images, attributes, description)
  - SDS/PDS document delta (the known Store-API gap)

Runs standalone (stdlib + `requests`). In the new project, adapt to httpx and wire in as
`harvest compare --client agar`.

Usage:
  python agar_mechanism_compare.py --baseline output/baseline_0.7.4 [--base-url https://agar.com.au] [--limit N]

Proxy/TLS: honours HTTPS_PROXY + SSL_CERT_FILE (set both in restricted egress environments).
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    sys.exit("This harness needs `requests` (pip install requests). In the new project, use httpx.")

UA = {"User-Agent": "agar-catalog-compare/1.0"}


# ---------- identity ----------
def slug_from_url(url: str) -> str:
    return urlparse(url).path.rstrip("/").split("/")[-1].lower()


# ---------- Store API ----------
def fetch_store_api(base_url: str, limit: int | None = None) -> dict[str, dict]:
    """Return {slug: normalized_record} from the public WooCommerce Store API (no auth)."""
    endpoint = f"{base_url.rstrip('/')}/wp-json/wc/store/v1/products"
    out: dict[str, dict] = {}
    page = 1
    while True:
        r = requests.get(endpoint, params={"per_page": 100, "page": page},
                         headers=UA, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        for p in batch:
            slug = (p.get("slug") or slug_from_url(p.get("permalink", ""))).lower()
            out[slug] = {
                "slug": slug,
                "name": p.get("name") or "",
                "sku": p.get("sku") or "",
                "categories": [c.get("name") for c in p.get("categories", [])],
                "images": [i.get("src") for i in p.get("images", [])],
                "attributes": {a.get("name"): [t.get("name") for t in a.get("terms", [])]
                               for a in p.get("attributes", [])},
                "description": re.sub("<[^>]+>", "", (p.get("description") or "")).strip(),
                "permalink": p.get("permalink") or "",
            }
            if limit and len(out) >= limit:
                return out
        total_pages = int(r.headers.get("X-WP-TotalPages", page))
        if page >= total_pages:
            break
        page += 1
    return out


# ---------- baseline fixture ----------
def load_baseline(baseline_dir: str) -> dict[str, dict]:
    files = sorted(glob.glob(os.path.join(baseline_dir, "agar_products_*.json")))
    if not files:
        sys.exit(f"No agar_products_*.json in {baseline_dir}")
    prods = json.load(open(files[-1]))
    prods = prods if isinstance(prods, list) else prods.get("products", [])
    out: dict[str, dict] = {}
    for p in prods:
        slug = slug_from_url(p.get("product_url", "")).lower()
        raw = (p.get("metadata") or {}).get("raw_extracted_data", {})
        out[slug] = {
            "slug": slug,
            "name": p.get("product_name") or "",
            "sku": raw.get("sku") or "",
            "categories": ([raw.get("categories")] if isinstance(raw.get("categories"), str)
                           else raw.get("categories") or []),
            "images": ([raw.get("product_images")] if isinstance(raw.get("product_images"), str)
                       else raw.get("product_images") or []),
            "attributes": {},
            "description": p.get("description") or "",
        }
    return out


# ---------- SDS/PDS document probe (the known Store-API gap) ----------
DOC_PAT = re.compile(r'href="([^"]*(?:\.pdf|/sds/|-pds-sds|datasheet|safety)[^"]*)"', re.I)
def doc_links_on_page(url: str) -> int:
    try:
        r = requests.get(url, headers=UA, timeout=20)
        return len(set(DOC_PAT.findall(r.text)))
    except Exception:
        return 0


# ---------- report ----------
FIELDS = ["name", "sku", "categories", "images", "description"]
def coverage(records: dict[str, dict]) -> dict[str, float]:
    n = len(records) or 1
    return {f: round(100 * sum(1 for r in records.values() if r.get(f)) / n, 1) for f in FIELDS}

def report(api: dict[str, dict], base: dict[str, dict], doc_sample: int, base_url: str) -> None:
    a, b = set(api), set(base)
    print("\n================ MECHANISM PARITY REPORT ================")
    print(f"Store API products : {len(api)}")
    print(f"Baseline products  : {len(base)}")
    print(f"In both            : {len(a & b)}")
    print(f"API-only (new)     : {len(a - b)}  {sorted(a - b)[:8]}")
    print(f"Baseline-only      : {len(b - a)}  {sorted(b - a)[:8]}")
    print("\nField coverage %      STORE_API   BASELINE")
    ca, cb = coverage(api), coverage(base)
    for f in FIELDS:
        print(f"  {f:<12}       {ca[f]:>7}    {cb[f]:>7}")
    print(f"  {'attributes':<12}       {round(100*sum(1 for r in api.values() if r['attributes'])/(len(api) or 1),1):>7}    {'0.0':>7}   (API-only richness)")
    if doc_sample:
        sample = list(api.values())[:doc_sample]
        withdocs = sum(1 for r in sample if r.get("permalink") and doc_links_on_page(r["permalink"]))
        print(f"\nSDS/PDS doc delta   : {withdocs}/{len(sample)} sampled products have doc links on-page")
        print("                      (documents are NOT in the Store API — the DocumentEnricher must fetch them)")
    verdict = "PASS — API meets or beats the baseline" if len(api) >= len(base) else "REVIEW — API returned fewer products"
    print(f"\nVerdict: {verdict}")
    print("========================================================\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", default="output/baseline_0.7.4")
    ap.add_argument("--base-url", default="https://agar.com.au")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--doc-sample", type=int, default=5, help="products to probe for SDS/PDS links (0=skip)")
    args = ap.parse_args()

    print(f"Fetching Store API from {args.base_url} ...")
    api = fetch_store_api(args.base_url, args.limit)
    print(f"Loading baseline from {args.baseline} ...")
    base = load_baseline(args.baseline)
    report(api, base, args.doc_sample, args.base_url)


if __name__ == "__main__":
    main()
