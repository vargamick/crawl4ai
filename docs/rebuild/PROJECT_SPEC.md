# PROJECT_SPEC — `agar-catalog`

A clean, API-first product-catalogue harvester. Replaces the `vargamick/crawl4ai` fork's browser-first
Agar scraper. crawl4ai is an **optional fallback dependency**, not the spine.

> Full rationale for the greenfield decision: `AGAR_DATA_SOURCE_EVALUATION.md` and the fork-sync analysis.
> What to carry over from the old fork: `MIGRATION_MAP.md`.

---

## 1. Goals & non-goals

**Goals**
- Retrieve a complete, normalised product catalogue for a client (Agar first) from the **best available
  structured source** — for Agar that's the WooCommerce **Store API**, not HTML scraping.
- Be **source-agnostic**: the same normaliser + output layer serves API, JSON-LD, HTML-CSS, or a generic
  crawl. Adding a client is a **YAML file**, not new code.
- Stay **lean**: `pip install .` pulls no browser/LLM stack. Heavy crawling is an opt-in extra.
- Produce output **byte-comparable in shape** to the existing 3DN normalized JSON contract, so downstream
  consumers don't change.

**Non-goals (v1)**
- No headless-browser dependency in the default install.
- No web frontend and no live service/DB in v1 (spec'd as optional later modules).
- Not a general crawler framework — it's a catalogue harvester that *can* fall back to crawling.

---

## 2. Dependencies

| Scope | Packages |
|---|---|
| **Core** (`pip install .`) | `httpx`, `pydantic>=2`, `beautifulsoup4`, `lxml`, `pyyaml`, `typer` (CLI) |
| **`[crawl]` extra** | `crawl4ai>=0.9.1` — used only by `sources/crawl4ai_source.py` |
| **`[postgres]` extra** | `asyncpg` — used only by the optional Postgres sink |
| **Dev** | `pytest`, `pytest-asyncio`, `ruff`, `mypy` |

Python **3.11**. `src/` layout, `pyproject.toml` (PEP 621), no `setup.py`.

**Proxy/TLS note (matters in restricted environments):** plain HTTP (`httpx`) works through an egress
proxy when `SSL_CERT_FILE`/`HTTPS_PROXY` are set; a **headless browser may be reset by such a proxy**
(`ERR_CONNECTION_RESET`). The API-first design sidesteps this entirely — one more reason crawl4ai is optional.

---

## 3. Layout

```
agar-catalog/
  pyproject.toml
  README.md                      CLAUDE.md
  src/agar_catalog/
    cli.py                       # `harvest` (typer)
    config.py                    # load + validate client YAML
    model/
      product.py                 # ProductSchema, MediaSchema, DocumentSchema, CategorySchema (pydantic v2)
    sources/
      base.py                    # ProductSource protocol
      woo_store_api.py           # WooCommerceStoreAPISource  ← PRIMARY
      jsonld.py                  # JsonLdSource
      http_css.py                # HttpCssSource
      crawl4ai_source.py         # Crawl4aiSource            [crawl extra]
    enrich/
      documents.py               # DocumentEnricher (SDS/PDS per-page links)
    normalize/
      normalizer.py              # JSONNormalizer → 3DN output contract
    output/
      json_writer.py
      markdown.py                # MarkdownGenerator (ported)
      postgres.py                # optional sink            [postgres extra]
    util/
      ids.py text.py http.py     # generate_product_id, clean_text, shared httpx client
    compare/
      harness.py                 # mechanism parity report
  clients/
    agar.yaml
  tests/
    fixtures/baseline_0.7.4/     # the committed baseline → parity oracle
    test_normalizer.py test_woo_store_api.py test_markdown.py
```

---

## 4. Core contracts

### 4.1 `ProductSource` protocol (`sources/base.py`)
```python
class ProductSource(Protocol):
    name: str
    async def discover(self) -> list[str]: ...        # product identifiers/urls
    async def fetch(self, ident: str) -> ProductSchema | None: ...
    async def harvest(self, limit: int | None = None) -> list[ProductSchema]: ...
```
`harvest()` has a default implementation (discover → bounded-concurrency fetch); a source that returns
whole pages (the Store API) overrides `harvest()` to paginate directly.

### 4.2 `WooCommerceStoreAPISource` (PRIMARY)
- Endpoint from config: `GET {base}/wp-json/wc/store/v1/products?per_page=100&page=N`.
- Anonymous — **no key** (verified). Read `X-WP-Total` / `X-WP-TotalPages` for pagination.
- Map each record → `ProductSchema`:
  `name→product_name, slug→id seed, sku, short_description+description→description, images[]→MediaSchema,
  categories[].name→CategorySchema, attributes[] (Code/Perfume/pH Level/Sizes)→spec fields, prices, stock`.
- Use `?_fields=` projection to keep payloads small.

### 4.3 `DocumentEnricher` (`enrich/documents.py`)
SDS/PDS documents are **not** in the Store API — they're links on the product page
(`/sds/`, `/{slug}-pds-sds`). For each product, do one light `httpx` GET of `permalink`, extract doc links
with the config's `document_link_patterns`, hand them to the ported `DocumentHandler` → `DocumentSchema`.
Skippable via `--no-documents`.

### 4.4 Fallback sources
- `JsonLdSource` — parse `<script type="application/ld+json">` `Product` nodes per page.
- `HttpCssSource` — the current baseline approach (httpx + CSS selectors), for sites without an API.
- `Crawl4aiSource` — `[crawl]` extra; wraps crawl4ai `AsyncWebCrawler` (or its HTTP strategy) for generic
  sites. Import lazily so core installs stay light.

### 4.5 Output contract
`JSONNormalizer` (ported) emits the **same 3DN file set** as today so downstream doesn't change:
`agar_products`, `agar_media`, `agar_categories`, `agar_product_categories`, `agar_documents`,
`agar_summary`, plus `agar_catalog_complete` / `agar_catalog_legacy`. `MarkdownGenerator` emits per-product
markdown. Optional `postgres.py` upserts the normalized rows.

---

## 5. Client config schema (`clients/agar.yaml`)
```yaml
client: agar
base_url: https://agar.com.au
source: store_api                 # store_api | jsonld | http_css | crawl4ai
store_api:
  path: /wp-json/wc/store/v1/products
  per_page: 100
documents:
  enabled: true
  # links matched on each product page and classified by DocumentHandler
  link_patterns: ['\.pdf($|\?)', '/sds/', '-pds-sds', 'datasheet', 'safety']
http_css:                          # only used when source: http_css
  discovery: sitemap               # sitemap | crawl
  sitemap: /product-sitemap.xml
output:
  dir: output/agar
  formats: [json, markdown]
```

---

## 6. CLI
```
harvest --client agar                         # uses config's source (store_api)
harvest --client agar --source http_css       # override
harvest --client agar --limit 10 --out /tmp   # bounded run
harvest compare --client agar                 # run compare/harness.py
```
`typer` gives `--help` for free. No secrets in code or config — a `wc/v3` key (if ever used) comes from an
env var, never committed.

---

## 7. Definition of done
- `harvest --client agar` → **192 products** with `sku`, `categories`, and `attributes` (pH/size/code)
  populated; JSON + markdown written in the 3DN shape.
- `harvest compare --client agar` reports **≥ parity** with `tests/fixtures/baseline_0.7.4` and flags the
  SDS/PDS document delta.
- `pip install .` installs no playwright/litellm; `pip install .[crawl]` adds the fallback.
- `pytest` green on normalizer/markdown/store-api unit tests.
