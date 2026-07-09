# CLAUDE.md — agar-catalog

> Template for the new repo's `CLAUDE.md` (Claude Code project guidance). Copy to the repo root.

## What this is
An **API-first** product-catalogue harvester. It pulls a client's catalogue from the best structured source
and normalises it to the 3DN JSON contract. **crawl4ai is an optional fallback dependency, never the spine.**
Built to replace a browser-first scraper from a stale crawl4ai fork.

## Golden rules
- **Do not add a headless-browser dependency to the core.** `pip install .` must not pull playwright/litellm.
  Browser/generic crawling lives behind the `[crawl]` extra and lazy imports.
- **API-first.** Default source is the WooCommerce Store API (`/wp-json/wc/store/v1/products`, no key).
  Only fall to JSON-LD → HTTP-CSS → crawl4ai when a site lacks an API.
- **Config-driven.** A client = a YAML file in `clients/`. No client-specific branches in core code.
- **Keep the output contract.** The `JSONNormalizer` 3DN file shape is a downstream contract — don't change
  field names/structure without a migration.
- **No secrets in code or config.** Any `wc/v3` key comes from an env var.
- **pydantic v2** throughout (`model_config = ConfigDict(...)`, `model_dump()`, `field_validator`).

## Setup
```bash
pip install -e .[dev]          # core + pytest/ruff/mypy
export SSL_CERT_FILE=$CA HTTPS_PROXY=$PROXY   # only in restricted-egress environments
```

## Common commands
```bash
harvest --client agar                 # run the pipeline
harvest compare --client agar         # parity vs tests/fixtures/baseline_0.7.4
pytest -q                             # unit tests (mock HTTP; no live calls in tests)
ruff check . && mypy src
```

## Where things live
- `src/agar_catalog/sources/` — data sources; `woo_store_api.py` is primary.
- `src/agar_catalog/enrich/documents.py` — per-page SDS/PDS fetch (docs aren't in the Store API).
- `src/agar_catalog/normalize/` + `output/` — ported normalizer + markdown (the 3DN contract).
- `clients/*.yaml` — one file per client.
- `tests/fixtures/baseline_0.7.4/` — the parity oracle (HTTP-mode, 192 products).

## Gotchas (verified during analysis)
- Agar's catalogue index is `/cleaning-products/`; products are `/product/<slug>/`. The old `/products/` URL
  is a 404 — don't reintroduce it.
- SDS/PDS docs are page links (`/sds/`, `/{slug}-pds-sds`), not Store-API fields.
- A headless browser's TLS is reset by some egress proxies (`ERR_CONNECTION_RESET`); the API/HTTP paths work.
