<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-04_Data--Collection-orange?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a> | <a href="./08-git-workflow.md">Git Workflow</a> | <a href="./09-live-experiment-results.md">Live Results</a> | <a href="./10-running-guide.md">Running Guide</a>
</p>

# Data Collection Plan

---

> **Compliance first:** robots.txt snapshots and the full per-platform
> analysis live in [`docs/compliance/`](./compliance/README.md). Status after
> live validation (2026-09-04): **Tokopedia = validated** (cache-based
> parsing, 320 products + 64 reviews — see
> [`09-live-experiment-results.md`](./09-live-experiment-results.md)) ·
> **Shopee** = robots-legal but anti-bot risk, code-validated only ·
> **Bibli** = products-only path (no search, no reviews), code-validated only.
> Every fetch passes the `RobotsGuard` compliance gate (fail-closed).

---

## Platform Overview

| Platform  | Target Category | Scraping Method          | Difficulty | Live status |
| --------- | --------------- | ------------------------ | ---------- | ----------- |
| Tokopedia | GPU, RAM, SSD   | Requests + Apollo-cache parsing | Medium | ✅ validated |
| Shopee    | GPU, RAM, SSD   | Selenium (dynamic)       | High       | ⚠️ not run live |
| Blibli    | GPU, RAM, SSD   | Requests + BeautifulSoup | Medium     | ⚠️ not run live |

---

## 6.1 Tokopedia — ✅ live-validated (2026-09-04)

**Data source: the embedded Apollo cache, not DOM selectors.** Product
cards render server-side but with obfuscated class names and no
field-level test-ids; the page embeds `window.__cache`, an Apollo
normalized JSON store holding complete entities
(`searchProductV5Product{ID}` → name, clean URL, numeric price +
`original_price`, discount %, rating, `meta.countReview`, shop
name/tier/city, category breadcrumb). Reviews pages carry the same
pattern (`productrevGetProductReviewList` → `reviewListPDPType{ID}`).

```
URL: https://www.tokopedia.com/find/{keyword}?page=1   (robots: Allow: /find/*?page)
Reviews: {product-url}/review                          (robots: Allow: /*/review)
Parse:   window.__cache → resolve id-references → product/review dicts
```

> ⚠️ The legacy `/search?q=` surface is robots-DISALLOWED — never use it.
> Bare category words ("gpu") return accessories and books; config
> `search_keywords` maps categories to chip-level keywords
> (`gpu→rtx`, `ram→ddr5`, `ssd→nvme`), and a breadcrumb filter plus
> name-signature exclusion patterns for accessories, laptops, PC builds,
> motherboards, and adapters (all live-verified — see
> [`09-live-experiment-results.md`](./09-live-experiment-results.md)) remove the rest.

Yield: 320 products (from 375 raw listings; 55 misclassified/accessory
listings filtered) across `max_pages=8` × 3 categories; 64-review corpus
from 29 products.

---

## 6.2 Shopee — ⚠️ robots-legal, not run live (anti-bot risk)

> Code-validated offline only. Robots' `User-agent: *` section does not
> disallow plain search and sets `Crawl-delay: 1` (our 2 s delay complies),
> but real browsing typically hits login walls/verification — do not scrape
> behind authentication regardless of robots.

**Structure:**

```
URL: https://shopee.co.id/search?keyword=gpu
HTML: div[data-testid="product-item"]
Price: span[data-testid="product-price"]
Dynamic Content: Requires Selenium
```

**Implementation:**

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_shopee(category):
    driver = webdriver.Chrome()
    driver.get(f"https://shopee.co.id/search?keyword={category}")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="product-item"]'))
    )

    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    products = []
    items = driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-item"]')
    for item in items:
        product = extract_shopee_product(item)
        products.append(product)

    driver.quit()
    return pd.DataFrame(products)
```

---

## 6.3 Blibli

**Structure (products-only path; code-validated, not yet run live):**

```
URL: https://www.blibli.com/c/{category}     (robots-allowed category pages)
Product detail: /p/{slug}-{sku}              (allowed, no query params)
Search: NOT PERMITTED — /search and /cari/* are robots-disallowed
Reviews: NOT SANCTIONED — no allowed review surface; scraper gated off
```

---

## Review Collection (Tokopedia — validated)

Reviews feed the sentiment phase. **Only Tokopedia's robots.txt explicitly
permits review crawling** (`Allow: /*/review`, plus a published
`review-index.xml` sitemap) — see [`compliance/README.md`](./compliance/README.md).
Live yield: 64 reviews from 29 sampled products
([`09-live-experiment-results.md`](./09-live-experiment-results.md)).

**Review schema** (`REVIEW_SCHEMA`, shared by all review scrapers):

```python
{
    'product_id': 'string',
    'review_id': 'string (platform feedback id)',
    'review_text': 'string',
    'rating': 'float (0-5)',
    'review_date': 'string (platform format)',
    'helpful_count': 'integer',
    'user_name': 'string',
    'source': 'platform name'
}
```

Scraped reviews are saved as `data/raw/reviews_{platform}_{category}.csv`;
the pipeline's sentiment phase auto-loads them (`reviews_*.csv` glob) and
trains via rating-derived weak supervision (≥4 → positive, ≤2 → negative,
else neutral). For production-grade accuracy, replace with hand-labelled
reviews.
