#!/usr/bin/env python3
"""
reconcile.py — evaluation: match a fresh Agar harvest against the current knowledge store and
HIGHLIGHT CONFLICTING VALUES.

A *conflict* = the same product (by slug) has a **non-empty but different** value for the same field in
the two sources. This is distinct from *enrichment* (one source has a value, the other is empty — e.g. the
Store API adds `sku`/`attributes` the old scrape never had) and *presence* gaps (product in one source only).

Sources
  - "harvest"         : the live WooCommerce Store API  (authoritative-ish, structured, no auth)
  - "knowledge store" : the current canonical Agar data. Defaults to the committed baseline
                        (output/baseline_0.7.4); point --knowledge-store at your real canonical JSON.

Outputs: console summary, a JSON report, and an HTML highlight (conflicts colour-coded).

Usage:
  python reconcile.py --knowledge-store output/baseline_0.7.4 [--base-url https://agar.com.au] \
                      --out docs/rebuild/eval/out
Proxy/TLS: honours HTTPS_PROXY + SSL_CERT_FILE.
"""
from __future__ import annotations
import argparse, glob, html, json, os, re, sys
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    sys.exit("needs `requests` (pip install requests)")

UA = {"User-Agent": "agar-catalog-eval/1.0"}
_WS = re.compile(r"\s+")
_TAGS = re.compile(r"<[^>]+>")


def norm_text(s: str | None) -> str:
    # unescape HTML entities so '&amp;' vs '&' isn't reported as a false value conflict
    return _WS.sub(" ", html.unescape(_TAGS.sub(" ", s or ""))).strip()

def slug_of(url: str) -> str:
    return urlparse(url).path.rstrip("/").split("/")[-1].lower()

def as_list(v) -> list[str]:
    if v is None:
        return []
    return [v] if isinstance(v, str) else list(v)


# ---------------- harvest: Store API ----------------
def harvest_store_api(base_url: str) -> dict[str, dict]:
    endpoint = f"{base_url.rstrip('/')}/wp-json/wc/store/v1/products"
    out, page = {}, 1
    while True:
        r = requests.get(endpoint, params={"per_page": 100, "page": page}, headers=UA, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        for p in batch:
            slug = (p.get("slug") or slug_of(p.get("permalink", ""))).lower()
            out[slug] = {
                "name": norm_text(p.get("name")),
                "sku": (p.get("sku") or "").strip(),
                "categories": sorted({html.unescape(c.get("name")) for c in p.get("categories", []) if c.get("name")}),
                "images": sorted({i.get("src") for i in p.get("images", []) if i.get("src")}),
                "description": norm_text(p.get("description") or p.get("short_description")),
                "attributes": {a.get("name"): sorted(t.get("name") for t in a.get("terms", []))
                               for a in p.get("attributes", [])},
            }
        if page >= int(r.headers.get("X-WP-TotalPages", page)):
            break
        page += 1
    return out


# ---------------- knowledge store: baseline JSON (or a provided canonical file) ----------------
def load_knowledge_store(path: str) -> dict[str, dict]:
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "agar_products_*.json")))
        if not files:
            sys.exit(f"no agar_products_*.json in {path}")
        prods = json.load(open(files[-1]))
    else:
        prods = json.load(open(path))
    prods = prods if isinstance(prods, list) else prods.get("products", [])
    out = {}
    for p in prods:
        slug = slug_of(p.get("product_url", "")).lower()
        raw = (p.get("metadata") or {}).get("raw_extracted_data", {})
        out[slug] = {
            "name": norm_text(p.get("product_name")),
            "sku": (raw.get("sku") or "").strip(),
            "categories": sorted(set(as_list(raw.get("categories")))),
            "images": sorted(set(as_list(raw.get("product_images")))),
            "description": norm_text(p.get("description")),
            "attributes": {},
        }
    return out


# ---------------- reconcile ----------------
SCALAR = ["name", "sku", "description"]
SETS = ["categories", "images"]

def classify(h: dict, k: dict) -> list[dict]:
    """Return field-level findings for one product present in both sources."""
    findings = []
    for f in SCALAR:
        hv, kv = h.get(f, ""), k.get(f, "")
        if hv and kv and hv != kv:
            findings.append({"field": f, "kind": "CONFLICT", "harvest": hv, "knowledge": kv})
        elif hv and not kv:
            findings.append({"field": f, "kind": "enrichment", "harvest": hv, "knowledge": ""})
        elif kv and not hv:
            findings.append({"field": f, "kind": "regression", "harvest": "", "knowledge": kv})
    for f in SETS:
        hs, ks = set(h.get(f, [])), set(k.get(f, []))
        if hs and ks and hs != ks:
            findings.append({"field": f, "kind": "CONFLICT",
                             "harvest": sorted(hs), "knowledge": sorted(ks),
                             "only_harvest": sorted(hs - ks), "only_knowledge": sorted(ks - hs)})
        elif hs and not ks:
            findings.append({"field": f, "kind": "enrichment", "harvest": sorted(hs), "knowledge": []})
    return findings


def reconcile(harvest: dict, ks: dict) -> dict:
    h, k = set(harvest), set(ks)
    both = sorted(h & k)
    products = {}
    conflict_products = 0
    field_conflicts = {f: 0 for f in SCALAR + SETS}
    for slug in both:
        fs = classify(harvest[slug], ks[slug])
        if fs:
            products[slug] = fs
        if any(x["kind"] == "CONFLICT" for x in fs):
            conflict_products += 1
        for x in fs:
            if x["kind"] == "CONFLICT":
                field_conflicts[x["field"]] += 1
    return {
        "counts": {"harvest": len(h), "knowledge_store": len(k), "in_both": len(both),
                   "harvest_only": sorted(h - k), "knowledge_only": sorted(k - h)},
        "conflict_product_count": conflict_products,
        "field_conflict_totals": field_conflicts,
        "products": products,
    }


# ---------------- output ----------------
def to_console(rep: dict) -> None:
    c = rep["counts"]
    print("\n============ AGAR RECONCILIATION — harvest vs knowledge store ============")
    print(f"harvest (Store API): {c['harvest']}   knowledge store: {c['knowledge_store']}   in both: {c['in_both']}")
    if c["harvest_only"]:
        print(f"  only in harvest ({len(c['harvest_only'])}): {c['harvest_only'][:10]}")
    if c["knowledge_only"]:
        print(f"  only in knowledge store ({len(c['knowledge_only'])}): {c['knowledge_only'][:10]}")
    print(f"\nproducts with >=1 CONFLICT: {rep['conflict_product_count']}")
    print("field conflict totals:", {k: v for k, v in rep["field_conflict_totals"].items() if v})
    print("\n--- sample conflicting values (first 12) ---")
    shown = 0
    for slug, fs in rep["products"].items():
        confs = [x for x in fs if x["kind"] == "CONFLICT"]
        for x in confs:
            hv = x["harvest"] if not isinstance(x["harvest"], list) else ", ".join(x["harvest"])
            kv = x["knowledge"] if not isinstance(x["knowledge"], list) else ", ".join(x["knowledge"])
            print(f"  [{slug}] {x['field']}:")
            print(f"       harvest   = {str(hv)[:90]}")
            print(f"       knowledge = {str(kv)[:90]}")
            shown += 1
            if shown >= 12:
                break
        if shown >= 12:
            break
    print("=========================================================================\n")


def to_html(rep: dict, path: str) -> None:
    def cell(v):
        s = v if not isinstance(v, list) else "<br>".join(v)
        s = html.escape(str(s))
        return s if len(s) <= 240 else s[:240] + " …"
    rows = []
    for slug, fs in rep["products"].items():
        for x in fs:
            hv = cell(x["harvest"])
            kv = cell(x["knowledge"])
            cls = x["kind"].lower()
            rows.append(
                f'<tr class="{cls}"><td>{html.escape(slug)}</td><td>{html.escape(x["field"])}</td>'
                f'<td class="k">{x["kind"]}</td><td>{hv or "<i>∅</i>"}</td><td>{kv or "<i>∅</i>"}</td></tr>')
    c = rep["counts"]
    doc = f"""<!doctype html><meta charset=utf-8><title>Agar reconciliation</title>
<style>
 body{{font:14px/1.5 system-ui,sans-serif;margin:24px;color:#16201f}}
 h1{{font-size:22px}} .sub{{color:#567}}
 table{{border-collapse:collapse;width:100%;margin-top:16px;font-size:13px}}
 th,td{{border:1px solid #dde;padding:6px 8px;text-align:left;vertical-align:top}}
 th{{background:#eef2f1}} td.k{{font-weight:700;font-family:monospace}}
 tr.conflict{{background:#fdecea}} tr.conflict td.k{{color:#bb3f2c}}
 tr.enrichment td.k{{color:#2f9257}} tr.regression td.k{{color:#b3760a}}
</style>
<h1>Agar reconciliation — harvest vs knowledge store</h1>
<p class=sub>harvest (Store API): {c['harvest']} &middot; knowledge store: {c['knowledge_store']} &middot;
 in both: {c['in_both']} &middot; products with conflicts: {rep['conflict_product_count']}</p>
<p class=sub>Legend: <b style="color:#bb3f2c">CONFLICT</b> = both non-empty &amp; different &middot;
 <b style="color:#2f9257">enrichment</b> = harvest adds a value &middot;
 <b style="color:#b3760a">regression</b> = knowledge store had a value harvest lost.</p>
<table><tr><th>product</th><th>field</th><th>kind</th><th>harvest (Store API)</th><th>knowledge store</th></tr>
{''.join(rows)}
</table>"""
    open(path, "w").write(doc)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--knowledge-store", default="output/baseline_0.7.4")
    ap.add_argument("--base-url", default="https://agar.com.au")
    ap.add_argument("--out", default="docs/rebuild/eval/out")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    print(f"Harvesting Store API from {args.base_url} ...")
    harvest = harvest_store_api(args.base_url)
    print(f"Loading knowledge store from {args.knowledge_store} ...")
    ks = load_knowledge_store(args.knowledge_store)

    rep = reconcile(harvest, ks)
    json.dump(rep, open(os.path.join(args.out, "reconciliation.json"), "w"), indent=2)
    to_html(rep, os.path.join(args.out, "reconciliation.html"))
    to_console(rep)
    print(f"Wrote {args.out}/reconciliation.json and reconciliation.html")


if __name__ == "__main__":
    main()
