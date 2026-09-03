<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market--Analysis-1.0-blue?style=for-the-badge" alt="Version Badge" />
  <img src="https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge" />
  <img src="https://img.shields.io/badge/Platform-Google%20Colab-orange?style=for-the-badge&logo=googlecolab&logoColor=white" alt="Colab Badge" />
  <img src="https://img.shields.io/badge/License-MIT--Next-green?style=for-the-badge" alt="License Badge" />
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
- **Visualization:** Matplotlib, Seaborn, Plotly, WordCloud
- **Environment:** Google Colab

## Project Structure

```
├── src/
│   ├── scrapers/          # BaseScraper + platform implementations
│   ├── preprocessing/     # DataPreprocessor, FeatureEngineer
│   ├── analysis/          # StatisticalAnalyzer, SentimentAnalyzer
│   ├── dss/               # AHPProcessor, TOPSISProcessor
│   ├── visualization/     # Visualizer
│   └── utils/             # Logger, helpers
├── notebooks/             # Colab notebooks
├── data/raw/              # Scraped CSVs per platform/category
├── data/processed/        # Cleaned datasets
├── outputs/               # Visualizations, rankings, sentiment results
├── docs/                  # Detailed documentation
├── config.yaml            # Centralized configuration
└── requirements.txt       # Python dependencies
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

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Run in Google Colab (recommended)
# Open notebooks/main_pipeline.ipynb
```

## Configuration

All settings are centralized in `config.yaml` — scraping parameters, preprocessing options, sentiment model config, DSS criteria weights, and visualization styles.

## License

Academic / Research use.
