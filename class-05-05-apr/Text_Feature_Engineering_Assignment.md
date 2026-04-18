# Text Feature Engineering Assignment (Real-world Dataset)

## Problem Statement

Build a **Text Processing Pipeline** to analyze real user-generated text (reviews/comments) and convert them into numerical features for machine learning models using:
- One Hot Encoding (OHE)
- Bag of Words (BoW)
- TF-IDF

---

## Dataset Collection

Minimum **100 reviews** scraped from **Amazon.in** and **Flipkart**, stored as CSV with a `review_text` column.

### [scraper.py](scraper.py) — Amazon India + Flipkart (Selenium-based)

| Detail | Value |
|---|---|
| Library | `undetected-chromedriver`, `selenium`, `BeautifulSoup` |
| Target | 500 reviews per platform (1000 total) |
| Sources | Amazon.in (dynamic ASIN discovery) + Flipkart (5 products) |
| Output files | `amazon_reviews.csv`, `flipkart_reviews.csv`, `all_reviews.csv` |
| Bot detection | Persistent Chrome profile; script pauses for manual login/CAPTCHA |

---

### Amazon.in — How it works

1. Searches Amazon.in for each query in `AMAZON_SEARCH_QUERIES`
2. Skips sponsored results, extracts real product ASINs
3. Paginates through review pages for each ASIN
4. If a login wall appears, script pauses — you log in once, then press ENTER

**Search queries used:**

| Query |
|---|
| oneplus nord smartphone |
| samsung galaxy m series phone |
| redmi note 5g phone |
| boat airdopes earbuds |
| fire boltt smartwatch |
| realme narzo phone |
| kindle ereader |
| noise colorfit smartwatch |

---

### Flipkart — How it works

1. Opens each product's review URL directly
2. Paginates through review pages
3. Anchors on star-rating divs (1–5), walks up the DOM to find review cards
4. Deduplicates reviews by `review_text`
5. If CAPTCHA appears, script pauses — you solve it once, then press ENTER

**Products hardcoded:**

| Product | Source |
|---|---|
| Samsung Galaxy M14 5G | Flipkart |
| OnePlus Nord CE 3 Lite | Flipkart |
| Redmi Note 13 5G | Flipkart |
| boAt Airdopes 141 | Flipkart |
| HP 15s Laptop | Flipkart |

---

### Key Functions

| Function | Description |
|---|---|
| `build_driver()` | Launches Chrome with a persistent profile to reuse sessions |
| `_discover_asins(driver, query)` | Searches Amazon.in, skips sponsored results, returns real ASINs |
| `_parse_amazon_page(driver, product)` | Extracts rating, title, body, author, date from Amazon review cards |
| `scrape_amazon(target)` | Full Amazon flow: discover ASINs → paginate → collect reviews |
| `_parse_flipkart_page(driver, product)` | Structural DOM extraction for Flipkart review cards |
| `scrape_flipkart(target)` | Full Flipkart flow: paginate product URLs → collect reviews |
| `wait_for_user(message)` | Pauses script for manual login/CAPTCHA resolution |
| `is_amazon_blocked(driver)` | Detects Amazon sign-in wall or CAPTCHA |
| `is_flipkart_blocked(driver)` | Detects Flipkart reCAPTCHA / verification page |
| `save_csv(review_list, path)` | Writes `Review` dataclass objects to CSV |

---

## CSV Schema

| Column | Description |
|---|---|
| `source` | Platform (`amazon` or `flipkart`) |
| `product` | Product name |
| `rating` | Star rating (1–5) |
| `title` | Review title (if available) |
| `review_text` | Main review body — **primary feature column** |
| `reviewer` | Username (Amazon only; Flipkart not available) |
| `date` | Review date (Amazon only; Flipkart not available) |

---

## Assignment Tasks

### Task 1: Preprocessing
1. Convert text to lowercase
2. Tokenization
3. Remove punctuation
4. *(Optional)* Remove stopwords (`and`, `a`, `the`, …)
5. *(Optional)* Lemmatization

### Task 2: Vocabulary Creation
Build vocabulary manually or using `sklearn`. Print:
- Vocabulary size
- Top frequent words

### Task 3: Feature Engineering

| Method | Tool |
|---|---|
| One Hot Encoding | Document-level binary vector |
| Bag of Words | `sklearn.feature_extraction.text.CountVectorizer` |
| TF-IDF | `sklearn.feature_extraction.text.TfidfVectorizer` |

### Task 4: Comparison Analysis
- Create a comparison table for OHE, BoW, and TF-IDF
- Explain which words rank highest in TF-IDF and why common words get lower weight

### Task 5: Sparse Matrix Analysis
- Print matrix shapes
- Calculate sparsity (% of zeros)
- Explain why sparse matrices are inefficient at scale

### Task 6: Real-world Questions
1. Why does BoW fail to capture semantic meaning? (e.g., synonyms treated as unrelated)
2. When should you use BoW vs TF-IDF in industry?
3. What are the limitations of TF-IDF in real applications?

### Task 7: Mini Use Case — Sentiment Classification
- Label reviews as **positive** or **negative**
- Train a **Logistic Regression** or **Naive Bayes** classifier
- Compare accuracy using BoW features vs TF-IDF features

---

## Deliverables

| # | Deliverable |
|---|---|
| 1 | Python notebook (`.ipynb`) |
| 2 | Clean and modular code |
| 3 | Scraped dataset (`all_reviews.csv`) |
| 4 | Output screenshots |
| 5 | Short report (1–2 pages) with observations and conclusions |

---

## Installation

```bash
pip install undetected-chromedriver selenium beautifulsoup4 lxml
pip install scikit-learn pandas nltk
```

> Chrome browser must be installed. The script auto-manages the ChromeDriver version.

## Running the Scraper

```bash
python scraper.py
```

- On the **first run**, if Amazon or Flipkart shows a login/CAPTCHA page, the script **pauses** and prints a message. Solve it manually in the open browser, then press **ENTER** to continue.
- On **subsequent runs**, the saved Chrome profile reuses your session automatically — no manual steps needed.
