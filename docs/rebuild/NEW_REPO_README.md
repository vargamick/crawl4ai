# agar-catalog

> Template README for the new project. Copy to the new repo's `README.md`.

API-first product-catalogue harvester. Retrieves a client's product catalogue from the best available
**structured** source — for Agar, the WooCommerce **Store API** — normalises it to the 3DN JSON contract,
and writes JSON + per-product markdown. A headless browser is a last-resort fallback, not a dependency.

## Why this exists
It replaces a browser-first scraper that lived in a stale `crawl4ai` fork. Analysis showed the fork's value
was a few crawl4ai-free modules and that the right Agar data path is the Store API, not a crawl — so this is
a clean rebuild that takes crawl4ai as an *optional* dependency. See `docs/AGAR_DATA_SOURCE_EVALUATION.md`.

## Install
```bash
pip install .            # core: httpx, pydantic v2, bs4, lxml, pyyaml, typer — NO browser/LLM stack
pip install .[crawl]     # adds crawl4ai>=0.9.1 for the generic-crawler fallback
pip install .[postgres]  # adds asyncpg for the optional DB sink
```

## Use
```bash
harvest --client agar                      # Store API → JSON + markdown (default)
harvest --client agar --limit 10 --out /tmp/agar
harvest --client agar --source http_css    # override the source
harvest compare --client agar              # parity report vs the baseline fixture
harvest --help
```
A client is a YAML file in `clients/` (base URL, source, document link patterns) — adding one needs no code.

## Data sources (best → last resort)
1. **WooCommerce Store API** — public, no key, complete + structured (incl. sku, categories, attributes).
2. **JSON-LD** / **WP REST** — structured fallbacks.
3. **HTTP + CSS** — selector-based, for sites without an API.
4. **crawl4ai** (`[crawl]` extra) — generic/browser last resort.

Documents (SDS/PDS) are fetched by a light per-page enricher — they're not in the Store API.

## Environment note
Plain HTTPS works through an egress proxy when `SSL_CERT_FILE` and `HTTPS_PROXY` are set. A **headless
browser can be reset by such a proxy** — prefer the API/HTTP sources there; don't add a browser to work
around a proxy, report the restriction.

## Access & governance
The Store API needs no key today, but it's the owner's endpoint (rate-limitable, changeable). For a
production/durable integration use an owner-authorised source: a WooCommerce `wc/v3` consumer key (env var,
never committed) or an owner-supplied CSV/JSON/HTML export. See `docs/AGAR_DATA_SOURCE_EVALUATION.md`.

## Layout
See `docs/PROJECT_SPEC.md` for the full architecture and `docs/MIGRATION_MAP.md` for what was ported from
the old fork.
