# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

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
