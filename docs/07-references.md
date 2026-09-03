<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-07_References-grey?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./04-data-collection.md">Data Collection</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a>
</p>

# References & Appendix

---

## References

### Academic Sources

1. Saaty, T.L. (1980). "The Analytic Hierarchy Process"
2. Hwang, C.L., & Yoon, K. (1981). "Multiple Attribute Decision Making"
3. Liu, Y., et al. (2023). "Sentiment Analysis in E-commerce: A Survey"

### Industry Reports

1. Samsung Electronics. (2024). "Semiconductor Market Outlook"
2. TrendForce. (2025). "DRAM/NAND Flash Price Trends"
3. Goldman Sachs. (2024). "AI Infrastructure Investment Report"

### Technical Documentation

1. BeautifulSoup Documentation
2. Selenium WebDriver Documentation
3. Pandas Documentation
4. Scikit-learn Documentation

---

## Appendix A: Required Libraries

```python
# Core Libraries
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import time
import re
import json
import warnings

# Selenium (if using dynamic content)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# NLP & Sentiment Analysis
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
```

---

## Appendix B: Google Colab Setup

```python
# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Install additional packages
!pip install selenium
!pip install webdriver-manager
!pip install wordcloud
!pip install plotly

# Download NLTK data
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')
```

---

## Appendix C: Colab File Structure

```
/content/drive/MyDrive/Project/
├── data/
│   ├── raw/
│   │   ├── tokopedia_gpu.csv
│   │   ├── tokopedia_ram.csv
│   │   ├── shopee_gpu.csv
│   │   └── blibli_ssd.csv
│   └── processed/
│       └── cleaned_data.csv
├── notebooks/
│   └── main_analysis.ipynb
├── outputs/
│   ├── visualizations/
│   ├── rankings.csv
│   └── sentiment_results.csv
└── README.md
```
