# Pre-sync baseline — crawl4ai 0.7.4 (HTTP-mode)

Captured as the "before" reference to diff against after syncing the fork up to upstream
`unclecode/crawl4ai`. See the fork-sync analysis/plan for the full context.

## What this is
A full-catalogue run of the **real** Agar pipeline (`AgarScraper.run_complete_scraping` — the
actual extraction schema, media/document handlers and JSON normalizer) on the current `0.7.4` base.

- **Products:** 192 (100% with title + description)
- **Media:** 192 images (186 png / 6 jpg)
- **Categories:** 50 · **Product-category relationships:** 192
- **Documents:** 2 (SDS/certificate PDFs)

## Two caveats on how it was produced
1. **HTTP-mode, not browser.** Headless Chromium's TLS is reset by the remote session's egress
   proxy, so this run used crawl4ai's `AsyncHTTPCrawlerStrategy` instead of the browser. It captures
   server-rendered content (where the Agar product data lives); **JS-rendered tab content is excluded**,
   which is why document/PDF coverage is sparse. A browser-based baseline should be captured in an
   environment with unrestricted egress before relying on this for exact fidelity comparison.
2. **Discovery via sitemap.** The scraper's default `agar.com.au/products/` now 404s; the live site
   serves products at `/product/<slug>/`. Product URLs were taken from `product-sitemap.xml` (192 URLs).

## Files
`agar_products_*` · `agar_media_*` · `agar_categories_*` · `agar_product_categories_*` ·
`agar_documents_*` · `agar_summary_*` · plus combined (`agar_catalog_complete_*`) and
`agar_catalog_legacy_*` aggregates.
