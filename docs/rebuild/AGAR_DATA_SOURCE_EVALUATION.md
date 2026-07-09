# Agar data-acquisition mechanism evaluation

Which **mechanism** best retrieves the Agar product catalogue — not which crawler. All figures verified
live against `agar.com.au` (a WooCommerce/WordPress site) during analysis.

## TL;DR
Use the **WooCommerce Store API** as the primary source. It returns all **192 products** fully structured
(including the spec attributes scraping struggles with), needs **no API key**, no browser, and works through
a restrictive egress proxy. HTML scraping is a fallback; a headless browser is a last resort. For a
production/durable integration, move to an **owner-authorised** source (a `wc/v3` key or an owner-supplied
export).

## What the site exposes (verified)
| Endpoint | Result | Notes |
|---|---|---|
| `GET /wp-json/wc/store/v1/products` | **200, no auth** | `X-WP-Total: 192`. Full records — see fields below. |
| `GET /wp-json/wc/v3/products` | **401** `woocommerce_rest_cannot_view` | The **key-based** Admin API. |
| `GET /wp-json/wp/v2/product` | 200 | WordPress core REST; raw post content. |
| product page `<script type="application/ld+json">` | present | schema.org `Product`, `AggregateRating`. |
| `GET /product-sitemap.xml` | 200 | 192 product URLs (discovery for the HTTP-CSS fallback). |
| public product feed (CSV/XML) | 404 | none published. |
| public GitHub repo / site source | none | hosted WooCommerce — the API is its structured source of truth. |

**Store API record fields:** `name, slug, sku, short_description, description, prices, images[], categories[],
tags, brands, attributes[] (Code / Perfume / pH Level / Sizes — the real spec data), variations, weight,
dimensions, stock`. Paginate `?per_page=100&page=N`; project with `?_fields=`.

## Comparison matrix (retrieving the Agar catalogue)
| Mechanism | Complete | Structured | JS-free | Robust | Access (verified) | Proxy-OK | Verdict |
|---|---|---|---|---|---|---|---|
| **Store API** `wc/store/v1` | 192/192 + attributes | ✅ JSON | ✅ | ✅ | **no key — anon 200** | ✅ | **Primary (no-friction)** |
| Owner-supplied export (CSV/JSON/HTML) | owner-defined | ✅/⚠ | ✅ | ✅ | owner grant (clean) | ✅ | **Best if sanctioned** |
| Admin REST `wc/v3` | full incl. private | ✅ JSON | ✅ | ✅ | **key/secret (401 without)** | ✅ | Sanctioned integration |
| JSON-LD per page | per-product | ✅ JSON | ✅ | ✅ | public | ✅ | Enrichment / fallback |
| HTTP + CSS (baseline) | 192 title+desc | ⚠ selector-shaped | ✅ | ✗ fragile | public | ✅ | Fallback for non-API sites |
| WP REST `wp/v2/product` | posts | ✅ JSON | ✅ | ✅ | public read (some auth) | ✅ | Secondary |
| Headless-browser crawl | + JS tabs | ⚠ selector-shaped | ✗ | ✗ fragile | public | ✗ (TLS reset) | Last resort |
| Repo / static source | none public | — | — | — | — | — | Check per client |

## Access & governance
- **Store API read needs no credentials** — the public front-end API, same access any visitor's browser has;
  no nonce/cart-token for reads. **But** it's the owner's endpoint: rate-limitable, changeable without
  notice, and programmatic use carries terms-of-use / legal / ethical weight. Great for evaluation; **not a
  contract**.
- **Key-based path:** Admin REST `wc/v3` needs a consumer **key/secret the owner issues** (read scope). The
  durable, authorised route.
- **Cleanest of all:** an **owner-supplied export** — WooCommerce's built-in Product CSV export, a JSON/CSV
  dump, a static "baked-out" HTML export of product pages, or a Google-Merchant/Feedonomics feed. Explicitly
  authorised and independent of a live endpoint.

## Recommendation (two-track)
1. **Evaluate / start now:** public **Store API** → `ProductSchema`. Complete, structured, no key, no
   browser, proxy-safe.
2. **Production / durable:** owner-authorised source — a `wc/v3` key **or** an owner-supplied export.
3. Keep **HTTP-CSS** as the generic fallback; retire the **headless browser** to last resort.
4. **Documents gap (verified):** SDS/PDS PDFs are **not** in the Store API — they're links on the product
   page (`/sds/`, `/{slug}-pds-sds`). Close with a light per-page fetch (the `DocumentEnricher`), not by
   adding a browser.
