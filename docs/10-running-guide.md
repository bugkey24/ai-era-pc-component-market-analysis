<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-10_Running--Guide-green?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./04-data-collection.md">Data Collection</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a> | <a href="./08-git-workflow.md">Git Workflow</a> | <a href="./09-live-experiment-results.md">Live Results</a>
</p>

# Running the Project

---

## 1. Two ways to run

| Mode | What it does | Data source | Live requests |
| ---- | ------------ | ----------- | ------------- |
| **Analysis mode** (recommended default) | Runs the full pipeline — preprocessing, statistics, sentiment, AHP-TOPSIS, prediction, charts — on the committed dataset | `data/snapshot/` (ships with the repo) | **Zero** |
| **Collection mode** | Scrapes fresh data from Tokopedia, then optionally review pages | Live web | Yes (rate-limited, robots-guarded) |

Both modes are exercised by the same code; the notebook covers analysis
mode end-to-end.

---

## 2. Google Colab (recommended)

Open [`notebooks/main_pipeline.ipynb`](../notebooks/main_pipeline.ipynb)
in Colab (GitHub: *File → Upload notebook*, or paste the repo URL in
Colab's *GitHub* tab). Then:

```python
# Cell 1 handles everything automatically when IN_COLAB is true:
#   - mounts Google Drive
#   - clones this repository
#   - installs requirements.txt
#   - downloads NLTK stopwords
```

Run all cells top-to-bottom (`Runtime → Run all`). CPU runtime is
sufficient; total runtime ≈ 2–3 minutes.

### Colab compatibility notes

- **Python ≥ 3.9** — Colab's current runtime satisfies this.
- The notebook **needs no network access in analysis mode**: the real
  experiment dataset ships in `data/snapshot/`, so results reproduce
  exactly (247 products, live TOPSIS ranking embedded in the outputs).
- `pip install -r requirements.txt` covers everything; Selenium and its
  driver management are only needed for collection mode.
- Google Drive mount is optional — it is only used to persist
  `outputs/` between sessions. Decline the mount dialog if you do not
  need persistence.
- NLTK downloads `stopwords` quietly at setup; if the download fails
  offline, `SentimentAnalyzer` falls back to built-in stopword lists.

### Colab collection mode (optional, cautious)

Cell 4 (Option B) enables live scraping. Rules of engagement:

1. Re-read [`compliance/README.md`](./compliance/README.md) first — robots
   rules change; our snapshots are dated 2026-09-03.
2. Keep `max_pages` small (1–3) and `delay ≥ 2.0` s (config defaults).
3. Tokopedia only, to start: its robots explicitly allows `/find/` and
   `/review` surfaces. Shopee carries anti-bot risk; Blibli's search and
   review surfaces are robots-disallowed.
4. Every request passes `RobotsGuard` (fail-closed) — if robots.txt is
   unreachable, fetching is blocked rather than guessed.

---

## 3. Local machine

```bash
git clone https://github.com/bugkey24/ai-era-pc-component-market-analysis.git
cd ai-era-pc-component-market-analysis

python -m venv .venv
.venv\Scripts\activate            # Windows (bash: source .venv/bin/activate)
pip install -r requirements.txt -r requirements-dev.txt

python -m pytest tests/           # 160 tests
python -m pytest --cov=src        # 82% coverage
```

Run the pipeline programmatically (analysis mode):

```python
import pandas as pd
from src import PipelineOrchestrator

pipeline = PipelineOrchestrator("config.yaml")
pipeline.data = pd.read_csv("data/snapshot/tokopedia_products.csv")  # skip scraping
pipeline.data = pipeline._run_preprocessing()
pipeline.stats = pipeline._run_statistics()
pipeline._run_sentiment()       # trains if data/raw/reviews_*.csv exist
pipeline.ranking = pipeline._run_dss()
pipeline._run_prediction()
pipeline._run_visualisation()
pipeline.save_results()
```

Or run the notebook locally with Jupyter — it detects `IN_COLAB = False`
and skips the Drive/clone steps.

---

## 4. Configuration

All behaviour is centralized in [`config.yaml`](../config.yaml):
scraping targets and keywords, robots-guard settings, preprocessing
options, sentiment model, DSS criteria/weights, visualization style,
logging. See [`docs/02-architecture.md`](./02-architecture.md) §7 for the
annotated config.

---

## 5. Troubleshooting

| Symptom | Cause | Fix |
| ------- | ----- | --- |
| `ModuleNotFoundError: src` when running scripts | project root not on `sys.path` | run from the repo root, or `sys.path.insert(0, project_root)` |
| `RobotsGuard` blocks every URL | robots.txt unreachable + `fail_open: false` | check connectivity; snapshots in `docs/compliance/robots/` are used first and avoid the network entirely |
| Notebook generates synthetic data | snapshot CSVs missing | ensure `data/snapshot/*.csv` exists (they ship with the repo) |
| `ValueError: corpus contains a single class` | review corpus all-positive | expected with small corpora; the pipeline skips training and logs it — collect more/broader reviews |
| Selenium driver errors | Chrome/driver mismatch | Selenium Manager (built-in ≥ 4.6) resolves drivers; verify Chrome is installed |
