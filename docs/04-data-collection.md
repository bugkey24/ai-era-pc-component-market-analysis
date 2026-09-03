<p align="center">
  <img src="https://img.shields.io/badge/AI--Era--PC--Market-DSS-blue?style=for-the-badge" alt="Project Badge" />
  <img src="https://img.shields.io/badge/Doc-04_Data--Collection-orange?style=for-the-badge" alt="Doc Badge" />
</p>

<p align="center">
  <a href="../README.md">README</a> | <a href="./01-overview.md">Overview</a> | <a href="./02-architecture.md">Architecture</a> | <a href="./03-methodology.md">Methodology</a> | <a href="./05-results-and-checklist.md">Results</a> | <a href="./06-timeline.md">Timeline</a> | <a href="./07-references.md">References</a>
</p>

# Data Collection Plan

---

> **⚠️ Compliance first:** robots.txt snapshots and the full per-platform
> analysis live in [`docs/compliance/`](./compliance/README.md). Summary:
> Tokopedia = primary platform (switch search to `/find/`, reviews explicitly
> allowed) · Shopee = risky (anti-bot in practice, `Crawl-delay: 1`) ·
> Blibli = products only, no search, no reviews. The selectors below are
> best-effort and must be re-validated against live pages.

---

## Platform Overview

| Platform  | Target Category | Scraping Method          | Difficulty |
| --------- | --------------- | ------------------------ | ---------- |
| Tokopedia | GPU, RAM, SSD   | Requests + BeautifulSoup | Medium     |
| Shopee    | GPU, RAM, SSD   | Selenium (dynamic)       | High       |
| Blibli    | GPU, RAM, SSD   | Requests + BeautifulSoup | Medium     |

---

## 6.1 Tokopedia

**Structure:**

```
URL: https://www.tokopedia.com/search?q=gpu&st=product
HTML: div[data-testid="divProductWrapper"]
Price: span[data-testid="productPrice"]
Rating: span[data-testid="productRating"]
```

**Implementation:**

```python
def scrape_tokopedia(category, pages=5):
    base_url = f"https://www.tokopedia.com/search?q={category}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    products = []

    for page in range(1, pages + 1):
        url = f"{base_url}&page={page}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        items = soup.find_all('div', {'data-testid': 'divProductWrapper'})
        for item in items:
            product = extract_product_data(item)
            products.append(product)

        time.sleep(2)

    return pd.DataFrame(products)
```

---

## 6.2 Shopee

**Structure:**

```
URL: https://shopee.co.id/search?keyword=gpu
HTML: div[data-testid="product-item"]
Price: span[data-testid="product-price"]
Dynamic Content: Requires Selenium
```

**Implementation:**

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_shopee(category):
    driver = webdriver.Chrome()
    driver.get(f"https://shopee.co.id/search?keyword={category}")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="product-item"]'))
    )

    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    products = []
    items = driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-item"]')
    for item in items:
        product = extract_shopee_product(item)
        products.append(product)

    driver.quit()
    return pd.DataFrame(products)
```

---

## 6.3 Blibli

**Structure:**

```
URL: https://www.blibli.com/search/gpu
HTML: div.product-item
Price: span.price-value
Similar to Tokopedia (static HTML)
```
