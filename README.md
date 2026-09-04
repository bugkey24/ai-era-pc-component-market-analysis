<p align="center">
  <a href="https://github.com/bugkey24/ai-era-pc-component-market-analysis">
    <img src="https://img.shields.io/badge/AI--Era--PC--Market--Analysis-1.3.1-blue?style=for-the-badge" alt="Version Badge" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge" />
  <img src="https://img.shields.io/badge/Platform-Google%20Colab-orange?style=for-the-badge&logo=googlecolab&logoColor=white" alt="Colab Badge" />
  <img src="https://img.shields.io/badge/License-MIT--Next-green?style=for-the-badge" alt="License Badge" />
  <a href="https://github.com/bugkey24/ai-era-pc-component-market-analysis/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/bugkey24/ai-era-pc-component-market-analysis/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI Status" />
  </a>
  <a href="https://github.com/bugkey24/ai-era-pc-component-market-analysis">
    <img src="https://img.shields.io/github/stars/bugkey24/ai-era-pc-component-market-analysis?style=for-the-badge&logo=github" alt="GitHub Stars" />
  </a>
</p>

<h1 align="center">AI-Driven Market Analysis for Computer Component Price Surge</h1>

<p align="center">
  <strong>Smart Decision Support System for Hardware Procurement in the AI Era</strong>
</p>

<p align="center">
  <a href="./docs/01-overview.md">Overview</a> | <a href="./docs/02-architecture.md">Architecture</a> | <a href="./docs/03-methodology.md">Methodology</a> | <a href="./docs/04-data-collection.md">Data</a> | <a href="./docs/05-results-and-checklist.md">Results</a> | <a href="./docs/06-timeline.md">Timeline</a> | <a href="./docs/07-references.md">References</a> | <a href="./docs/08-git-workflow.md">Git Workflow</a> | <a href="./CHANGELOG.md">Changelog</a> | <a href="./LICENSE">License</a>
</p>

## Problem

The AI boom has diverted semiconductor production away from consumer-grade components, causing GPU, RAM, and SSD prices in Indonesia to surge 100-300%. Traditional purchasing decisions no longer work. This project builds a Decision Support System (DSS) to answer:

- **Why** have prices increased over 100%?
- **When** will prices normalize?
- **What** is the optimal purchasing strategy for my needs and risk tolerance?

## Results (live experiments, 2026-09-04)

Collected **320 real product listings** (GPU/RAM/SSD) and a **64-review
corpus** from Tokopedia in robots-guarded requests — full findings in
[docs/09-live-experiment-results.md](docs/09-live-experiment-results.md):

| Metric | GPU | RAM | SSD |
| ------ | --- | --- | --- |
| Median price (IDR) | 9,918,000 | 8,670,000 | 3,388,000 |
| AHP-TOPSIS best-value pick | MSI RTX 5050 Ventus 2X 8GB (Rp 9.0M) | V-GeN Platinum Rescue DDR5 (Rp 2.1M) | V-GeN Hyper Pro NVMe (Rp 2.0M) |
| Price-normalization outlook | base scenario: **2027-2028** (expected normalized price Rp 8.59M vs current Rp 5.4M median) | | |

Sentiment on the real corpus: 63 positive / 1 neutral / 0 negative; held-out
accuracy **not measurable** (e-commerce reviews skew ~all-positive) — honest
reporting, path to the >75% criterion documented.

## Approach

| Phase | Method | Purpose |
| ----- | ------ | ------- |
| **Data Collection** | Web scraping (Tokopedia, Shopee, Blibli) | 100+ product listings across GPU, RAM, SSD |
| **Preprocessing** | Pandas pipeline with outlier removal & feature engineering | Clean, analysis-ready dataset |
| **Statistical Analysis** | Descriptive stats, correlation, trend analysis | Identify price patterns and drivers |
| **Sentiment Analysis** | SVM classifier on product reviews (Indonesian NLP) | Consumer sentiment per aspect (price, performance, quality) |
| **Decision Modeling** | AHP-TOPSIS hybrid | Rank top products by weighted multi-criteria score |
| **Prediction** | Scenario modeling (bear / base / bull) | Price normalization timeline |

## Tech Stack

- **Scraping:** Requests + BeautifulSoup (static), Selenium (dynamic JS)
- **Data:** Pandas, NumPy
- **NLP/ML:** NLTK, scikit-learn (LinearSVC, TF-IDF)
- **Decision Support:** Custom AHP-TOPSIS implementation
- **Visualization:** Matplotlib, Seaborn, WordCloud
- **Environment:** Google Colab

## Project Structure

```
├── src/
│   ├── scrapers/          # BaseScraper + platform implementations (products & reviews)
│   │                      # + RobotsGuard: RFC 9309 compliance gate on every fetch
│   ├── preprocessing/     # DataPreprocessor, FeatureEngineer
│   ├── analysis/          # StatisticalAnalyzer, SentimentAnalyzer, NormalizationPredictor
│   ├── dss/               # AHPProcessor, TOPSISProcessor
│   ├── visualization/     # Visualizer
│   ├── pipeline.py        # 7-phase orchestrator
│   └── utils/             # Logger, config loading
├── tests/                 # 166 offline tests (pytest, CI-gated, 82% coverage)
├── notebooks/             # main_pipeline.ipynb (Colab entry point)
├── data/snapshot/         # committed real experiment data (no scraping needed)
├── data/raw/              # fresher local scrape output (gitignored)
├── data/processed/        # Cleaned datasets
├── outputs/               # Charts, rankings, statistics.json, prediction.json
├── docs/                  # Detailed documentation + compliance/ + results
├── config.yaml            # Centralized configuration
├── requirements.txt       # Runtime dependencies
└── requirements-dev.txt   # Test/CI tooling
```

## Documentation

| Document | Contents |
| -------- | -------- |
| [docs/01-overview.md](docs/01-overview.md) | Executive summary, objectives, scope |
| [docs/02-architecture.md](docs/02-architecture.md) | Technical architecture, class definitions, design principles |
| [docs/03-methodology.md](docs/03-methodology.md) | Step-by-step methodology for all 6 phases |
| [docs/04-data-collection.md](docs/04-data-collection.md) | Scraping targets and platform-specific code |
| [docs/05-results-and-checklist.md](docs/05-results-and-checklist.md) | Expected results, checklist, success criteria, risks |
| [docs/06-timeline.md](docs/06-timeline.md) | 4-week implementation timeline |
| [docs/07-references.md](docs/07-references.md) | References, required libraries, Colab setup |
| [docs/08-git-workflow.md](docs/08-git-workflow.md) | Branching strategy, commit conventions, merge rules |
| [docs/09-live-experiment-results.md](docs/09-live-experiment-results.md) | Live experiment results: collection, statistics, sentiment, ranking, prediction |
| [docs/10-running-guide.md](docs/10-running-guide.md) | How to run — Colab-first, local setup, collection mode, troubleshooting |
| [docs/compliance/README.md](docs/compliance/README.md) | robots.txt snapshots + per-platform scraping verdicts |
| [docs/compliance/live-validation-2026-09-04.md](docs/compliance/live-validation-2026-09-04.md) | Live-collection audit: filters, robots re-verification, corrections |
| [docs/compliance/final-validation-v1-2-0.md](docs/compliance/final-validation-v1-2-0.md) | Formal success-criteria validation |

## Getting Started

**Google Colab (recommended):** open
[`notebooks/main_pipeline.ipynb`](notebooks/main_pipeline.ipynb) in
[Colab](https://colab.research.google.com) and run all cells — the real
experiment data ships in `data/snapshot/`, so no scraping is required
(≈3 minutes, CPU runtime). Full instructions including collection mode:
[docs/10-running-guide.md](docs/10-running-guide.md).

<details>
<summary>Local setup</summary>

```bash
git clone https://github.com/bugkey24/ai-era-pc-component-market-analysis.git
cd ai-era-pc-component-market-analysis
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/        # 166 tests
```

</details>

## Configuration

All settings are centralized in `config.yaml` — scraping parameters, preprocessing options, sentiment model config, DSS criteria weights, and visualization styles.

## License

Academic / Research use.
