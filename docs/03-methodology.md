<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-03_Methodology-teal?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./04-data-collection.md">Data Collection</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a>
</p>

# Detailed Methodology

---

## Phase 1: Web Scraping

### Scraping Strategy

1. **Category Search:** Use platform search with category filters
2. **Pagination:** Scrape 3-5 pages per category (50-100 products)
3. **Rate Limiting:** 1-3 second delay between requests
4. **Error Handling:** Retry with exponential backoff
5. **User Agent Rotation:** Mimic real browsers

### Target Data Fields

```python
{
    'product_id': 'string',
    'name': 'string',
    'category': 'GPU|RAM|SSD',
    'price': 'integer (IDR)',
    'discount': 'integer (%)',
    'rating': 'float (0-5)',
    'review_count': 'integer',
    'seller_name': 'string',
    'seller_rating': 'float (0-5)',
    'seller_followers': 'integer',
    'product_condition': 'new|used',
    'specifications': {
        'capacity': 'string',
        'speed': 'string',
        'interface': 'string (for SSD)',
        'memory_type': 'string (for RAM)',
        'cuda_cores': 'string (for GPU)'
    },
    'location': 'string',
    'scrape_timestamp': 'datetime'
}
```

---

## Phase 2: Data Preprocessing

### Cleaning Process

1. Remove duplicates
2. Handle missing values
3. Convert price strings to integers
4. Extract numerical values from specifications
5. Standardize category names
6. Normalize rating scales
7. Remove outliers (beyond 3 standard deviations)
8. Encode categorical variables
9. Text cleaning for sentiment analysis

### Feature Engineering

| Feature             | Method                                 |
| ------------------- | -------------------------------------- |
| Price per GB        | price / capacity                       |
| Price per CUDA Core | price / cuda_cores                     |
| Discount Depth      | (original - current) / original * 100  |
| Review Score        | rating * review_count (weighted)       |
| Seller Trust        | seller_rating * log(followers + 1)     |

---

## Phase 3: Statistical Analysis

### A. Descriptive Statistics

```python
statistics = {
    'mean_price': df['price'].mean(),
    'median_price': df['price'].median(),
    'std_dev': df['price'].std(),
    'min_price': df['price'].min(),
    'max_price': df['price'].max(),
    'q1': df['price'].quantile(0.25),
    'q3': df['price'].quantile(0.75),
    'iqr': df['price'].quantile(0.75) - df['price'].quantile(0.25)
}
```

### B. Price Trend Analysis

- Month-over-month price changes
- Year-over-year comparison
- Correlation with AI investment announcements
- Seasonality patterns (if detectable)

### C. Cross-Category Correlation

- GPU price vs RAM price
- GPU price vs SSD price
- Price vs Rating correlation

### D. Normalization Analysis

- Percentage increase calculation
- Projected normalization timeline based on:
  - Historical semiconductor cycles (4-6 years)
  - AI investment trends
  - New fabrication plant construction timelines

---

## Phase 4: Sentiment Analysis

### A. Text Preprocessing

```python
1. Lowercase conversion
2. Remove special characters
3. Tokenization
4. Stopword removal (Indonesian + English)
5. Stemming/Lemmatization
6. TF-IDF Vectorization
```

### B. Sentiment Classification (SVM)

```python
# Model Pipeline
1. Split data: 80% train, 20% test
2. Feature extraction: TF-IDF (max_features=5000)
3. Model: LinearSVC with class_weight='balanced'
4. Evaluation: Accuracy, Precision, Recall, F1-Score
5. Cross-validation: 5-fold
```

### C. Aspect-Based Sentiment Analysis

```python
aspects = {
    'price': ['mahal', 'murah', 'terjangkau'],
    'performance': ['cepat', 'lambat', 'stabil'],
    'quality': ['awet', 'rusak', 'bagus'],
    'ai_capability': ['AI', 'machine learning', 'training'],
    'value': ['worth it', 'overpriced', 'recommend']
}
```

### D. Sentiment Visualization

- Word clouds
- Sentiment distribution pie charts
- Sentiment score distribution
- Aspect-sentiment heatmap

---

## Phase 5: AHP-TOPSIS Implementation

### AHP (Analytical Hierarchy Process)

#### Criteria Definition

| Criteria            | Code | Weight (%) | Direction |
| ------------------- | ---- | ---------- | --------- |
| Price (IDR)         | C1   | 30%        | Minimize  |
| Performance         | C2   | 25%        | Maximize  |
| Customer Rating     | C3   | 15%        | Maximize  |
| Seller Reliability  | C4   | 10%        | Maximize  |
| Sentiment Score     | C5   | 10%        | Maximize  |
| Future Value        | C6   | 10%        | Maximize  |

#### Pairwise Comparison Matrix

```python
# 1-9 Scale: C1=Price, C2=Performance, C3=Rating, C4=Seller, C5=Sentiment, C6=Future
pairwise_matrix = [
    [1, 1/3, 3, 5, 5, 3],           # Price vs others
    [3, 1, 5, 7, 7, 5],             # Performance vs others
    [1/3, 1/5, 1, 3, 3, 1/3],       # Rating vs others
    [1/5, 1/7, 1/3, 1, 1, 1/5],     # Seller vs others
    [1/5, 1/7, 1/3, 1, 1, 1/5],     # Sentiment vs others
    [1/3, 1/5, 3, 5, 5, 1]          # Future Value vs others
]
```

#### AHP Steps

1. Normalize pairwise matrix
2. Calculate priority weights (column-normalization method)
3. Check consistency ratio (CR < 0.1)

### TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)

#### Process

```python
# Step 1: Normalize decision matrix
r_ij = x_ij / sqrt(sum(x_ij^2))

# Step 2: Weighted normalized matrix
v_ij = w_j * r_ij

# Step 3: Determine ideal and negative-ideal solutions
A_plus = [max(v_ij) for benefit, min(v_ij) for cost]
A_minus = [min(v_ij) for benefit, max(v_ij) for cost]

# Step 4: Calculate separation measures
S_plus = sqrt(sum((v_ij - A_plus_j)^2))
S_minus = sqrt(sum((v_ij - A_minus_j)^2))

# Step 5: Calculate relative closeness
C_i = S_minus / (S_plus + S_minus)

# Step 6: Rank alternatives by C_i (descending)
```

#### Ranking Output

- Top 5-10 recommended products
- Detailed score breakdown
- Comparison visualization

---

## Phase 6: Price Normalization Prediction

### Scenario Modeling

```python
scenarios = {
    'bull': {
        'description': 'AI investment continues aggressive',
        'timeframe': '2028-2029',
        'recovery_probability': 0.3
    },
    'base': {
        'description': 'AI investment stabilizes, new fabs operational',
        'timeframe': '2027-2028',
        'recovery_probability': 0.5
    },
    'bear': {
        'description': 'AI bubble bursts, surplus capacity',
        'timeframe': '2026-2027',
        'recovery_probability': 0.2
    }
}
```

### Factors Affecting Normalization

| Factor                  | Impact | Timeline    |
| ----------------------- | ------ | ----------- |
| New Fab Construction    | High   | 2-3 years   |
| AI Investment Slowdown  | Medium | 6-12 months |
| Memory Technology Shift | Medium | 1-2 years   |
| Consumer Demand Drop    | Low    | 3-6 months  |
| Government Regulations  | Low    | Variable    |
