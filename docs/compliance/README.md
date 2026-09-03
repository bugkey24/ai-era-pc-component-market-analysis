# Scraping Compliance — robots.txt Analysis

**Snapshot date:** 2026-09-03
**Source files:** `tokopedia.robots.txt`, `shopee.robots.txt`, `blibli.robots.txt` (this directory)
**Governing agent:** each platform's rules for `User-agent: *` (our scrapers identify with a custom UA, which falls under `*`)

> Re-snapshot robots.txt before every live scraping run — platform rules change.
> This analysis maps each rule to our configured scraping targets in `config.yaml`.
> Note: snapshots are whitespace-normalized (pre-commit); rule lines are untouched.

---

## Verdict Summary

| Platform | Product listing | Product detail | Reviews | Verdict |
| -------- | --------------- | -------------- | ------- | ------- |
| **Tokopedia** | ✅ Allowed (via `/find/` path) | ✅ Allowed (default-permit) | ✅ **Explicitly allowed** | **Primary platform** — products + reviews |
| **Shopee** | ⚠️ Letter-of-robots allowed, `Crawl-delay: 1` | ✅ Allowed | ⚠️ Fragment-based, ungoverned | **Risky** — anti-bot/login walls in practice |
| **Blibli** | ❌ **Disallowed** (`/search`, `/cari/*`) | ✅ Allowed (`/p/*$`) | ⚠️ No sanctioned review surface (see correction note) | **Products only, no reviews, no search** |

---

## Platform Detail

### Tokopedia (`tokopedia.robots.txt`)

| Our target | Rules | Status |
| ---------- | ----- | ------ |
| Product search — `config.yaml` uses `/search?q={category}` | `Disallow: /search?*` (L93), `Disallow: /search/*` (L94) | ❌ **Current scraper URL violates robots** |
| Product search — alternative `/find/{category}?page=N` | `Allow: /find/*?page` (L8) | ✅ **Migrate the scraper to this path** |
| Review pages — `{product-url}/review` | `Allow: /*/review` (L3), `Allow: /*/*/review` (L4) | ✅ Explicitly permitted — and a dedicated `review-index.xml` sitemap signals crawlers are welcome |
| Sitemaps | `products-index-*.xml`, `review-index.xml` (L133-144) | ✅ Sanctioned discovery route |

**Action:** rewrite `TokopediaScraper._build_search_url` from `/search?q=` to `/find/{category}?page=`; keep reviews on Tokopedia only.

### Shopee (`shopee_robots.txt`)

| Our target | Rules (`User-agent: *`, L103+) | Status |
| ---------- | ------------------------------ | ------ |
| Search — `/search?keyword=gpu` | Not disallowed for `*` (only `/search*searchPrefill` L119); `Crawl-delay: 1` (L104) | ⚠️ Robots-legal, but note the Googlebot section disallows many `/search*` variants — the intent is restrictive |
| Product pages — `*-i.{shopId}.{itemId}` | Only `*-i.*/similar` disallowed (L116) | ✅ |
| Reviews | Rendered via `#ratings` URL fragment — robots.txt does not govern fragments | ⚠️ Ungoverned territory |
| Rate limit | `Crawl-delay: 1` | ✅ Our `delay: 2.0` is compliant |

**Action:** compliant on paper; expect login-walls/anti-bot in practice (independent of robots.txt). Deprioritize; never scrape behind a login wall regardless of robots.

### Blibli (`blibli_robots.txt`)

| Our target | Rules | Status |
| ---------- | ----- | ------ |
| Search — `/search/{category}` (config) and `/cari/*` | `Disallow: /search` (L39), `Disallow: /search?*` (L40), `Disallow: /cari/*` (L15) | ❌ **Disallowed — stop using search-based discovery** |
| Product detail — `/p/{slug}-{sku}` | `Allow: /p/*$` (L3) — clean URLs without query strings | ✅ Primary allowed surface |
| Review pages — `{product}/reviews` | `Disallow: /p/*/pr*` (L54) matches `/p/{slug}/product-reviews`; a literal `/reviews` segment is **not** matched by any rule | ⚠️ Our review URL is an unvalidated guess; the platform publishes no review sitemap and no explicit review `Allow` (contrast Tokopedia) |
| Discovery | `sitemap: .../blibli-product-curated-1.xml` (L108); category pages `/c/...` not disallowed for `*` | ✅ Use sitemap / category pages instead of search |

**Action:** disable `BlibliReviewScraper` from the active registry path; rework Blibli product discovery to category pages or sitemap entries; respect `/p/*$` (no query params on product URLs).

> **Correction note (2026-09-03, test-driven):** an earlier draft of this
> table claimed `/p/*/pr*` blocks literal `/reviews` URLs. The RFC 9309
> engine added in `feature/robots-compliance` proved that wrong — the rule
> matches `pr…` segments (`product-reviews`), not `re…`. Blibli reviews stay
> **gated off** (`robots_permitted = False`) on conservative grounds: no
> sanctioned review surface is known, no explicit `Allow` exists, and the
> platform may serve review content through disallowed `pr*` paths.

---

## Compliance Requirements Going Forward

1. **Programmatic robots check** — ✅ implemented: `RobotsGuard`
   (`src/scrapers/robots_guard.py`) runs an RFC 9309 longest-match engine
   against the snapshots in this directory (live fetch as fallback,
   fail-closed on unreachable); both scrape loops consult it before every
   fetch and log+skip disallowed URLs.
2. **Tokopedia-only reviews** — the review objective (sentiment analysis) is served exclusively by Tokopedia, whose robots explicitly permits reviews.
3. **Rate limits** — delays stay at or above each platform's `Crawl-delay` (Shopee: ≥1 s; project default 2 s).
4. **No login-walled content** — robots compliance does not override authentication boundaries.
5. **Re-verify before each run** — robots.txt files here are snapshots; live re-checks are mandatory.
