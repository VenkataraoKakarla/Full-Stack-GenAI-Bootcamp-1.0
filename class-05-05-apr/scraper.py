"""
scraper.py — Amazon India & Flipkart Review Scraper
-----------------------------------------------------
Collects 500 reviews from Amazon.in and 500 from Flipkart using
undetected-chromedriver (bypasses bot detection).

A persistent Chrome profile is used so you only need to log in / solve
CAPTCHA ONCE — subsequent runs reuse the saved session automatically.

Usage:
    python scraper.py

Output (saved in the same directory):
    amazon_reviews.csv
    flipkart_reviews.csv
    all_reviews.csv
"""

import csv
import time
import random
import logging
import os
from dataclasses import dataclass, fields, asdict
from typing import Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────

TARGET_PER_PLATFORM = 500
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROME_PROFILE_DIR = os.path.join(OUTPUT_DIR, "chrome_profile")

# Amazon.in — search queries used to discover product ASINs dynamically
AMAZON_SEARCH_QUERIES = [
    "oneplus nord smartphone",
    "samsung galaxy m series phone",
    "redmi note 5g phone",
    "boat airdopes earbuds",
    "fire boltt smartwatch",
    "realme narzo phone",
    "kindle ereader",
    "noise colorfit smartwatch",
]

# Flipkart — search queries used to discover live product review URLs dynamically
FLIPKART_SEARCH_QUERIES = [
    "samsung galaxy smartphone",
    "oneplus nord smartphone",
    "redmi note 5g phone",
    "boat airdopes earbuds",
    "noise colorfit smartwatch",
    "realme narzo phone",
    "hp laptop",
    "lenovo ideapad laptop",
]


# ─── Data model ───────────────────────────────────────────────────────────────

@dataclass
class Review:
    source: str
    product: str
    rating: Optional[str]
    title: Optional[str]
    review_text: str
    reviewer: Optional[str]
    date: Optional[str]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def save_csv(review_list: list, path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[f.name for f in fields(Review)])
        writer.writeheader()
        for r in review_list:
            writer.writerow(asdict(r))
    log.info("Saved %d reviews → %s", len(review_list), path)


def sleep(lo: float = 2.0, hi: float = 5.0):
    time.sleep(random.uniform(lo, hi))


def build_driver() -> uc.Chrome:
    """Build undetected-chromedriver with a persistent Chrome profile."""
    os.makedirs(CHROME_PROFILE_DIR, exist_ok=True)
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=en-IN")
    options.add_argument("--disable-notifications")
    return uc.Chrome(options=options, use_subprocess=True, version_main=146)


def wait_for_user(message: str):
    """Pause and let the user resolve a login wall or CAPTCHA manually."""
    print("\n" + "=" * 60)
    print(message)
    print("After resolving it in the browser, press ENTER to continue...")
    print("=" * 60)
    input()


# ─── Amazon ───────────────────────────────────────────────────────────────────

def is_amazon_blocked(driver) -> bool:
    url = driver.current_url
    return (
        "ap/signin" in url
        or "Sign-In" in driver.title
        or "Enter the characters" in driver.page_source[:3000]
    )


def _discover_asins(driver, query: str, max_products: int = 2) -> list[tuple[str, str]]:
    """Search Amazon.in, skip sponsored ads, return (ASIN, product_name) pairs."""
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    log.info("  Searching Amazon: %s", url)
    driver.get(url)
    sleep(3, 5)

    soup = BeautifulSoup(driver.page_source, "lxml")
    products = []
    for item in soup.select("div[data-component-type='s-search-result']"):
        if item.select_one("span.s-label-popover-default, .puis-sponsored-label-text"):
            continue  # skip sponsored
        asin = item.get("data-asin", "").strip()
        if not asin or len(asin) != 10:
            continue
        name_el = item.select_one("h2 span.a-text-normal, h2 a span")
        name = name_el.get_text(strip=True)[:60] if name_el else query
        products.append((asin, name))
        if len(products) >= max_products:
            break

    log.info("  Found %d products for '%s'", len(products), query)
    return products


def _parse_amazon_page(driver, product_name: str) -> list[Review]:
    # Scroll to bottom to trigger any lazy-loaded review content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "lxml")
    reviews = []

    # Amazon.in uses both data-hook='review' and id^='customer_review'
    cards = soup.select("div[data-hook='review']")
    if not cards:
        cards = soup.select("div[id^='customer_review']")
    if not cards:
        # Last-resort: any div containing a review-body span
        cards = [el.find_parent("div") for el in soup.select("span[data-hook='review-body']")
                 if el.find_parent("div")]

    log.info("  Amazon parser: found %d review cards", len(cards))

    for card in cards:
        body_el   = card.select_one("span[data-hook='review-body'] span")
        if not body_el:
            body_el = card.select_one("span[data-hook='review-body']")
        rating_el = card.select_one("i[data-hook='review-star-rating'] span.a-icon-alt")
        if not rating_el:
            rating_el = card.select_one("i[data-hook='cmps-review-star-rating'] span.a-icon-alt")
        title_el  = card.select_one("a[data-hook='review-title'] span:not(.a-icon-alt)")
        if not title_el:
            title_el = card.select_one("span[data-hook='review-title']")
        author_el = card.select_one("span.a-profile-name")
        date_el   = card.select_one("span[data-hook='review-date']")

        body = body_el.get_text(strip=True) if body_el else ""
        if not body:
            continue
        reviews.append(Review(
            source="amazon",
            product=product_name,
            rating=rating_el.get_text(strip=True).split()[0] if rating_el else None,
            title=title_el.get_text(strip=True) if title_el else None,
            review_text=body,
            reviewer=author_el.get_text(strip=True) if author_el else None,
            date=date_el.get_text(strip=True) if date_el else None,
        ))
    return reviews


def scrape_amazon(target: int = 500) -> list[Review]:
    driver = build_driver()
    all_reviews: list[Review] = []
    login_handled = False

    try:
        log.info("Discovering product ASINs from Amazon.in...")
        discovered: list[tuple[str, str]] = []
        for query in AMAZON_SEARCH_QUERIES:
            discovered.extend(_discover_asins(driver, query, max_products=2))
            sleep(2, 4)

        # Deduplicate ASINs
        seen = set()
        products = []
        for asin, name in discovered:
            if asin not in seen:
                seen.add(asin)
                products.append((asin, name))
        log.info("Discovered %d unique products.", len(products))

        per_product = max(10, (target // max(len(products), 1)) + 10)

        for asin, name in products:
            if len(all_reviews) >= target:
                break
            collected, page = 0, 1

            while collected < per_product:
                url = (
                    f"https://www.amazon.in/product-reviews/{asin}/"
                    f"?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
                )
                log.info("Amazon | %-40s | page=%d | total=%d", name[:40], page, len(all_reviews))
                driver.get(url)
                sleep(4, 7)

                if is_amazon_blocked(driver):
                    if not login_handled:
                        wait_for_user(
                            "Amazon is showing a login wall.\n"
                            "Please log in to your Amazon account in the open browser."
                        )
                        login_handled = True
                        driver.get(url)
                        sleep(5, 8)
                    if is_amazon_blocked(driver):
                        log.warning("Still blocked — skipping '%s'", name)
                        break

                try:
                    # Wait for either known review container selector
                    WebDriverWait(driver, 25).until(
                        lambda d: d.find_elements(By.CSS_SELECTOR, "div[data-hook='review']")
                        or d.find_elements(By.CSS_SELECTOR, "div[id^='customer_review']")
                        or d.find_elements(By.CSS_SELECTOR, "span[data-hook='review-body']")
                    )
                except TimeoutException:
                    log.warning("Timeout waiting for reviews on page %d — parsing anyway", page)

                sleep(2, 3)
                page_reviews = _parse_amazon_page(driver, name)
                if not page_reviews:
                    log.info("  No reviews on page %d — next product.", page)
                    break

                all_reviews.extend(page_reviews)
                collected += len(page_reviews)
                log.info("  +%d reviews | product total: %d", len(page_reviews), collected)
                page += 1
                sleep(3, 6)

            sleep(4, 8)

    finally:
        driver.quit()

    return all_reviews[:target]


# ─── Flipkart ─────────────────────────────────────────────────────────────────

def is_flipkart_blocked(driver) -> bool:
    src = driver.page_source[:5000].lower()
    return "recaptcha" in src or "verify" in driver.title.lower()


def _discover_flipkart_products(driver, query: str, max_products: int = 2) -> list[tuple[str, str]]:
    """
    Search Flipkart for a query, open each product page, and extract
    the live product-reviews URL from the 'All reviews' link.
    Returns list of (review_base_url, product_name).
    """
    search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
    log.info("  Searching Flipkart: %s", search_url)
    driver.get(search_url)
    sleep(3, 5)

    soup = BeautifulSoup(driver.page_source, "lxml")

    # Collect product page links from search results
    product_links = []
    for a in soup.select("a[href*='/p/']"):
        href = a.get("href", "")
        if href and "/p/" in href:
            full = "https://www.flipkart.com" + href if href.startswith("/") else href
            # Strip query params to get a clean product URL
            full = full.split("?")[0]
            if full not in product_links:
                product_links.append(full)
        if len(product_links) >= max_products * 3:
            break

    results = []
    for product_url in product_links[:max_products * 3]:
        if len(results) >= max_products:
            break
        log.info("  Checking product page: %s", product_url)
        driver.get(product_url)
        sleep(3, 5)

        psoup = BeautifulSoup(driver.page_source, "lxml")

        # Extract product name from title tag or h1
        name_el = psoup.select_one("h1.yhB1nd, span.B_NuCI, h1")
        name = name_el.get_text(strip=True)[:60] if name_el else query

        # Find the "All X Reviews" link which leads to product-reviews page
        review_link = None
        for a in psoup.find_all("a", href=True):
            href = a["href"]
            if "product-reviews" in href:
                review_link = "https://www.flipkart.com" + href if href.startswith("/") else href
                # Remove page param — we'll add it ourselves
                review_link = review_link.split("&page=")[0].split("?page=")[0]
                break

        if review_link:
            log.info("  Found review URL for '%s': %s", name, review_link)
            results.append((review_link, name))
        else:
            log.info("  No review link found for '%s' — skipping", name)

        sleep(2, 3)

    return results


def _parse_flipkart_page(driver, product_name: str) -> list[Review]:
    # Scroll to trigger lazy-loaded content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "lxml")
    reviews = []
    BAD_PHRASES = {"add to cart", "buy now", "log in", "sign in", "emi available",
                   "search for", "sort by", "filter"}

    # Anchor on "Certified Buyer" — the one element present on every Flipkart review
    certified_els = [
        el for el in soup.find_all(["span", "div", "p"])
        if "Certified Buyer" in el.get_text(strip=True)
        and len(el.get_text(strip=True)) < 30   # exclude large containers
    ]
    log.info("  Flipkart: found %d 'Certified Buyer' markers", len(certified_els))

    for cert_el in certified_els:
        # Walk up until we reach a container with enough text to be a review card
        card = cert_el
        for _ in range(8):
            card = card.parent
            if card is None:
                break
            if len(card.get_text(separator=" ", strip=True)) > 100:
                break

        if card is None:
            continue

        # Longest text block in the card = review body
        body = ""
        for el in card.find_all(["p", "div", "span"]):
            if el.find(["p", "div", "span"]):
                continue          # skip container elements, leaf nodes only
            txt = el.get_text(strip=True)
            if len(txt) > len(body) and 20 < len(txt) < 3000:
                if not any(ph in txt.lower() for ph in BAD_PHRASES):
                    body = txt

        if not body:
            continue

        # Star rating: leaf element with a single digit 1–5
        rating = None
        for el in card.find_all(["div", "span"]):
            txt = el.get_text(strip=True)
            if txt in ("1", "2", "3", "4", "5") and not el.find():
                rating = txt
                break

        # Review title: short text ≠ body, not "Certified Buyer"
        title = None
        for el in card.find_all(["p", "span", "div"]):
            txt = el.get_text(strip=True)
            if 8 < len(txt) < 120 and txt != body and "Certified" not in txt and not el.find():
                title = txt
                break

        # Reviewer name: short text near "Certified Buyer"
        reviewer = None
        for el in cert_el.parent.find_all(["span", "div", "p"]) if cert_el.parent else []:
            txt = el.get_text(strip=True)
            if 2 < len(txt) < 50 and "Certified" not in txt and txt != body and not el.find():
                reviewer = txt
                break

        reviews.append(Review(
            source="flipkart",
            product=product_name,
            rating=rating,
            title=title,
            review_text=body,
            reviewer=reviewer,
            date=None,
        ))

    # Deduplicate by review_text
    seen: set[str] = set()
    deduped = []
    for r in reviews:
        if r.review_text not in seen:
            seen.add(r.review_text)
            deduped.append(r)

    log.info("  Flipkart parsed %d reviews from page", len(deduped))
    return deduped


def scrape_flipkart(target: int = 500) -> list[Review]:
    driver = build_driver()
    all_reviews: list[Review] = []
    captcha_handled = False

    try:
        # Discover live product review URLs dynamically
        log.info("Discovering Flipkart products from search...")
        discovered: list[tuple[str, str]] = []
        for query in FLIPKART_SEARCH_QUERIES:
            discovered.extend(_discover_flipkart_products(driver, query, max_products=2))
            sleep(2, 4)
            if len(discovered) >= 12:
                break

        # Deduplicate by review URL
        seen_urls: set[str] = set()
        products = []
        for url, name in discovered:
            if url not in seen_urls:
                seen_urls.add(url)
                products.append((url, name))

        log.info("Discovered %d unique Flipkart products to scrape.", len(products))
        per_product = max(10, (target // max(len(products), 1)) + 10)

        for base_url, name in products:
            if len(all_reviews) >= target:
                break
            collected, page = 0, 1

            while collected < per_product:
                # Flipkart review pagination: ?page=N or &page=N
                sep = "&" if "?" in base_url else "?"
                url = f"{base_url}{sep}page={page}"
                log.info("Flipkart | %-35s | page=%d | total=%d", name[:35], page, len(all_reviews))
                driver.get(url)
                sleep(3, 6)

                if is_flipkart_blocked(driver):
                    if not captcha_handled:
                        wait_for_user(
                            "Flipkart is showing a CAPTCHA or verification page.\n"
                            "Please solve it in the open browser."
                        )
                        captcha_handled = True
                        driver.get(url)
                        sleep(4, 7)
                    if is_flipkart_blocked(driver):
                        log.warning("Still blocked — skipping '%s'", name)
                        break

                # Check for E002 / "Something went wrong" error page
                if "something went wrong" in driver.page_source.lower() or \
                   "E002" in driver.page_source:
                    log.warning("  Flipkart error page (E002) on page %d — skipping product", page)
                    break

                try:
                    # Wait until "Certified Buyer" text is present — reliable across all Flipkart designs
                    WebDriverWait(driver, 30).until(
                        lambda d: "Certified Buyer" in d.page_source
                    )
                except TimeoutException:
                    log.warning("  Timeout on page %d for '%s' — parsing anyway", page, name)

                sleep(2, 4)
                page_reviews = _parse_flipkart_page(driver, name)
                if not page_reviews:
                    log.info("  No reviews on page %d — next product.", page)
                    break

                all_reviews.extend(page_reviews)
                collected += len(page_reviews)
                log.info("  +%d reviews | product total: %d", len(page_reviews), collected)
                page += 1
                sleep(3, 6)

            sleep(4, 8)

    finally:
        driver.quit()

    return all_reviews[:target]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Amazon already scraped — only run Flipkart
    log.info("=== Flipkart scrape (target=%d) ===", TARGET_PER_PLATFORM)
    log.info("Chrome profile: %s", CHROME_PROFILE_DIR)
    flipkart_reviews = scrape_flipkart(TARGET_PER_PLATFORM)
    save_csv(flipkart_reviews, os.path.join(OUTPUT_DIR, "flipkart_reviews.csv"))
    log.info("Flipkart collected: %d", len(flipkart_reviews))

    # Merge with existing Amazon reviews if available
    amazon_path = os.path.join(OUTPUT_DIR, "amazon_reviews.csv")
    amazon_reviews = []
    if os.path.exists(amazon_path):
        import csv as _csv
        with open(amazon_path, encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                amazon_reviews.append(row)
        log.info("Loaded %d existing Amazon reviews from %s", len(amazon_reviews), amazon_path)

    # Save combined CSV
    all_path = os.path.join(OUTPUT_DIR, "all_reviews.csv")
    with open(all_path, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=[field.name for field in fields(Review)])
        writer.writeheader()
        for row in amazon_reviews:
            writer.writerow(row)
        for r in flipkart_reviews:
            writer.writerow(asdict(r))
    log.info("Combined CSV saved → %s  (Amazon=%d | Flipkart=%d | Total=%d)",
             all_path, len(amazon_reviews), len(flipkart_reviews),
             len(amazon_reviews) + len(flipkart_reviews))


if __name__ == "__main__":
    main()
