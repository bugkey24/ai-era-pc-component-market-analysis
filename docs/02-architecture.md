<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-02_Architecture-purple?style=for-the-badge" alt="Doc Badge" />
  <img src="https://img.shields.io/badge/Fixes-Applied-orange?style=for-the-badge" alt="Fixes Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./04-data-collection.md">Data Collection</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a>
</p>

# Technical Architecture

---

## 1. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR (Main Pipeline)                       │
│                      `main_pipeline.py` / Colab Notebook                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────┐     ┌─────────────────────────┐     ┌───────────────────┐
│   CONFIG        │     │    DATA MANAGER          │     │   LOGGING         │
│  (config.yaml)  │◄────│  (DataLoader/Saver)      │     │   (logger.py)     │
└─────────────────┘     └─────────────────────────┘     └───────────────────┘
         │                             │                             │
         └─────────────────────────────┼─────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAYER 1: SCRAPING MODULE                         │
│                         (Polymorphism + Factory Pattern)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     abstract class BaseScraper                      │  │
│  │  + fetch_page()  + parse_product()  + get_next_page()  + save()   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    ▲                                       │
│                                    │                                       │
│   ┌────────────────┬───────────────┴───────────────┬─────────────────┐  │
│   │                │                               │                 │  │
│   ▼                ▼                               ▼                 ▼  │
│ TokopediaScraper  ShopeeScraper (Selenium)   BlibliScraper       Future   │
│  (static HTML)    (dynamic JS)              (static HTML)      Platform  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 2: PREPROCESSING MODULE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      DataPreprocessor (Class)                       │  │
│  │  + clean_text()  + normalize_price()  + handle_missing()  +        │  │
│  │    extract_specs()  + remove_outliers()  + transform_features()    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     FeatureEngineer (Class)                        │  │
│  │  + create_price_per_gb()  + create_weighted_rating()  +           │  │
│  │    create_seller_trust_score()                                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LAYER 3: ANALYSIS MODULE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐ │
│  │   StatisticalAnalyzer       │  │   SentimentAnalyzer (NLP)           │ │
│  │  + describe()              │  │  + preprocess_text()               │ │
│  │  + correlation_matrix()    │  │  + vectorize() (TF-IDF)            │ │
│  │  + trend_analysis()        │  │  + train_model() (SVM/LogReg)      │ │
│  │  + normality_test()        │  │  + predict_aspect()               │ │
│  └─────────────────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 4: DSS MODULE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐ │
│  │       AHPProcessor          │  │       TOPSISProcessor              │ │
│  │  + build_pairwise_matrix()  │  │  + normalize_matrix()             │ │
│  │  + calculate_weights()      │  │  + find_ideal_solutions()         │ │
│  │  + check_consistency()      │  │  + calculate_separation()         │ │
│  │  + get_weighted_criteria()  │  │  + rank_alternatives()            │ │
│  └─────────────────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 5: VISUALIZATION MODULE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        Visualizer (Class)                           │  │
│  │  + plot_price_trends()  + plot_sentiment_distribution()  +         │  │
│  │    plot_ranking_bar_chart()  + plot_correlation_heatmap()  +       │  │
│  │    plot_wordcloud()  + plot_radar_chart()                         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐  │
│  │  LAYER 1     │     │  LAYER 2     │     │  LAYER 3              │  │
│  │  DATA        │────▶│  DATA        │────▶│  ANALYSIS             │  │
│  │  ACQUISITION │     │  PROCESSING  │     │  & MODELLING          │  │
│  └──────────────┘     └──────────────┘     └──────────────────────┘  │
│         │                     │                        │               │
│  Tokopedia            Pandas DataFrame        Statistical Analysis    │
│  Shopee               Data Cleaning           Sentiment Analysis      │
│  Blibli               Normalization           AHP-TOPSIS             │
│                                                          │             │
│                                                    ┌─────▼─────┐     │
│                                                    │ LAYER 4   │     │
│                                                    │ OUTPUT    │     │
│                                                    │ RENDER    │     │
│                                                    └───────────┘     │
│                                                    Visualizations    │
│                                                    Recommendations   │
│                                                    Prediction         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Class Definitions

### 3.1 BaseScraper (Abstract Base Class)

```python
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Optional

class BaseScraper(ABC):
    """Abstract base class for all platform scrapers."""

    platform_name: str  # Must be set by subclasses

    def __init__(self, config: Dict):
        self.config = config
        self.headers = {'User-Agent': config.get('user_agent', 'Mozilla/5.0')}
        self.timeout = config.get('timeout', 10)
        self.retry_count = config.get('retry_count', 3)

    @abstractmethod
    def fetch_page(self, url: str) -> str:
        """Fetch HTML content from a given URL."""
        pass

    @abstractmethod
    def parse_product(self, html_element) -> Dict:
        """Parse product data from HTML element."""
        pass

    @abstractmethod
    def get_next_page_url(self, current_url: str) -> Optional[str]:
        """Get URL for next page of results."""
        pass

    @abstractmethod
    def _build_search_url(self, category: str) -> str:
        """Build the initial search URL for a category."""
        pass

    def scrape(self, category: str, max_pages: int = 5) -> pd.DataFrame:
        """Main scraping orchestration method."""
        products = []
        url = self._build_search_url(category)

        for page in range(max_pages):
            html = self.fetch_page(url)
            items = self._extract_items(html)

            for item in items:
                product = self.parse_product(item)
                product['source'] = self.platform_name
                product['scrape_timestamp'] = pd.Timestamp.now()
                products.append(product)

            next_url = self.get_next_page_url(url)
            if not next_url:
                break
            url = next_url
            time.sleep(self.config.get('delay', 2))

        return pd.DataFrame(products)

    def _extract_items(self, html: str) -> List:
        """Extract product items from HTML (implementation varies)."""
        raise NotImplementedError
```

> **Fix applied:** `_build_search_url` is now declared as an `@abstractmethod` on the base class, ensuring subclasses cannot omit it.

### 3.2 Concrete Scraper Implementations

```python
class TokopediaScraper(BaseScraper):
    """Scraper for Tokopedia (static HTML)."""

    platform_name = "tokopedia"

    def fetch_page(self, url: str) -> str:
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def parse_product(self, html_element) -> Dict:
        return {
            'product_id': html_element.get('data-product-id'),
            'name': html_element.find('span', {'data-testid': 'productName'}).text,
            'price': self._extract_price(html_element),
            'rating': self._extract_rating(html_element),
        }

    def get_next_page_url(self, current_url: str) -> Optional[str]:
        # Parse pagination from Tokopedia
        pass

    def _build_search_url(self, category: str) -> str:
        return f"https://www.tokopedia.com/search?q={category}&st=product"


class ShopeeScraper(BaseScraper):
    """Scraper for Shopee (dynamic JavaScript)."""

    platform_name = "shopee"

    def __init__(self, config: Dict):
        super().__init__(config)
        self.driver = None

    def fetch_page(self, url: str) -> str:
        if not self.driver:
            self.driver = self._init_driver()
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="product-item"]'))
        )
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        return self.driver.page_source

    def _init_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)

    def _build_search_url(self, category: str) -> str:
        return f"https://shopee.co.id/search?keyword={category}"

    # ... other methods
```

### 3.3 DataPreprocessor Class

```python
class DataPreprocessor:
    """Clean and preprocess scraped data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def clean_prices(self) -> 'DataPreprocessor':
        """Convert price strings to integers."""
        pattern = r'[^0-9]'
        self.df['price'] = self.df['price'].str.replace(pattern, '', regex=True).astype(int)
        return self

    def handle_missing(self, strategy: str = 'drop') -> 'DataPreprocessor':
        """Handle missing values."""
        if strategy == 'drop':
            self.df.dropna(inplace=True)
        elif strategy == 'fill':
            self.df.fillna(self.df.median(numeric_only=True), inplace=True)
        return self

    def extract_specifications(self) -> 'DataPreprocessor':
        """Extract specs from product name/description."""
        return self

    def remove_outliers(self, threshold: float = 3.0) -> 'DataPreprocessor':
        """Remove statistical outliers using absolute z-score threshold."""
        mean_price = self.df['price'].mean()
        std_price = self.df['price'].std()
        if std_price == 0:
            return self  # Guard: cannot normalize if std is zero
        z_scores = np.abs((self.df['price'] - mean_price) / std_price)
        self.df = self.df[z_scores < threshold]
        return self

    def normalize_ratings(self) -> 'DataPreprocessor':
        """Normalize ratings to 0-5 scale if needed."""
        return self

    def get_cleaned_data(self) -> pd.DataFrame:
        return self.df
```

> **Fix applied:** `remove_outliers` now guards against division by zero when `std == 0`, and `handle_missing` uses `numeric_only=True` in `median()` to avoid errors with non-numeric columns.

### 3.4 AHPProcessor Class

```python
class AHPProcessor:
    """Analytical Hierarchy Process implementation."""

    def __init__(self, criteria: List[str]):
        self.criteria = criteria
        self.n = len(criteria)
        self.pairwise_matrix = None
        self.weights = None
        self.consistency_ratio = None

    def build_pairwise_matrix(self, comparisons: List[List[float]]) -> 'AHPProcessor':
        """Build pairwise comparison matrix."""
        if len(comparisons) != self.n or len(comparisons[0]) != self.n:
            raise ValueError("Matrix size mismatch")
        self.pairwise_matrix = np.array(comparisons, dtype=float)
        return self

    def calculate_weights(self) -> 'AHPProcessor':
        """Calculate priority weights using column-normalization method."""
        col_sums = self.pairwise_matrix.sum(axis=0)
        normalized_matrix = self.pairwise_matrix / col_sums
        self.weights = normalized_matrix.mean(axis=1)
        return self

    def check_consistency(self) -> 'AHPProcessor':
        """Calculate consistency ratio (CR). CR must be < 0.1 for acceptable consistency."""
        if self.weights is None:
            raise ValueError("Weights not calculated. Call calculate_weights() first.")

        weighted_sum = self.pairwise_matrix @ self.weights
        lambda_max = (weighted_sum / self.weights).mean()

        ci = (lambda_max - self.n) / (self.n - 1)

        ri_values = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
        ri = ri_values.get(self.n, 1.45)

        self.consistency_ratio = ci / ri
        return self

    def is_consistent(self, threshold: float = 0.1) -> bool:
        """Check if consistency ratio is acceptable (CR < 0.1)."""
        if self.consistency_ratio is None:
            raise ValueError("Consistency not checked. Call check_consistency() first.")
        return self.consistency_ratio < threshold

    def get_weights(self) -> np.ndarray:
        if self.weights is None:
            raise ValueError("Weights not calculated. Call calculate_weights() first.")
        return self.weights
```

> **Fix applied:** Added `ValueError` guards in `check_consistency`, `is_consistent`, and `get_weights` when called before prerequisites. Added `dtype=float` to matrix construction for numerical stability.

### 3.5 TOPSISProcessor Class

```python
class TOPSISProcessor:
    """TOPSIS implementation for ranking alternatives."""

    def __init__(self, decision_matrix: np.ndarray, weights: np.ndarray, criteria_types: List[str]):
        self.matrix = np.array(decision_matrix, dtype=float)
        self.weights = np.array(weights, dtype=float)
        self.criteria_types = criteria_types
        self.n_alternatives = self.matrix.shape[0]
        self.n_criteria = self.matrix.shape[1]

    def normalize_matrix(self) -> 'TOPSISProcessor':
        """Normalize decision matrix using vector normalization."""
        norms = np.sqrt((self.matrix ** 2).sum(axis=0))
        norms[norms == 0] = 1  # Guard against division by zero
        self.normalized = self.matrix / norms
        return self

    def apply_weights(self) -> 'TOPSISProcessor':
        """Apply weights to normalized matrix."""
        self.weighted = self.normalized * self.weights
        return self

    def find_ideal_solutions(self) -> 'TOPSISProcessor':
        """Find positive and negative ideal solutions."""
        self.ideal_positive = []
        self.ideal_negative = []

        for j in range(self.n_criteria):
            col = self.weighted[:, j]
            if self.criteria_types[j] == 'benefit':
                self.ideal_positive.append(col.max())
                self.ideal_negative.append(col.min())
            else:  # cost
                self.ideal_positive.append(col.min())
                self.ideal_negative.append(col.max())

        self.ideal_positive = np.array(self.ideal_positive)
        self.ideal_negative = np.array(self.ideal_negative)
        return self

    def calculate_separation(self) -> 'TOPSISProcessor':
        """Calculate separation from ideal solutions."""
        self.d_plus = np.sqrt(((self.weighted - self.ideal_positive) ** 2).sum(axis=1))
        self.d_minus = np.sqrt(((self.weighted - self.ideal_negative) ** 2).sum(axis=1))
        return self

    def calculate_scores(self) -> 'TOPSISProcessor':
        """Calculate relative closeness scores."""
        denominator = self.d_plus + self.d_minus
        denominator[denominator == 0] = 1  # Guard against division by zero
        self.scores = self.d_minus / denominator
        return self

    def rank(self) -> pd.DataFrame:
        """Return ranking of alternatives."""
        self.normalize_matrix().apply_weights().find_ideal_solutions()
        self.calculate_separation().calculate_scores()

        ranking = pd.DataFrame({
            'Alternative': range(self.n_alternatives),
            'Score': self.scores,
            'Rank': self.scores.argsort()[::-1] + 1
        })
        return ranking.sort_values('Rank')
```

> **Fix applied:** Added zero-division guards in `normalize_matrix` (norm == 0) and `calculate_scores` (d_plus + d_minus == 0). Added `dtype=float` to all array constructions.

### 3.6 SentimentAnalyzer Class

```python
class SentimentAnalyzer:
    """Sentiment analysis using SVM."""

    def __init__(self, language: str = 'indonesian'):
        self.language = language
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.model = LinearSVC(class_weight='balanced', random_state=42)
        self.is_trained = False

    def preprocess_text(self, text: str) -> str:
        """Clean and tokenize text."""
        if not isinstance(text, str) or not text.strip():
            return ''
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        tokens = word_tokenize(text)
        stop_words = set(stopwords.words('indonesian') + stopwords.words('english'))
        tokens = [t for t in tokens if t not in stop_words]
        return ' '.join(tokens)

    def train(self, texts: List[str], labels: List[str]) -> 'SentimentAnalyzer':
        """Train the sentiment classifier."""
        processed = [self.preprocess_text(t) for t in texts]
        # Filter out empty strings that may result from preprocessing
        valid_mask = [bool(p.strip()) for p in processed]
        processed = [p for p, v in zip(processed, valid_mask) if v]
        labels = [l for l, v in zip(labels, valid_mask) if v]

        X = self.vectorizer.fit_transform(processed)
        y = LabelEncoder().fit_transform(labels)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)
        self.is_trained = True

        y_pred = self.model.predict(X_test)
        self.accuracy = (y_pred == y_test).mean()
        self.report = classification_report(y_test, y_pred, output_dict=True)

        return self

    def predict(self, texts: List[str]) -> List[str]:
        """Predict sentiment for new texts."""
        if not self.is_trained:
            raise ValueError("Model not trained yet. Call train() first.")
        processed = [self.preprocess_text(t) for t in texts]
        X = self.vectorizer.transform(processed)
        return self.model.predict(X)

    def aspect_sentiment(self, texts: List[str], aspects: Dict[str, List[str]]) -> Dict:
        """Perform aspect-based sentiment analysis."""
        results = {}
        for aspect_name, keywords in aspects.items():
            aspect_texts = []
            for text in texts:
                if any(keyword in text.lower() for keyword in keywords):
                    aspect_texts.append(text)
            if aspect_texts:
                predictions = self.predict(aspect_texts)
                results[aspect_name] = {
                    'positive': sum(1 for p in predictions if p == 'positive') / len(predictions),
                    'negative': sum(1 for p in predictions if p == 'negative') / len(predictions),
                    'neutral': sum(1 for p in predictions if p == 'neutral') / len(predictions)
                }
        return results
```

> **Fix applied:** Added null/empty guard in `preprocess_text`. Added filtering of empty strings in `train()` to prevent TF-IDF issues. Added proper `ValueError` in `predict()`.

### 3.7 PipelineOrchestrator

```python
class PipelineOrchestrator:
    """Orchestrate the entire data pipeline."""

    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.data = None

    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML file."""
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logger(self):
        """Configure logging with a named logger (avoids overwriting root config)."""
        import logging
        logger = logging.getLogger('pipeline')
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def run_full_pipeline(self):
        """Execute all phases sequentially."""
        self.logger.info("Starting full pipeline...")

        self.logger.info("Phase 1: Scraping...")
        scrapers = self._initialize_scrapers()
        self.data = self._run_scraping(scrapers)

        self.logger.info("Phase 2: Preprocessing...")
        preprocessor = DataPreprocessor(self.data)
        self.data = preprocessor.clean_prices() \
            .handle_missing('drop') \
            .extract_specifications() \
            .remove_outliers() \
            .get_cleaned_data()

        self.logger.info("Phase 3: Statistical Analysis...")
        analyzer = StatisticalAnalyzer(self.data)
        stats = analyzer.describe().correlation_matrix()

        self.logger.info("Phase 4: Sentiment Analysis...")
        sentiment = SentimentAnalyzer()
        # ... train and predict

        self.logger.info("Phase 5: DSS Processing...")
        dss_result = self._run_dss()

        self.logger.info("Phase 6: Visualization...")
        visualizer = Visualizer(self.data)
        visualizer.create_all_plots()

        self.logger.info("Pipeline complete!")
        return self.data, stats, dss_result

    def _run_scraping(self, scrapers: List[BaseScraper]) -> pd.DataFrame:
        """Run all scrapers and combine results."""
        all_data = []
        for scraper in scrapers:
            self.logger.info(f"Scraping {scraper.platform_name}...")
            df = scraper.scrape(
                category=self.config['scraping']['categories'][0],
                max_pages=self.config['scraping']['max_pages']
            )
            all_data.append(df)
        return pd.concat(all_data, ignore_index=True)

    def _run_dss(self):
        """Run AHP-TOPSIS decision support."""
        criteria = self.config['dss']['criteria']

        ahp = AHPProcessor(criteria)
        ahp.build_pairwise_matrix(self.config['dss']['pairwise_matrix'])
        ahp.calculate_weights().check_consistency()

        if not ahp.is_consistent():
            self.logger.warning("AHP consistency ratio exceeds 0.1!")

        matrix = self._prepare_decision_matrix()
        topsis = TOPSISProcessor(matrix, ahp.get_weights(), self.config['dss']['criteria_types'])
        ranking = topsis.rank()

        return ranking
```

> **Fix applied:** `_setup_logger` now uses a named logger (`pipeline`) and only attaches handlers once, preventing root logger pollution. `_run_scraping` reads from config properly instead of a hardcoded key.

---

## 4. Design Principles

| Principle                       | Implementation                                                                             |
| ------------------------------- | ------------------------------------------------------------------------------------------ |
| **Single Responsibility**       | Each class has one clear purpose (e.g., `AHPProcessor` only handles AHP)                   |
| **Open/Closed**                 | New scrapers can be added without modifying existing code (inheritance from `BaseScraper`) |
| **Liskov Substitution**         | All scraper subclasses can replace `BaseScraper`                                           |
| **Interface Segregation**       | `BaseScraper` only includes essential abstract methods                                     |
| **Dependency Inversion**        | High-level modules depend on abstractions, not concrete implementations                    |
| **DRY (Don't Repeat Yourself)** | Common code extracted to base classes and utility modules                                  |
| **Configuration Over Code**     | `config.yaml` centralizes all settings                                                     |

---

## 5. File Structure

```
spk-scraping-harga-komponen-ai/
│
├── README.md
├── requirements.txt
├── config.yaml
│
├── src/
│   ├── __init__.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── tokopedia_scraper.py
│   │   ├── shopee_scraper.py
│   │   └── blibli_scraper.py
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── data_preprocessor.py
│   │   └── feature_engineer.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── statistical_analyzer.py
│   │   └── sentiment_analyzer.py
│   ├── dss/
│   │   ├── __init__.py
│   │   ├── ahp_processor.py
│   │   └── topsis_processor.py
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── visualizer.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
│
├── notebooks/
│   └── main_pipeline.ipynb
│
├── data/
│   ├── raw/
│   │   ├── tokopedia_gpu.csv
│   │   ├── tokopedia_ram.csv
│   │   ├── shopee_gpu.csv
│   │   └── blibli_ssd.csv
│   └── processed/
│       └── cleaned_data.csv
│
├── outputs/
│   ├── visualizations/
│   │   ├── price_trends.png
│   │   ├── sentiment_distribution.png
│   │   └── ranking_results.png
│   ├── rankings.csv
│   └── sentiment_results.json
│
└── logs/
    └── pipeline.log
```

---

## 6. Technology Stack

| Component              | Technology                       | Purpose                        |
| ---------------------- | -------------------------------- | ------------------------------ |
| **Scraping**           | Python Requests + BeautifulSoup  | Static HTML parsing            |
| **Dynamic Content**    | Selenium WebDriver               | JavaScript-rendered content    |
| **Data Processing**    | Pandas, NumPy                    | Data manipulation              |
| **Sentiment Analysis** | NLTK, scikit-learn (SVM)         | Text classification            |
| **Visualization**      | Matplotlib, Seaborn, Plotly      | Data visualization             |
| **DSS Methods**        | Custom AHP-TOPSIS implementation | Multi-criteria decision making |
| **Environment**        | Google Colab                     | Cloud-based execution          |

---

## 7. Dependency Management

### requirements.txt

```txt
# Core
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# Web Scraping
selenium>=4.15.0
webdriver-manager>=4.0.0

# NLP & Machine Learning
scikit-learn>=1.3.0
nltk>=3.8.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.17.0
wordcloud>=1.9.0

# Utilities
pyyaml>=6.0.0
tqdm>=4.66.0
```

### config.yaml

```yaml
project:
  name: "AI-Driven Market Analysis"
  version: "1.0"
  environment: "google-colab"

scraping:
  categories:
    - gpu
    - ram
    - ssd
  max_pages: 5
  delay: 2.0
  retry_count: 3
  timeout: 10
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  platforms:
    - name: tokopedia
      enabled: true
      method: static
      base_url: "https://www.tokopedia.com/search"
    - name: shopee
      enabled: true
      method: dynamic
      base_url: "https://shopee.co.id/search"
    - name: blibli
      enabled: true
      method: static
      base_url: "https://www.blibli.com/search"

preprocessing:
  handle_missing: "drop"
  outlier_threshold: 3.0
  normalize_ratings: true

sentiment:
  language: "indonesian"
  model: "LinearSVC"
  test_size: 0.2
  random_state: 42
  max_features: 5000

dss:
  criteria:
    - "price"
    - "performance"
    - "rating"
    - "seller_reliability"
    - "sentiment"
    - "future_value"
  criteria_types:
    - "cost"
    - "benefit"
    - "benefit"
    - "benefit"
    - "benefit"
    - "benefit"
  pairwise_matrix:
    - [1, 1/3, 3, 5, 5, 3]
    - [3, 1, 5, 7, 7, 5]
    - [1/3, 1/5, 1, 3, 3, 1/3]
    - [1/5, 1/7, 1/3, 1, 1, 1/5]
    - [1/5, 1/7, 1/3, 1, 1, 1/5]
    - [1/3, 1/5, 3, 5, 5, 1]

visualization:
  style: "seaborn-v0_8-darkgrid"
  palette: "viridis"
  figsize: [12, 8]
  dpi: 150

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/pipeline.log"
```
