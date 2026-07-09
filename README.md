# agar-catalog

API-first product-catalogue harvester. Reads the **WooCommerce Store API** (not a browser crawl),
normalises to the 3DN JSON contract, and writes the same 8-file output set + per-product markdown the
old scraper produced — better-populated, with `sku` and `attributes` the scrape never captured.

It replaces a browser-first scraper that lived in a stale `crawl4ai` fork. crawl4ai is now an **optional
fallback dependency**, not the spine.

## Install
```bash
pip install .            # core: httpx, pydantic v2, pyyaml, typer — no browser/LLM stack
pip install .[crawl]     # optional crawl4ai>=0.9.1 fallback source
pip install .[postgres]  # optional asyncpg sink
pip install .[dev]       # pytest, ruff, mypy
```

## Use
```bash
harvest run --client agar                 # Store API → 8 JSON files + markdown in output/agar
harvest run --client agar --limit 10 --out /tmp/agar
harvest run --client agar --no-documents  # skip the per-page SDS/PDS fetch
harvest compare --client agar             # reconcile vs the knowledge store; highlight conflicts
```
A client is a YAML file in `clients/` (base URL, source, document-link patterns) — adding one needs no code.

## What it produces (the ingestion contract, unchanged)
`agar_products`, `agar_media`, `agar_documents`, `agar_categories`, `agar_product_categories`,
`agar_summary`, plus `agar_catalog_complete` / `agar_catalog_legacy`, and per-product markdown. These feed
the existing ingestion pipeline unchanged — the `JSONNormalizer` and `AgarCatalogData` model are ported
as-is, so the files are source-independent.

New vs the old scrape: `sku`, `price`, `attributes` (pH / size / code) are now first-class fields; the
Store API returns **all** categories and the **full** image gallery (the scrape captured one of each). SDS/PDS
documents aren't in the API — the `DocumentEnricher` fetches them per product page.

## Layout
```
src/agar_catalog/
  cli.py            # `harvest run` / `harvest compare`
  config.py         # load clients/<name>.yaml
  model.py          # pydantic v2 schemas (ProductSchema + sku/price/attributes, Media/Doc/Category)
  sources/
    woo_store_api.py  # PRIMARY
  enrich.py         # DocumentEnricher (per-page SDS/PDS)
  documents.py      # DocumentHandler (ported)
  normalizer.py     # JSONNormalizer — the 3DN output contract (ported)
  markdown.py       # MarkdownGenerator (ported)
  compare.py        # reconciliation / conflict highlighter
  util.py           # id + text helpers (ported)
clients/agar.yaml
tests/              # offline unit tests + baseline parity fixture
```

## Environment note
Plain HTTPS works through an egress proxy with `SSL_CERT_FILE` + `HTTPS_PROXY` set. A headless browser can
be reset by such a proxy — prefer the API/HTTP sources there; don't add a browser to work around it.

## Access & governance
The Store API needs no key today, but it's the owner's endpoint (rate-limitable, changeable). For a durable
integration, move to an owner-authorised source — a WooCommerce `wc/v3` consumer key (env var, never
committed) or an owner-supplied CSV/JSON/HTML export.
