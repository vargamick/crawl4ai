# CLAUDE.md — agar-catalog

API-first product-catalogue harvester. Pulls a client's catalogue from the best structured source and
normalises it to the 3DN JSON contract. **crawl4ai is an optional fallback dependency, never the spine.**

## Golden rules
- **API-first.** Default source is the WooCommerce Store API (`/wp-json/wc/store/v1/products`, no key).
  Only fall to HTML/JSON-LD/crawl4ai for sites without an API.
- **No browser in the core.** `pip install .` must not pull playwright/litellm. crawl4ai lives behind the
  `[crawl]` extra with lazy imports.
- **Keep the output contract.** `normalizer.py` (JSONNormalizer) + `model.py` (AgarCatalogData) define the
  8-file / 5-table ingestion contract — don't change field names/shape without a migration.
- **Config-driven.** A client = `clients/<name>.yaml`. No client-specific branches in the core.
- **pydantic v2** throughout. **No secrets in code** — a `wc/v3` key would come from an env var.

## Setup & commands
```bash
pip install -e .[dev]
export SSL_CERT_FILE=$CA HTTPS_PROXY=$PROXY   # restricted-egress environments only
harvest run --client agar                     # harvest → output/agar
harvest compare --client agar                 # conflicts vs tests/fixtures/baseline_0.7.4
pytest -q                                      # offline unit tests (no live calls)
ruff check .
```

## Ported from the old crawl4ai fork (crawl4ai-free)
`model.py` (was `schemas.py`, upgraded to pydantic v2 + new `sku`/`price`/`attributes`), `normalizer.py`,
`markdown.py`, `documents.py`, `util.py`. Keep them behaviourally identical to preserve the output contract.

## Gotchas (verified)
- Agar catalogue index is `/cleaning-products/`; products `/product/<slug>/`. The old `/products/` URL 404s.
- SDS/PDS docs are product-page links (`/sds/`, `/{slug}-pds-sds`), not Store-API fields → `enrich.py`.
- The Store API returns ALL categories and the FULL image gallery; the old scrape captured one of each.
