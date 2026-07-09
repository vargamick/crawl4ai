# Claude Code build prompt — `agar-catalog`

Paste the block below into a fresh Claude Code session opened in a **new, empty repository**. Copy the four
supporting docs into that repo first (or attach them): `PROJECT_SPEC.md`, `AGAR_DATA_SOURCE_EVALUATION.md`,
`MIGRATION_MAP.md`, and `agar_mechanism_compare.py`. The prompt is self-contained — it needs no reference
back to the old `crawl4ai` fork beyond the files named in `MIGRATION_MAP.md`.

---

## PROMPT

You are building a new, standalone Python project called **`agar-catalog`** — an API-first product-catalogue
harvester. It replaces an old browser-based scraper that lived inside a stale `crawl4ai` fork. **Do not fork
crawl4ai**; take it only as an optional dependency. Follow `PROJECT_SPEC.md` exactly for architecture,
`MIGRATION_MAP.md` for what to port from the old fork, and `AGAR_DATA_SOURCE_EVALUATION.md` for why the
WooCommerce Store API is the primary data source.

### Ground rules
- **API-first.** The default and recommended path is the WooCommerce **Store API**
  (`/wp-json/wc/store/v1/products`) — public, no key, returns complete structured data. HTML scraping and
  crawl4ai are fallbacks only.
- **crawl4ai is optional.** It goes in a `[crawl]` extra and is imported lazily. `pip install .` (no extras)
  must NOT pull playwright or litellm.
- **Config-driven.** A client is a YAML file. No client-specific code paths in the core.
- **No secrets in code or config.** Any future `wc/v3` key comes from an env var.
- **Port, don't reinvent.** The old fork's `schemas.py`, `json_normalizer.py`, `markdown_generator.py`,
  `document_handler.py`, `utils.py` are crawl4ai-free — port them per `MIGRATION_MAP.md`, upgrading pydantic
  v1 `class Config` → v2 `model_config = ConfigDict(...)`.
- **Keep the output contract.** Emit the same 3DN normalized JSON file set as the old pipeline so downstream
  consumers are unaffected.
- Work in small commits, one per phase. Run `ruff` and `pytest` before each commit.

### Phase 1 — Scaffold
Create the `src/` layout, `pyproject.toml` (PEP 621, Python 3.11), core deps (`httpx`, `pydantic>=2`,
`beautifulsoup4`, `lxml`, `pyyaml`, `typer`), the `[crawl]`/`[postgres]`/`dev` extras, `ruff`+`mypy` config,
and a stub `harvest` CLI (`typer`) that prints `--help`. Add `README.md` and `CLAUDE.md` (from the new-repo
templates). Commit.

### Phase 2 — Model + normalizer (ported, pydantic v2)
Port `model/product.py` (ProductSchema + Media/Document/Category), `normalize/normalizer.py`,
`output/markdown.py`, `util/` helpers, and the `enrich/documents.py` document classifier per
`MIGRATION_MAP.md`. Upgrade to pydantic v2. Copy the old baseline output into
`tests/fixtures/baseline_0.7.4/`. Write `tests/test_normalizer.py` and `tests/test_markdown.py` against those
fixtures. Commit when green.

### Phase 3 — Primary source: WooCommerce Store API
Implement `sources/base.py` (the `ProductSource` protocol) and `sources/woo_store_api.py`:
- paginate `GET {base}/wp-json/wc/store/v1/products?per_page=100&page=N`, using `X-WP-Total` /
  `X-WP-TotalPages`;
- map each record → `ProductSchema` (name, slug, sku, descriptions, images, categories, **attributes**
  Code/Perfume/pH Level/Sizes, prices, stock);
- add `enrich/documents.py` wiring: one light `httpx` GET of each product's `permalink`, extract doc links
  with the config's `link_patterns`, classify via the ported `DocumentHandler`.
Add `clients/agar.yaml` per the spec. Write `tests/test_woo_store_api.py` (mock the HTTP layer — no live
calls in tests). Commit.

### Phase 4 — CLI + output
Wire `harvest --client agar [--source ...] [--limit N] [--out DIR] [--no-documents]` to: load config →
select source → harvest → normalize → write JSON + markdown in the 3DN shape. Commit.

### Phase 5 — Fallback sources (thin)
Implement `sources/http_css.py` (httpx + CSS, sitemap discovery via `/product-sitemap.xml`) and
`sources/jsonld.py` (schema.org `Product`). Implement `sources/crawl4ai_source.py` behind a lazy import
guarded by the `[crawl]` extra (raise a clear error if crawl4ai isn't installed). Commit.

### Phase 6 — Comparison harness + verification
Add `compare/harness.py` (adapt the provided `agar_mechanism_compare.py`): harvest via Store API and via
HTTP-CSS, normalize both, diff each against `tests/fixtures/baseline_0.7.4/`, and print a parity report
(product-count match, per-field coverage %, per-SKU presence, SDS/PDS document delta). Expose as
`harvest compare --client agar`. Commit.

### Verification (must pass before you report done)
1. `pip install .` then `python -c "import playwright"` **fails** (no browser stack pulled);
   `pip install .[crawl]` then the same import succeeds.
2. `harvest --client agar` (needs outbound HTTPS to agar.com.au) returns **192 products** with `sku`,
   `categories`, and `attributes` populated; JSON + markdown written.
3. `harvest compare --client agar` reports **≥ parity** vs the baseline fixture (the API should meet or beat
   the HTTP-CSS baseline on product count and field coverage) and lists the document delta.
4. `pytest` green; `ruff check` clean; `harvest --help` self-documents.

If outbound network is restricted in your environment: the Store API is plain HTTPS and works through a
proxy with `SSL_CERT_FILE`/`HTTPS_PROXY` set — do **not** add a browser dependency to work around it; report
the restriction instead.

### Report
When done, summarise: what was ported vs new, the `pip install .` dependency footprint, the parity-report
numbers, and any gaps (e.g. documents needing the per-page enricher).

---

## Notes for whoever runs this
- The **baseline fixture** to copy in lives at `output/baseline_0.7.4/` in the old fork
  (`vargamick/crawl4ai`, branch `claude/fork-sync-plan-lwz0p0`). It's HTTP-mode (192 products) — good as a
  shape/coverage oracle; recapture a browser-mode baseline only if you need exact JS-tab fidelity.
- Access reality for the Store API: **no key today**, but it's the owner's endpoint. For a production/durable
  integration, move to an owner-authorised source (a `wc/v3` consumer key or an owner-supplied CSV/HTML
  export) — see `AGAR_DATA_SOURCE_EVALUATION.md` §Access & governance.
