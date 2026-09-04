# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.3.0] - 2026-09-04

### Changed

- **Live-scraped snapshot refresh:** 375 products (GPU 101, RAM 91, SSD 183)
  and 64 real reviews from 29 products — zero synthetic data.
- **Visualizer:** price trends now 1×N subplots with log-scale Y (RAM/SSD
  visible next to GPU); ranking chart shows product names (top 10) with
  score labels; `show` toggle renders figures inline before closing them.
- **Pipeline:** ranking enriched with product name/category/price; new
  data-requirements check against `config.yaml` thresholds.
- **Config:** `scraping.max_pages` 5→8, new `review_max_pages: 4`, new
  `data_requirements` section.
- **Notebook:** charts render inline in Colab (removed forced Agg backend,
  fixed figure-close-before-show); export cell previews the cleaned dataset
  and lists output files with sizes; conclusions updated to live-scraped
  stats (GPU median 12.09M, RAM 8.29M, SSD 3.38M).

### Fixed

- Colab ran stale code: the notebook cloned the repo's default branch
  (`main`) while all fixes lived on `develop`, so every run executed the
  old seaborn-based `plot_ranking_bar_chart` and failed with
  ``Could not interpret value `Alternative` for `y``` once `df_ranked`
  (which has no `Alternative` column) was passed in. Resolved by merging
  `develop` → `main`.

### Docs

- Mermaid flowcharts replace ASCII diagrams (`docs/02`, `docs/08`); charts
  embedded in `docs/09`; honest sentiment assessment (63 positive / 1
  negative → accuracy not measurable on a single-class test set);
  `scripts/expand_reviews.py` added for future review collection.

---

## [1.2.3] - 2026-09-03

### Fixed

Two defects surfaced by a user's Colab Option B run:

- **Stale clone:** cell 1's `git clone` failed silently when the target
  directory already existed (re-used runtime / Drive state), so runs kept
  executing old repo code. Cell 1 now pulls when the clone exists and
  prints the checked-out commit hash for verification.
- **Dataset poisoning:** a 0-row live scrape overwrote the working `data`
  frame, crashing section 6 (`Cannot describe a DataFrame without
  columns`). Option B is now a guarded `try_live_scrape()` — empty
  results never replace the dataset — and is **commented out by
  default**, so *Run all* performs pure analysis on the snapshot.

### Changed

- Notebook re-executed headless: 23 cells, zero errors, 247-row snapshot
  confirmed as the data source.

---

## [1.2.2] - 2026-09-03

### Context

Live scraping attempted from Google Colab (datacenter IPs) failed exactly
as documented: Tokopedia timeouts, Shopee missing-Chrome, Blibli 403 —
the pipeline degraded gracefully to 0 rows. This release hardens the code
for that environment and makes the notebook honest about it.

### Added

- **Shared retry module** (`src/scrapers/retry.py`) — product scrapers
  (`TokopediaScraper`, `BlibliScraper`) now retry connection errors,
  timeouts, 5xx and 429 with exponential backoff (previously one timeout
  ended a whole category; only the review scrapers retried). 4xx fails
  fast — backing off cannot heal a blocked URL.
- Notebook Option B is **self-contained** (imports inside the cell — no
  more `NameError` from cell-order) and carries explicit warnings about
  datacenter-IP expectations per platform.
- `docs/10` troubleshooting rows for every error observed from Colab:
  Tokopedia timeouts, Shopee `session not created` (+ Chrome install
  snippet), Blibli 403.

### Changed

- `BaseReviewScraper._request_with_retry` delegates to the shared module
  (behaviour unchanged; tests re-pointed).

---

## [1.2.1] - 2026-09-03

### Added

- **Committed real-data snapshot** (`data/snapshot/`) — 247-product dataset
  + 42-review corpus travel with the repo, so notebook/Colab runs present
  the actual live-experiment data instead of a synthetic fallback
  (gitignore exception added).
- `docs/09-live-experiment-results.md` — full live-experiment results:
  collection stats, statistical findings, sentiment reality (skewed
  corpus, accuracy honestly unmeasurable), AHP-TOPSIS top-10 on real
  data, normalization prediction.
- `docs/10-running-guide.md` — how to run: Colab-first (auto-setup cell,
  compatibility notes, collection-mode rules of engagement), local setup,
  pipeline API usage, troubleshooting table.

### Changed

- Notebook data-loading cell prefers `data/snapshot/*products*.csv`,
  falls back to fresher `data/raw` output, synthetic sample last; TOPSIS
  cell resolves criterion columns adaptively (live cache has `seller_tier`
  but no `seller_rating`/`followers` — demo data is the reverse).
  Re-executed headless on the real snapshot: 23 cells, zero errors,
  real TOPSIS ranking embedded.
- All documentation aligned to the shipped state: docs/04 rewritten around
  the live-validated cache-based collection (dead DOM selectors removed),
  docs/05 checklist at actual progress with pointers to real results,
  doc-09/10 cross-links in every nav bar, stale test counts corrected
  (160), version badge bumped.
- Cleaned: `notebooks/.gitkeep` removed (notebook exists).

---

## [1.2.0] - 2026-09-03

### Release highlights

- **Live-validated end to end**: 247 products (3 pages × gpu/ram/ssd) and a
  42-review corpus collected from Tokopedia in ~30 rate-limited,
  robots-guarded requests; every phase of the pipeline executed on this
  real data (see `docs/compliance/final-validation-v1-2-0.md`).
- Full success-criteria validation against docs/05 with honest reporting
  of deferred items (sentiment accuracy needs a labelled corpus; seller
  metrics need detail-page enrichment).

### Added

- **Live scraping validated (Tokopedia)** — 119 products across
  gpu/ram/ssd from single-page runs (8 requests total, robots-guarded,
  ≥2 s apart). Full findings in
  `docs/compliance/live-validation-2026-09-03.md`.
- Tokopedia scrapers (products + reviews) now parse the server-rendered
  Apollo cache (`window.__cache`) instead of guessed DOM selectors —
  richer fields: numeric price, `original_price`, discount %, review
  count, shop city, clean product URL (tracking params stripped).
- Chip-level `search_keywords` (rtx/ddr5/nvme) + breadcrumb filter
  (live-verified taxonomy: `vga-card`, `ram-komputer`,
  `media-penyimpanan-data/ssd`) + accessory/laptop exclusion patterns.
- `DataPreprocessor.nullify_unrated_ratings()` — Tokopedia serves
  `rating=5.0, review_count=0` for unrated products; those defaults are
  nullified before DSS scoring.
- Review schema extended with `review_id` + `user_name`;
  `fetch_reviews` now enforces exact schema column order.
- **Robots.txt compliance layer** (`RobotsGuard`,
  `src/scrapers/robots_guard.py`) — RFC 9309 longest-match engine
  (replaces `urllib.robotparser`, which drops query strings and
  mishandles `$`-anchored rules), offline resolution from the committed
  snapshots in `docs/compliance/robots/` with live fetch as fallback,
  fail-closed on unreachable robots.txt, per-origin caching, and
  `Crawl-delay` honouring in both scrape loops. Every fetch is now
  robots-checked before being requested.
- `robots_permitted` flag on review scrapers — orchestration can skip
  robots-blocked platforms (`BlibliReviewScraper` = False).
- **Price-normalization prediction module** (`NormalizationPredictor`,
  `src/analysis/normalization_predictor.py`) — implements methodology
  Phase 6, which was documented but never built: the regression-based
  `predict_normalization` model, explicit bull/base/bear scenario
  definitions (with per-scenario investment/fab drivers matching the
  documented semantics), probability-weighted `summarize()`.
- Pipeline Phase 6: runs scenario analysis on the median price and
  persists `outputs/prediction.json` via `save_results`.
- **Review-scraping layer** — parallel `BaseReviewScraper` ABC with
  `TokopediaReviewScraper`, `BlibliReviewScraper`, `ShopeeReviewScraper`
  (Selenium), `REVIEW_SCRAPER_REGISTRY` + `get_review_scraper()` factory,
  and a shared review schema (`product_id`, `review_text`, `rating`,
  `review_date`, `helpful_count`, `source`). Unblocks the sentiment
  objective: product scrapers alone collect no review text.
- Retry with exponential backoff for static review fetching
  (methodology Phase 1, step 4) — verified via mocked-network tests.
- Review deduplication (same text + date) inside the fetch loop.
- `PipelineOrchestrator._run_sentiment` now loads `data/raw/reviews_*.csv`
  when present and trains the SVM via rating-derived weak supervision
  (≥4 → positive, ≤2 → negative, else neutral); per-product positive-rate
  is merged back as `sentiment_score`.

### Changed

- `_run_preprocessing` now runs the full FeatureEngineer chain — previously
  `weighted_rating`/`seller_trust`/`price_per_gb` never existed at pipeline
  level and the DSS silently zero-filled them. `create_discount_depth`
  wired in (data available since `original_price` capture).
- `seller_tier` (Tokopedia shop programme tier) collected as the
  `seller_reliability` criterion proxy, with fallback to `seller_trust`.
- `SentimentAnalyzer.train`: single-class corpora fail fast (a classifier
  needs two classes); skewed corpora (min class < 2 — live reality:
  41 positive / 1 negative) fit on the full data with accuracy reported
  as not measurable; `classification_report` labels pinned for
  single-class test splits.
- Test coverage measured at **82%** (1,481 statements).

- `ShopeeScraper._build_search_url`: regression introduced by the config
  `base_url` change produced `shopee.co.id?keyword=` (missing `/search`
  path); URL construction fixed and locked by a stricter test.
- `docs/04`: Tokopedia examples migrated to the robots-allowed `/find/`
  surface; `docs/07` appendices purged of removed deps (plotly,
  webdriver-manager).

### Documentation

- `docs/compliance/final-validation-v1-2-0.md` — success-criteria
  validation against docs/05 (technical + analytical), limitations ledger.
- `docs/02-architecture.md` synced to current state: review-scraping layer,
  `RobotsGuard`, `NormalizationPredictor`, 7-phase orchestrator, real file
  structure (tests/, CI, compliance dir), corrected dependency list.
- `docs/01-overview.md` deliverables reflect actual outputs.
- `docs/03-methodology.md` — Phase 1 and Phase 6 implementation-status notes.
- `docs/04-data-collection.md` — review-collection section, Blibli
  restrictions, review schema.
- `docs/05-results-and-checklist.md` — checklist ticked to actual progress.
- `docs/07-references.md` — RFC 9309 added.
- `README.md` — structure tree and docs index updated.

---

## [1.1.0] - 2026-09-03

### Added

- Full pytest suite — **90 tests** across AHP, TOPSIS, preprocessing, feature
  engineering, sentiment, scrapers (offline HTML parsing), visualizer
  (headless), and utils. Coverage of error paths and edge cases.
- `pyproject.toml` — project metadata, pytest config, ruff lint + format rules.
- `.pre-commit-config.yaml` — whitespace/yaml checks, ruff fix + format.
- GitHub Actions CI (`.github/workflows/ci.yml`) — ruff lint job + pytest with
  coverage gate (≥70%) on Python 3.10/3.11/3.12; CI badge on README.
- `notebooks/main_pipeline.ipynb` — 11-section Colab notebook covering the
  complete pipeline, **verified by headless execution**; includes an offline
  sample-data generator and a demo sentiment training set.
- `SentimentAnalyzer` now prefers NLTK stopwords (indonesian + english) with a
  graceful fallback to built-in lists when the corpus is unavailable.

### Fixed

- `requirements.txt`: added missing `scipy` (imported by
  `StatisticalAnalyzer` — hard crash before); removed unused
  `webdriver-manager`, `plotly`, `tqdm`.
- `AHPProcessor.build_pairwise_matrix`: accepts `"a/b"` fraction strings —
  YAML parses `1/3` as a *string*, so the config-driven pairwise matrix
  previously crashed on float conversion. Covered by regression tests.
- `TokopediaScraper.get_next_page_url`: appended `page=2` on first pagination
  step (previously returned `None` because no `page` param existed yet).
- `Visualizer`: resolves legacy `seaborn-v0_8-*` style names to current
  seaborn styles (dropped in seaborn ≥0.14); fixed palette-without-hue
  deprecation warnings.
- CHANGELOG: corrected `handle_missing` description to match implementation.

### Changed

- Modernized typing to PEP 585/604 (`list[str]`, `X | None`) across `src/`
  and `tests/`; removed 5 unused imports (ruff-clean: 0 findings).

---

## [1.0.0] - 2026-09-03

### Added

- Project documentation split from monolithic `PROJECT.md` into 7 modular docs.
- `docs/01-overview.md` — executive summary, objectives, scope.
- `docs/02-architecture.md` — technical architecture, class definitions, design principles.
- `docs/03-methodology.md` — detailed methodology for all 6 phases.
- `docs/04-data-collection.md` — scraping targets and platform-specific code.
- `docs/05-results-and-checklist.md` — expected results, checklist, success criteria, risks.
- `docs/06-timeline.md` — 4-week implementation timeline.
- `docs/07-references.md` — references, required libraries, Colab setup.
- Badge headers and cross-navigation links on all documentation files.
- `README.md` — project entry point with badges, overview, and doc index.
- `CHANGELOG.md` — this file.
- `docs/08-git-workflow.md` — branching strategy, commit conventions, merge rules, tagging.
- `.gitignore`, `requirements.txt`, `config.yaml`, and full directory skeleton for Git readiness.

### Changed

- `BaseScraper._build_search_url` — promoted to `@abstractmethod` on base class.
- `PipelineOrchestrator._setup_logger` — switched to named logger to avoid root pollution.
- `PipelineOrchestrator._run_scraping` — reads category from config instead of hardcoded key.

### Fixed

- `AHPProcessor.check_consistency` — added `ValueError` guard when weights not yet computed.
- `TOPSISProcessor.normalize_matrix` — added zero-norm guard to prevent division by zero.
- `TOPSISProcessor.calculate_scores` — added zero-denominator guard.
- `SentimentAnalyzer.preprocess_text` — added null/empty string guard.
- `SentimentAnalyzer.train` — filters empty strings before TF-IDF vectorization.
- `DataPreprocessor.remove_outliers` — added `std == 0` guard.
- `DataPreprocessor.handle_missing` — restricted fill to numeric columns via `select_dtypes(include=np.number)` before `median()`.

### Removed

- `docs/PROJECT.md` — content fully covered by modular docs.
- `docs/index.md` — `README.md` now serves as the document index.
