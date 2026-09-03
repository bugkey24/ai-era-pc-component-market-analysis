<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-05_Results--Checklist-red?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./04-data-collection.md">Data Collection</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a>
</p>

# Expected Results, Checklist & Risk Management

---

## 1. Expected Results

### 1.1 Statistical Analysis Results

| Metric                  | GPU                     | RAM                  | SSD                  |
| ----------------------- | ----------------------- | -------------------- | -------------------- |
| Average Price           | Rp 12,500,000           | Rp 1,800,000         | Rp 950,000           |
| Median Price            | Rp 11,800,000           | Rp 1,700,000         | Rp 900,000           |
| Price Range             | Rp 4,000,000-25,000,000 | Rp 800,000-3,800,000 | Rp 450,000-2,500,000 |
| Std Deviation           | Rp 3,200,000            | Rp 400,000           | Rp 200,000           |
| % Increase (YoY)        | 80%                     | 170%                 | 60%                  |
| Projected Normalization | 2027-2028               | 2027-2028            | 2027-2028            |

### 1.2 Sentiment Analysis Results

```python
{
    'sentiment_distribution': {
        'positive': 45%,
        'negative': 35%,
        'neutral': 20%
    },
    'aspect_sentiment': {
        'price': {'positive': 20%, 'negative': 65%, 'neutral': 15%},
        'performance': {'positive': 70%, 'negative': 15%, 'neutral': 15%},
        'quality': {'positive': 60%, 'negative': 20%, 'neutral': 20%},
        'ai_capability': {'positive': 80%, 'negative': 5%, 'neutral': 15%}
    },
    'model_accuracy': {
        'SVM': 82.5%,
        'Logistic_Regression': 80.3%
    }
}
```

### 1.3 AHP-TOPSIS Ranking Results

| Rank | Product   | Score | Price    | Performance | Rating | Sentiment | Recommendation         |
| ---- | --------- | ----- | -------- | ----------- | ------ | --------- | ---------------------- |
| 1    | Product X | 0.89  | Rp 12.5M | 100%        | 4.8    | 85%       | **Highly Recommended** |
| 2    | Product Y | 0.82  | Rp 11.8M | 95%         | 4.7    | 80%       | Recommended            |
| 3    | Product Z | 0.78  | Rp 13.2M | 98%         | 4.6    | 82%       | Recommended            |
| 4    | Product A | 0.71  | Rp 9.5M  | 85%         | 4.5    | 75%       | Value Option           |
| 5    | Product B | 0.65  | Rp 15.0M | 100%        | 4.3    | 70%       | Premium Option         |

### 1.4 Price Normalization Predictions

```
Scenario Analysis:
┌─────────────────────────────────────────────────────────────────────┐
│ Scenario  │ Timeline   │ Probability │ Recommendation              │
├───────────┼────────────┼─────────────┼────────────────────────────┤
│ Bear      │ 2026-2027  │ 20%         │ Wait if possible, buy       │
│           │            │             │ if necessary                │
│ Base      │ 2027-2028  │ 50%         │ Hold for 6-12 months,       │
│           │            │             │ then consider buying        │
│ Bull      │ 2028-2029  │ 30%         │ Buy now, prices will        │
│           │            │             │ continue to rise            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Implementation Checklist

### 2.1 Pre-Implementation (Week 1)

- [x] Select and research target websites
- [x] Check robots.txt policies *(snapshots + verdicts in `docs/compliance/`)*
- [x] Install required libraries *(requirements.txt + requirements-dev.txt)*
- [x] Set up Google Colab environment *(notebooks/main_pipeline.ipynb)*
- [x] Create project structure

### 2.2 Implementation (Week 2-3)

- [x] Develop scraping functions for each platform *(products + reviews, robots-gated)*
- [x] Implement data cleaning pipeline
- [x] Build statistical analysis module
- [x] Implement sentiment analysis (SVM) *(training data pending — see 2.3)*
- [x] Code AHP-TOPSIS algorithm
- [x] Create visualization functions

### 2.3 Post-Implementation (Week 4)

- [ ] Run complete pipeline against live platforms *(pending — selectors need live validation)*
- [ ] Validate results
- [x] Create documentation
- [ ] Generate visualizations from live data
- [ ] Write conclusions and recommendations
- [ ] Share Google Colab notebook

---

## 3. Success Criteria

### 3.1 Technical Success

| Criterion             | Target               | Measurement                      |
| --------------------- | -------------------- | -------------------------------- |
| Scraping Success Rate | >95%                 | Number of successful extractions |
| Data Quality          | Clean, no duplicates | Pandas validation checks         |
| Sentiment Accuracy    | >75%                 | F1-score on test set             |
| AHP Consistency       | CR < 0.1             | Consistency ratio calculation    |
| Execution Time        | <30 minutes          | Colab runtime                    |

### 3.2 Analytical Success

| Criterion              | Target                                |
| ---------------------- | ------------------------------------- |
| Meaningful Insights    | At least 3 actionable recommendations |
| Clear Price Trends     | Visual evidence of price increases    |
| Normalization Timeline | 3 scenarios with probabilities        |
| Consumer Value         | Ranking helps decision making         |

---

## 4. Risks & Mitigation

| Risk                    | Likelihood | Impact | Mitigation                     |
| ----------------------- | ---------- | ------ | ------------------------------ |
| Website blocks scraper  | Medium     | High   | Rotate headers, use proxies    |
| Dynamic content changes | High       | Medium | Use Selenium, flexible parsing |
| Data inconsistency      | Medium     | Medium | Robust validation checks       |
| Model underperformance  | Low        | Medium | Try multiple algorithms        |
| Google Colab limits     | Low        | Low    | Optimize memory usage          |
