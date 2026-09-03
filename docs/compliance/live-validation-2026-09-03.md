# Live Scraping Validation Report — 2026-09-03

**Scope:** Tokopedia product + review scrapers, minimal-scale live run.
**Total live requests this session: 8** (2 keyword probes + 3 category scrapes + 1 review probe×2 + fixtures) — all ≥2–3 s apart, robots-guarded, no login-walled content.

---

## Verdicts

| Surface | Status | Yield (1 page) |
| ------- | ------ | -------------- |
| `/find/rtx?page=1` (gpu) | ✅ 200, cache-parsed | 52 products |
| `/find/ddr5?page=1` (ram) | ✅ 200, cache-parsed | 33 products |
| `/find/nvme?page=1` (ssd) | ✅ 200, cache-parsed | 34 products |
| `{product}/review` | ✅ 200, cache-parsed | 1 review (product has 1) |

**The 100+ listings objective is met** (119 products) at minimal scale.

## Key findings (all encoded in code + tests)

1. **DOM selectors are dead; the Apollo cache is the source.** Product cards
   render server-side with obfuscated class names and no field-level
   test-ids. `window.__cache` holds full entities
   (`searchProductV5Product{ID}` → price (incl. `original`!), shop, rating,
   `meta.countReview`, category breadcrumb). Both scrapers now parse it.
2. **Keyword noise.** Searching "gpu" returns holders/cables/books. Fix:
   chip-level keywords (config `search_keywords`: rtx / ddr5 / nvme) +
   breadcrumb filter (`vga-card`, `ram-komputer`, `media-penyimpanan-data/ssd`)
   + accessory/laptop exclusion patterns.
3. **Default ratings.** Unrated products ship `rating=5.0, countReview=0`.
   `DataPreprocessor.nullify_unrated_ratings()` nullifies them so the DSS
   rating criterion isn't inflated.
4. **`original_price` is available** in the cache (`price.original`) — the
   previously dead `discount_depth` feature now has data.
5. **Review pages are cache-rendered too** — `productrevGetProductReviewList`
   → `reviewListPDPType{feedbackID}` entities (message, rating, timestamp,
   user, likes, `hasNext`/`totalReviews`). The guessed DOM selectors were
   replaced.
6. **No bot challenge encountered** — the single "captcha" marker on pages
   is a reCAPTCHA *site key* in a JS config blob, not an interstitial.

## Data quality notes for the analysis phase

- `review_count`/`rating` on find pages reflect the *search snapshot*;
  per-product review pages are the authoritative source (verified: a
  product's review page exposes rating aggregates + review list).
- Most page-1 products have 0 reviews (new RTX-50-series listings) — the
  review corpus will grow as `fetch_reviews` runs across the catalog.
- Dedup by `product_id` (products) / `review_text+review_date` (reviews) is
  active in the scrapers.

## Compliance ledger

- All fetches: `/find/*` and `/*\/review` — both explicitly allowed by the
  committed Tokopedia snapshot; `Crawl-delay` honoured (our 2–3 s ≥ 1 s for
  Shopee; Tokopedia declares none).
- Shopee and Blibli were **not** touched in this session (Shopee: anti-bot
  risk, deferred; Blibli: search+reviews disallowed, products-only path
  untested live).
