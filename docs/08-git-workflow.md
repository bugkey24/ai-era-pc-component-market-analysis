<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-08_Git--Workflow-indigo?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./04-data-collection.md">Data Collection</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a>
</p>

# Git Workflow & Branching Strategy

---

## 1. Model: Simplified Git Flow

This project uses a lightweight **Git Flow** variant suited for a small team building toward a single deliverable (Colab notebook + report). It balances structure with speed.

**Repository:** [github.com/bugkey24/ai-era-pc-component-market-analysis](https://github.com/bugkey24/ai-era-pc-component-market-analysis)

```
main (production-ready, tagged releases)
 │
 ├── develop (integration branch — all features merge here)
 │    │
 │    ├── feature/scraper-tokopedia
 │    ├── feature/scraper-shopee
 │    ├── feature/preprocessing-pipeline
 │    ├── feature/sentiment-analyzer
 │    ├── feature/ahp-topsis-dss
 │    ├── feature/visualizations
 │    └── docs/branching-strategy
 │
 └── release/v1.0.0 (optional — only if staging before final)
```

---

## 2. Branch Types & Naming

| Type | Prefix | Example | Purpose |
| ---- | ------ | ------- | ------- |
| **Production** | *(none)* | `main` | Stable, deployable code |
| **Development** | *(none)* | `develop` | Integration branch for next release |
| **Feature** | `feature/` | `feature/sentiment-analyzer` | New functionality |
| **Bugfix** | `bugfix/` | `bugfix/price-parsing-error` | Non-critical bug fixes |
| **Hotfix** | `hotfix/` | `hotfix/scraping-timeout` | Urgent production fixes |
| **Docs** | `docs/` | `docs/branching-strategy` | Documentation-only changes |
| **Release** | `release/` | `release/v1.0.0` | Release preparation & stabilization |

### Naming Rules

- Use **lowercase kebab-case**: `feature/preprocessing-pipeline`
- Keep names short but descriptive (2-4 words)
- Prefix with the scope when useful: `feature/dss-ahp-processor`

---

## 3. Branch Lifecycle

### 3.1 Feature Branch

```bash
# Start a feature
git checkout develop
git pull origin develop
git checkout -b feature/sentiment-analyzer

# Work, commit often
git add src/analysis/sentiment_analyzer.py
git commit -m "feat(analysis): add SentimentAnalyzer with SVM training"

# Push and open a Pull Request
git push -u origin feature/sentiment-analyzer
```

### 3.2 Merge via Pull Request

- Every feature merges into `develop` through a **Pull Request** (or Merge Request).
- PR must be reviewed before merge (self-review is fine for solo work).
- Use **squash merge** to keep `develop` history clean:

```
feature/sentiment-analyzer  ──squash merge──▶  develop
```

### 3.3 Cleanup

```bash
# After merge, delete the feature branch locally and remotely
git checkout develop
git pull origin develop
git branch -d feature/sentiment-analyzer
git push origin --delete feature/sentiment-analyzer
```

---

## 4. Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/) to keep history machine-readable and consistent.

### Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types

| Type | When to Use |
| ---- | ----------- |
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Code restructuring, no behavior change |
| `test` | Adding or updating tests |
| `chore` | Build, CI, dependencies, config |
| `data` | Data files, CSVs, scraped output |

### Examples

```
feat(scrapers): add TokopediaScraper with pagination support

fix(dss): guard against division by zero in TOPSIS scores

docs: add branching strategy document (08-git-workflow.md)

chore: add .gitignore and requirements.txt

data: add raw scraped dataset for GPU category
```

---

## 5. Merge Strategy

| From | To | Strategy | Reason |
| ---- | -- | -------- | ------ |
| `feature/*` | `develop` | **Squash merge** | One clean commit per feature |
| `bugfix/*` | `develop` | **Squash merge** | Same as feature |
| `hotfix/*` | `main` + `develop` | **Merge commit** | Preserve hotfix traceability |
| `release/*` | `main` | **Merge commit** | Mark release points |
| `docs/*` | `develop` | **Squash merge** | Clean doc history |

### Rules

- **Never force-push** to `main` or `develop`.
- **Never commit directly** to `main`.
- Keep `develop` always in a green (buildable) state.

---

## 6. Tagging & Releases

Tag releases on `main` using semantic versioning.

```bash
# After merging release into main
git checkout main
git tag -a v1.0.0 -m "v1.0.0: Initial project release"
git push origin v1.0.0
```

### Version Format

```
v<major>.<minor>.<patch>
```

| Bump | When |
| ---- | ---- |
| **Major** | Breaking changes, complete rewrite |
| **Minor** | New features, new analysis phases |
| **Patch** | Bug fixes, doc corrections, config tweaks |

---

## 7. Day-to-Day Workflow

### Solo Developer

```
1. git checkout develop
2. git pull origin develop
3. git checkout -b feature/<name>
4. Implement, commit (conventional messages)
5. git push -u origin feature/<name>
6. Open PR → review yourself → squash merge → delete branch
7. Repeat
```

### With Collaborators

```
1. Same as above, but add:
   - PR review requirement (at least 1 approval)
   - CI checks must pass before merge
   - Assignees and labels on PR
```

---

## 8. Protected Branches

Set these rules on your remote (GitHub/GitLab):

| Branch | Protection |
| ------ | ---------- |
| `main` | No direct push. PR required. 1 approval. No force-push. |
| `develop` | No direct push. PR required. CI must pass. |

---

## 9. Quick Reference

```bash
# Clone the repository
git clone https://github.com/bugkey24/ai-era-pc-component-market-analysis.git
cd ai-era-pc-component-market-analysis

# Sync develop
git checkout develop && git pull origin develop

# Start feature
git checkout -b feature/<name>

# Push work
git push -u origin feature/<name>

# After PR merge — clean up
git checkout develop && git pull origin develop
git branch -d feature/<name>
git push origin --delete feature/<name>

# Tag a release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```
