<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-09_Live--Results-teal?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./04-data-collection.md">Data Collection</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a> | <a href="./08-git-workflow.md">Git Workflow</a> | <a href="./10-running-guide.md">Running Guide</a>
</p>

# Live Experiment Results

**Date:** 2026-09-04 · **Platform:** Tokopedia (robots-guarded) · **Scrape method:** Apollo cache parsing
Raw audit trails: [`compliance/live-validation-2026-09-04.md`](./compliance/live-validation-2026-09-04.md) · [`compliance/final-validation-v1-2-0.md`](./compliance/final-validation-v1-2-0.md)

---

## 1. Collection

| Category | Search keyword | Products after filters | After preprocessing |
| -------- | -------------- | ---------------------- | ------------------- |
| GPU | `rtx` | 82 | 79 |
| RAM | `ddr5` | 63 | 61 |
| SSD | `nvme` | 175 | 175 |
| **Total** | | **320** | **315** |

Raw find-page yield was **375 listings**; data-quality auditing (v1.3.1) added
name-signature filters that removed **55 misclassified or accessory listings**
(24 motherboards under RAM/SSD breadcrumbs, 19 laptops/PC-builds under GPU,
2 PCIe↔M.2 adapters, 1 storage bag, 9 other accessories) — see
[`compliance/live-validation-2026-09-04.md`](./compliance/live-validation-2026-09-04.md).

Review corpus: **64 reviews from 29 products** across all 3 categories. All reviews are real, live-scraped data — no synthetic or dummy content. The committed snapshot (`data/snapshot/`) contains both datasets so every notebook run reproduces these results.

**Data quality filters applied** (all encoded in `TokopediaScraper` + tests): chip-level keywords instead of bare category words; breadcrumb taxonomy (`vga-card`, `ram-komputer`, `media-penyimpanan-data/ssd`); accessory/laptop/motherboard/enclosure exclusion patterns; cross-category miscategorization guard; id-based deduplication.

**Platform coverage:** Only Tokopedia returned data. Shopee required Selenium (Chrome not available in this environment). Blibli returned 404 on category URLs (robots-disallowed search surface). This is expected — see `docs/10-running-guide.md` §5.

---

## 2. Statistical Findings (numerical data)

| Metric | GPU | RAM | SSD |
| ------ | --- | --- | --- |
| Products (after preprocessing) | 79 | 61 | 175 |
| Median price (IDR) | 9,918,000 | 8,670,000 | 3,388,000 |
| Mean price (IDR) | 12,033,782 | 8,815,348 | 3,879,467 |
| Price per GB (SSD) | — | — | Rp 3,820 median |
| Ratings | n/a* | n/a* | n/a* |

\* Find-page metadata ships `rating = 5.0, review_count = 0` for unrated products; `nullify_unrated_ratings` nullifies these, so every product in this snapshot is effectively unrated. True per-product rating aggregates live on review pages (`productrevGetProductRatingAndTopics`) — the enrichment path for the next iteration.

### Price Distribution

![Price Distribution by Category](../outputs/visualizations/price_trends.png)

*Subplots with log-scale Y-axis — GPU prices span Rp 2.75M–33.5M, RAM Rp 2.07M–23.6M, SSD Rp 522K–13.1M.*

### Correlation Matrix

![Feature Correlation Matrix](../outputs/visualizations/correlation_heatmap.png)

Other statistics produced by `StatisticalAnalyzer` in the notebook: `describe()` (mean/median/std/quartiles/IQR/skew/kurtosis per numeric column), Pearson correlation matrix, Shapiro-Wilk normality test on price, per-category price dispersion (coefficient of variation), per-platform price comparison.

---

## 3. Sentiment (64 real reviews, weak supervision)

- Class distribution: **63 positive / 1 neutral / 0 negative** — Indonesian e-commerce reviews skew overwhelmingly positive. This is the genuine distribution from live-scraped Tokopedia data (the single non-positive review is neutral, rating 3).
- Consequence: held-out accuracy is **not measurable** (a classifier cannot be evaluated on a single-class split); the model fits the full corpus and predicts, with `accuracy = None` reported honestly.
- Aspect sentiment (keyword-filtered): price / performance / quality / packaging — consistent with the corpus composition.
- To achieve >75% F1: collect reviews from products with genuine negative feedback (e.g., defective items, shipping issues), or use hand-labelled public Indonesian review corpora.

### Sentiment Distribution

![Sentiment Distribution](../outputs/visualizations/sentiment_distribution.png)

---

## 4. Decision Model Output (AHP-TOPSIS on live data)

AHP consistency ratio: **CR = 0.0586** (< 0.1, consistent; asserted on every run). Criteria weights: performance 0.439 · price 0.227 · future-value 0.160 · rating 0.092 · seller 0.041 · sentiment 0.041.

Top of the real-data ranking (`outputs/rankings.csv`, chart `ranking_results.png`) — the Rank column follows Score ordering exactly (v1.3.1 fixed a rank-assignment bug that could scramble the two):

![TOPSIS Ranking — Top 10 Products](../outputs/visualizations/ranking_results.png)

| Rank | Product | Category | Price (IDR) | Score |
| ---- | ------- | -------- | ----------- | ----- |
| 1 | MSI NVIDIA GEFORCE RTX 5050 8GB VENTUS 2X OC GDDR6 | gpu | 8,955,000 | 0.6792 |
| 2 | COLORFUL IGAME NVIDIA GEFORCE RTX 5050 ULTRA W DUO OC 8GB GDDR6 | gpu | 8,583,000 | 0.6778 |
| 3 | MSI VGA NVIDIA GEFORCE RTX 3050 VENTUS 2X E 6GB GDDR6 OC 3Y | gpu | 6,024,000 | 0.6778 |
| 4 | VGA PALIT GeForce RTX 5050 StormX 8GB GDDR6 | gpu | 7,499,000 | 0.6723 |
| 5 | VGA Card MSI GeForce RTX 3050 VENTUS 2X 6G OC - 6GB GDDR6 | gpu | 5,605,000 | 0.6722 |

Category best-value picks: GPU — MSI RTX 5050 Ventus 2X (Rp 8,955,000) · RAM — V-GeN Platinum Rescue DDR5 (Rp 2,067,000) · SSD — V-GeN Hyper Pro NVMe (Rp 1,989,000).

Interpretation: with ratings inert (see §2), price and value-per-capacity dominate the ranking — the model surfaces best-value picks rather than best-reviewed ones; budget GPUs lead the overall top-5.

---

## 5. Price Normalization Prediction (methodology Phase 6)

Input: median collected price **Rp 5,399,999**. Output (`prediction.json`):

- Most likely scenario: **base — 2027-2028** (probability 0.5)
- Expected normalized price: **Rp 8,585,998** (probability-weighted across
  bull/base/bear)

Bull = aggressive AI investment keeps prices rising; bear = bubble bursts,
surplus fab capacity. Full scenario table in `docs/03-methodology.md` Phase 6.

---

## 6. Success Criteria Scorecard

See [`final-validation-v1-2-0.md`](./compliance/final-validation-v1-2-0.md)
for the formal assessment against `docs/05`: 4/5 technical criteria met
(sentiment accuracy deferred to labelled data), 4/4 analytical criteria met.
