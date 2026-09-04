<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-01_Overview-green?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./04-data-collection.md">Data Collection</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a> | <a href="./08-git-workflow.md">Git Workflow</a> | <a href="./09-live-experiment-results.md">Live Results</a> | <a href="./10-running-guide.md">Running Guide</a>
</p>

# Project Overview

## Smart Decision Support System for Hardware Procurement in the AI Era

---

## 1. Executive Summary

This project develops a **Decision Support System (DSS)** that analyzes the unprecedented price surge of computer components (GPU, RAM, SSD) driven by the Artificial Intelligence boom. The system combines web scraping, statistical analysis, sentiment analysis, and multi-criteria decision-making methods to provide actionable insights and recommendations for consumers, businesses, and investors.

### Problem Statement

The global semiconductor industry is experiencing a structural crisis where AI infrastructure demands have diverted production capacity away from consumer-grade components. Prices have increased by over 100-300% across various components, creating significant uncertainty for consumers and businesses. Traditional purchasing decisions are no longer reliable, as market dynamics have fundamentally changed.

### Key Questions Addressed

1. **Why** have prices increased by over 100%?
2. **When** will prices normalize?
3. **Will** prices continue to rise indefinitely?
4. **What** is the optimal purchasing strategy based on individual needs and risk tolerance?

---

## 2. Project Objectives

### Primary Objectives

| Objective                | Description                                                      | Success Metric                         |
| ------------------------ | ---------------------------------------------------------------- | -------------------------------------- |
| **Data Collection**      | Scrape real-time pricing data from multiple e-commerce platforms | 100+ unique product listings           |
| **Statistical Analysis** | Analyze historical and current price trends                      | Identification of correlation patterns |
| **Sentiment Analysis**   | Extract consumer sentiment from product reviews                  | >75% classification accuracy           |
| **Decision Modeling**    | Implement AHP-TOPSIS hybrid method                               | Ranking of 5-10 top recommendations    |
| **Prediction Framework** | Develop price normalization timeline                             | Provide 2-3 distinct scenarios         |

### Secondary Objectives

- Create a reusable scraping framework for multiple platforms
- Build a reproducible analysis pipeline in Google Colab
- Generate visualizations that explain price dynamics
- Provide risk-adjusted recommendations

---

## 3. Project Scope & Deliverables

### In-Scope

- **Web Scraping:** Tokopedia, Shopee, and Blibli for computer components
- **Data Categories:** GPU, RAM (DDR4/DDR5), SSD/NVMe storage
- **Data Fields:** Product name, price, rating, review count, seller rating, specifications
- **Analysis Methods:** Statistical analysis, sentiment analysis (SVM), AHP-TOPSIS
- **Output:** Interactive Google Colab notebook with complete analysis

### Out-of-Scope

- Real-time market monitoring (one-time snapshot acceptable)
- Deep learning models (SVM/Logistic Regression sufficient)
- Full-fledged web application (Colab-based only)
- International market analysis (focus on Indonesian market)

### Deliverables

```
Project Deliverables
├── README.md (Project Documentation)
├── Google Colab Notebook (Complete Implementation)
│   ├── Section 1-2: Environment Setup & Configuration
│   ├── Section 3-4: Data Loading (existing CSVs or live scraping)
│   ├── Section 5: Preprocessing & Feature Engineering
│   ├── Section 6: Statistical Analysis
│   ├── Section 7: Sentiment Analysis
│   ├── Section 8: AHP-TOPSIS Decision Model
│   ├── Section 9-10: Visualization & Export
│   └── Section 11: Conclusions
├── src/ Package (7 layers, importable)
│   ├── scrapers/ (products + reviews + robots compliance gate)
│   ├── preprocessing/ · analysis/ · dss/ · visualization/
│   └── pipeline.py (7-phase orchestrator)
├── Data Outputs
│   ├── cleaned_data.csv
│   ├── rankings.csv
│   ├── statistics.json
│   └── prediction.json
├── Visualizations
│   ├── price_trends.png
│   ├── correlation_heatmap.png
│   └── ranking_results.png
└── Test Suite (166 offline tests, CI-gated)
```

---

## 4. Conclusion

This project provides a comprehensive blueprint for developing a DSS that analyzes computer component price surges in the AI era. By integrating web scraping, statistical analysis, sentiment analysis, and AHP-TOPSIS, the system will deliver:

1. **Data-driven insights** into why prices have increased over 100%
2. **Predictive analysis** of when prices might normalize
3. **Actionable recommendations** for purchasing decisions
4. **Transparent methodology** using proven decision-making frameworks

The expected outcome is a reproducible, well-documented Google Colab notebook that can serve as a decision-making tool for consumers, businesses, and researchers interested in understanding and navigating the current computer hardware market crisis.

---

**Document Version:** 1.0 | **Date:** September 2026
