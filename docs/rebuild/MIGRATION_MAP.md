# MIGRATION_MAP — old fork → `agar-catalog`

Exactly what to carry from `vargamick/crawl4ai` (branch `claude/fork-sync-plan-lwz0p0`) into the new
project, and what to drop. The carry-over modules are all **crawl4ai-free** and portable; the only real
work is a **pydantic v1 → v2** upgrade and re-wiring imports to the new package layout.

## Carry over (port, upgrading pydantic to v2)

### `clients/agar/schemas.py` (157 L) → `src/agar_catalog/model/product.py`
Port these public symbols verbatim, then upgrade to pydantic v2:
- Enums: `MediaType`, `MediaFormat`, `DocumentType`
- Models: `ProductSchema`, `MediaDimensions`, `MediaSchema`, `DocumentSchema`, `CategorySchema`,
  `ProductCategoryRelation`, `AgarCatalogData`
- `ScrapingConfig` → rename/rework into the new **client-config** model (see `PROJECT_SPEC.md` §5); the old
  `base_url`/`max_products`/`delay_seconds` fields map onto the YAML config.

**pydantic v2 changes (the only breaking edits):**
- `class Config:` at **lines 133 and 155** → `model_config = ConfigDict(...)`.
- `HttpUrl` fields: v2 returns a `Url` object, not `str` — call `str(url)` where the old code assumed a
  string (notably in `generate_product_id` and any f-string building output paths).
- Replace any `@validator` with `@field_validator`; `.dict()`/`.json()` → `.model_dump()`/`.model_dump_json()`.

### `clients/agar/utils.py` (399 L) → `src/agar_catalog/util/`
Cherry-pick (they have no external coupling): `generate_product_id`, `generate_media_id`,
`generate_document_id`, `generate_category_id`, `clean_text`, `extract_urls_from_text`,
`detect_document_type`, `detect_media_format`, `normalize_category_name`, `create_slug`,
`safe_filename`, `ensure_directory`, `extract_version_from_filename`, `format_file_size`, `batch_items`.
Split across `ids.py` / `text.py` / `fs.py` as you like.

### `clients/agar/json_normalizer.py` (384 L) → `src/agar_catalog/normalize/normalizer.py`
Port `JSONNormalizer` whole — it defines the **3DN output contract** and must not change shape. Keep methods
`normalize_catalog_data`, `save_normalized_files`, `save_legacy_format`, `create_summary_report`,
`save_summary_report`. Only edit: imports (new model path) and pydantic `.model_dump()` calls.

### `clients/agar/markdown_generator.py` (360 L) → `src/agar_catalog/output/markdown.py`
Port `MarkdownGenerator` as-is (crawl4ai-free). Methods: `generate_product_markdown`,
`save_product_markdown`, `generate_index_markdown`, `save_index_markdown`, `generate_all_markdown`.

### `clients/agar/document_handler.py` (361 L) → `src/agar_catalog/enrich/documents.py`
Port `DocumentHandler`. In the old flow it read links out of `raw_extracted_data`; in the new flow the
**`DocumentEnricher`** supplies links from a per-product page fetch (SDS/PDS are not in the Store API), then
`DocumentHandler.extract_documents_from_product` classifies them. Keep `group_documents_by_type`,
`sort_documents_by_version`, `get_latest_document_by_type`.

### `output/baseline_0.7.4/` → `tests/fixtures/baseline_0.7.4/`
The committed HTTP-mode baseline (192 products) becomes the **parity oracle** for `compare/harness.py` and
the normalizer tests. Read its `README.md` for provenance/caveats.

## Reference only (don't port; reimplement clean)
- `clients/agar/product_extractor.py` — its **CSS extraction schema** (WooCommerce selectors:
  `h1.product_title`, `.woocommerce-product-gallery img`, `.posted_in a`, `a[href$='.pdf']`) is a useful
  starting point for `sources/http_css.py`. Its browser-based `discover_product_urls` is **not** carried —
  use sitemap discovery instead.
- `scratchpad/run_baseline.py` (in this session) — reference implementation of sitemap discovery + the
  HTTP-strategy approach for `sources/http_css.py` and `sources/crawl4ai_source.py`.

## Drop entirely
- The whole `crawl4ai/` fork package and the fork's git history (take crawl4ai from PyPI instead).
- Browser-first discovery; the stale `agar.com.au/products/` URL (now 404 → `/cleaning-products/`, products
  at `/product/<slug>/`).
- The docs reorg + 145 `docs/deprecated/examples_old/` files; `docker-compose*`, `tools/` relocations.
- `src/pipeline/universal_scraper.py` (its Store-API `/crawl` path is superseded by `woo_store_api.py`).

## Port only if wanted (optional later modules — leave out of v1)
- `deploy/agar-scraper/` — Flask service + `database_integration.py` (asyncpg/Postgres). If ported, becomes
  `output/postgres.py` (sink) + a thin service wrapper; keep the same normalized rows.
- `crawl4ai-scraper-frontend/` — React UI. Out of scope for v1.
