# Rebuild hand-off package — `agar-catalog`

The decision (see the fork-sync analysis) is to **stop maintaining this stale crawl4ai fork** and rebuild the
Agar catalogue pipeline greenfield: API-first (WooCommerce Store API), crawl4ai as an optional dependency.
This folder is the self-contained hand-off so a fresh Claude Code session can build that project with no
reference back to this fork beyond the files listed in `MIGRATION_MAP.md`.

## Read / use in this order
1. **`CLAUDE_CODE_BUILD_PROMPT.md`** — paste into a fresh Claude Code session in a new empty repo. The prompt.
2. **`PROJECT_SPEC.md`** — architecture, module contracts, deps, client-config schema, output contract.
3. **`AGAR_DATA_SOURCE_EVALUATION.md`** — why the Store API is primary; the mechanism matrix + access/governance.
4. **`MIGRATION_MAP.md`** — exactly what to port from this fork (pydantic v1→v2) and what to drop.
5. **`agar_mechanism_compare.py`** — runnable parity harness (Store API vs baseline). Verified this session:
   192/192 products, and the API adds **sku + attributes** the old scraper never captured.
6. **`NEW_REPO_README.md`, `NEW_REPO_CLAUDE.md`** — drop into the new repo as `README.md` / `CLAUDE.md`.

## Key facts (verified live)
- Store API `GET /wp-json/wc/store/v1/products` — **192 products, no auth**, fully structured.
- Documents (SDS/PDS) are page links, not API fields → a light per-page enricher closes the gap.
- The parity oracle is the committed `output/baseline_0.7.4/` (HTTP-mode, 192 products).
