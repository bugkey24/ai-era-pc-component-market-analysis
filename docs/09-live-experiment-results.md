<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-09_Live--Results-teal?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./04-data-collection.md">Data Collection</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a> | <a href="./08-git-workflow.md">Git Workflow</a> | <a href="./10-running-guide.md">Running Guide</a>
</p>

# Live Experiment Results

**Date:** 2026-09-03 · **Platform:** Tokopedia (robots-guarded) · **Requests:** ~30 total, ≥2 s apart
Raw audit trails: [`compliance/live-validation-2026-09-03.md`](./compliance/live-validation-2026-09-03.md) · [`compliance/final-validation-v1-2-0.md`](./compliance/final-validation-v1-2-0.md)

---

## 1. Collection

| Category | Search keyword | Pages | Products kept | Noise filtered |
| -------- | -------------- | ----- | ------------- | -------------- |
| GPU | `rtx` | 3 | 99 | accessories, laptops, PCs |
| RAM | `ddr5` | 3 | 74 | motherboards, miscategorized GPUs |
| SSD | `nvme` | 3 | 74 | enclosures, cases, coolers, screws |
| **Total** | | **9** | **247** | |

Review corpus: 42 reviews from 11 of 12 stratified sample products (one 404 + one
timeout absorbed by retry/backoff). The committed snapshot
(`data/snapshot/`) contains both datasets so every notebook run reproduces
these results.

**Data quality filters verified live** (all encoded in `TokopediaScraper` +
tests): chip-level keywords instead of bare category words; breadcrumb
taxonomy (`vga-card`, `ram-komputer`, `media-penyimpanan-data/ssd`);
accessory/laptop/enclosure exclusion patterns; cross-category
miscategorization guard (a seller listed a Radeon GPU under RAM); id-based
deduplication.

---

## 2. Statistical Findings (numerical data)

| Metric | GPU | RAM | SSD |
| ------ | --- | --- | --- |
| Median price (IDR) | 14,633,000 | 8,544,500 | 3,479,000 |
| Price per GB (SSD) | — | — | Rp 3,750 median |
| Discount depth computable | — | — | 55 SKUs (original price captured) |
| Ratings | n/a* | n/a* | n/a* |

\* Find-page metadata ships `rating = 5.0, review_count = 0` for unrated
products; `nullify_unrated_ratings` nullifies these, so every product in this
snapshot is effectively unrated. True per-product rating aggregates live on
review pages (`productrevGetProductRatingAndTopics`) — the enrichment path
for the next iteration.

Other statistics produced by `StatisticalAnalyzer` in the notebook:
`describe()` (mean/median/std/quartiles/IQR/skew/kurtosis per numeric
column), Pearson correlation matrix, Shapiro-Wilk normality test on price,
per-category price dispersion (coefficient of variation), per-platform
price comparison.

---

## 3. Sentiment (42 real reviews, weak supervision)

- Class reality: **41 positive / 1 negative** — Indonesian e-commerce reviews
  skew overwhelmingly positive.
- Consequence: held-out accuracy is **not measurable** (a classifier cannot
  be evaluated on a single-class split); the model fits the full corpus and
  predicts, with `accuracy = None` reported honestly.
- Aspect sentiment (keyword-filtered): price / performance / quality /
  packaging all classified positive — consistent with the corpus skew, not
  an independent finding.
- Path to the >75% F1 criterion: broader review crawling + hand-labelled
  (or public-corpus) Indonesian review labels.

---

## 4. Decision Model Output (AHP-TOPSIS on live data)

AHP consistency ratio: **CR < 0.1** (asserted on every run). Criteria
weights: performance 0.439 · price 0.227 · future-value 0.160 · rating 0.092
· seller 0.041 · sentiment 0.041.

Top of the real-data ranking (`outputs/rankings.csv`, chart
`ranking_results.png`):

| Rank | Product | Category | Price (IDR) | Score |
| ---- | ------- | -------- | ----------- | ----- |
| 1 | CORSAIR MP600 ELITE 1TB PCIe Gen4 NVMe | ssd | 3,949,000 | 0.554 |
| 2 | VGA Zotac GeForce RTX 3050 6GB TWIN EDGE OC | gpu | 5,199,000 | 0.616 |
| 3 | KINGSTON KC3000 1024GB PCIe 4.0 | ssd | 4,330,000 | 0.552 |
| 4 | GSKILL RIPJAWS S5 BLACK DDR5 6000MHz | ram | 20,950,000 | 0.437 |

Interpretation: with ratings inert (see §2), price and value-per-capacity
dominate the ranking — the model surfaces best-value picks rather than
best-reviewed ones.

---

## 5. Price Normalization Prediction (methodology Phase 6)

Input: median collected price **Rp 8,499,000**. Output (`prediction.json`):

- Most likely scenario: **base — 2027-2028** (probability 0.5)
- Expected normalized price: **Rp 13,513,410** (probability-weighted across
  bull/base/bear)

Bull = aggressive AI investment keeps prices rising; bear = bubble bursts,
surplus fab capacity. Full scenario table in `docs/03-methodology.md` Phase 6.

---

## 6. Success Criteria Scorecard

See [`final-validation-v1-2-0.md`](./compliance/final-validation-v1-2-0.md)
for the formal assessment against `docs/05`: 4/5 technical criteria met
(sentiment accuracy deferred to labelled data), 4/4 analytical criteria met.
