# Evaluation — harvest vs knowledge store (conflict highlighter)

An evaluation slice of the `agar-catalog` rebuild: harvest the Agar catalogue from the **WooCommerce Store
API** and reconcile it against the **current knowledge store**, highlighting **conflicting values**.

- `reconcile.py` — the tool. Fetches the Store API, loads the knowledge store, classifies every field as
  **conflict / enrichment / regression**, and writes `out/reconciliation.json` + a colour-coded
  `out/reconciliation.html`.
- `CONFLICT_FINDINGS.md` — this session's results and what each conflict means (per-field, with a
  recommendation on which source to trust).
- `out/` — generated report (192 products).

## Run
```bash
export SSL_CERT_FILE=/root/.ccr/ca-bundle.crt   # restricted-egress environments only
python reconcile.py --knowledge-store output/baseline_0.7.4 --out docs/rebuild/eval/out
```

## "Knowledge store" — what it points at
Defaults to the committed baseline (`output/baseline_0.7.4/`) as a stand-in for the current canonical Agar
data. Point `--knowledge-store` at your **real** Agar knowledge store — a canonical JSON export, a CRM dump,
or a prior delivered catalogue — to reconcile against that. The conflict logic is source-agnostic; it keys
products by URL slug and compares `name, sku, categories, images, description`.

## This is an evaluation, not the product
It reuses the Store-API harvest logic destined for `sources/woo_store_api.py` and the reconciliation logic
destined for a `reconcile`/`compare` command. When the new **agar-catalog** repo exists, lift this into it.

> Note: the new repo could not be created from this session — the GitHub App here only has access to
> `vargamick/crawl4ai`, not repo-creation rights (`403 Resource not accessible by integration`). Create
> `agar-catalog` on GitHub (or grant the app Administration access), then this evaluation drops straight in.
