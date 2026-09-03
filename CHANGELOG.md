# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
- `DataPreprocessor.handle_missing` — added `numeric_only=True` to `median()`.

### Removed

- `docs/PROJECT.md` — content fully covered by modular docs.
- `docs/index.md` — `README.md` now serves as the document index.
