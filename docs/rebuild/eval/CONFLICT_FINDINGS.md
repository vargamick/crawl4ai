# Agar reconciliation — conflicting values (evaluation)

Run this session: **live WooCommerce Store API** ("harvest") vs the **current knowledge store**
(the committed `output/baseline_0.7.4/`, our HTTP-mode scrape). Tool: `reconcile.py`. Full data:
`out/reconciliation.json` + colour-coded `out/reconciliation.html`.

> A **conflict** = same product (by slug), same field, **both non-empty but different**. Distinct from
> **enrichment** (harvest adds a value the store lacked) and **regression** (store had a value harvest lost).

## Headline
| | |
|---|---|
| Products in both sources | **192 / 192** (perfect presence match, 0 only-in-either) |
| Products with ≥1 conflict | **192** |
| `name` conflicts | **0** — names agree (after HTML-entity normalisation) |
| `sku` conflicts | **0** — SKU is **API-only enrichment** (the scrape never captured it) |
| `attributes` (pH/size/code) | **API-only enrichment** — absent from the scrape entirely |
| `categories` conflicts | **53 genuine** (+43 were false `&amp;` vs `&` encoding, now normalised out) |
| `description` conflicts | **192** |
| `images` conflicts | **191** |

## What each conflict actually means (cause → who's right)

**`categories` (53) — the scrape under-captured; the API is authoritative.**
The old CSS scrape took only the *first* `.posted_in a` link, so it recorded **one** category per product.
The Store API returns **all** of them. Every conflict is the API being a superset:
- `acid-wash` → API `[Metal Products, Ware Washing]` vs store `[Metal Products]`
- `bac2work` → API `[Biological, Green Cleaning, Toilet & Bathroom]` vs store `[Biological]`
→ **Trust the API.** No merge needed — the API is a strict superset.

**`description` (192) — the sources capture different sections.**
The Store API `description` field is the long *"How Does It Work?"* body; the scrape captured the short
*"What is X?"* intro from a different selector. Neither is wrong; they're different content blocks.
→ **Decision required:** adopt the API's full description as canonical (recommended — it's the richer,
structured field), optionally keeping the short intro as a `summary`. Don't treat these as data errors.

**`images` (191) — single scraped image vs full gallery.**
The scrape grabbed one primary image (often a newer `…-1000x1000.png` render); the API returns the whole
gallery (often multiple, sometimes older original filenames).
→ **Trust the API gallery** for completeness; if a specific hero render is wanted, select by filename rule.

**`name` (0) / `sku` (0).** Names agree. SKU exists only via the API → pure enrichment, no conflict.

## Bottom line
The conflicts aren't two credible sources disagreeing on facts — they're the **HTML scrape being lossy**
(one category, one image, the wrong description block, no SKU/attributes) against a **complete structured
API**. This is direct evidence for the greenfield decision: adopt the **Store API as the canonical source**,
map its full `categories`/`images`/`attributes`/`sku`, choose the API `description` as canonical, and keep
the per-page enricher only for SDS/PDS documents (not in the API).

## Reproduce / point at your real knowledge store
```bash
export SSL_CERT_FILE=$CA HTTPS_PROXY=$PROXY   # restricted-egress only
python reconcile.py --knowledge-store <DIR-or-canonical.json> --base-url https://agar.com.au --out out
```
`--knowledge-store` defaults to the baseline; point it at the **actual** Agar knowledge store (a canonical
JSON export, a CRM dump, etc.) to reconcile against that instead — the conflict logic is source-agnostic.
