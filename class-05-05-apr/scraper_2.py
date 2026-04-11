"""
scraper_2.py — Amazon India & Flipkart Review Scraper (Selenium)
-----------------------------------------------------------------
Uses undetected-chromedriver to bypass bot detection.
A persistent Chrome profile is used so you only need to log in ONCE.

Strategy:
  - On the first run, if a login/CAPTCHA page is detected, the script PAUSES
    and prints a message — you solve it manually in the open browser, then
    press ENTER in the terminal to continue.
  - On subsequent runs the saved session/cookies are reused automatically.

Usage:
    python scraper_2.py

Output (in class-05-05-apr/):
    amazon_product_reviews.csv
    flipkart_product_reviews.csv
    all_product_reviews.csv
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
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

TARGET_PER_PLATFORM = 500
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Persistent Chrome profile directory (keeps login sessions between runs)
CHROME_PROFILE_DIR = os.path.join(OUTPUT_DIR, "chrome_profile")

# ── Amazon ──
# Search queries — ASINs are discovered dynamically from Amazon.in search results
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

# ── Flipkart ──
# Format: (review_url, product_name)
# URL pattern: flipkart.com/{slug}/product-reviews/{item-id}?pid={pid}
FLIPKART_PRODUCTS = [
    (
        "https://www.flipkart.com/samsung-galaxy-m14-5g/product-reviews/itm33fcb510d0ba3?pid=MOBGMFHRJQHZFEMP&lid=LSTMOBGMFHRJQHZFEMP",
        "Samsung Galaxy M14 5G",
    ),
    (
        "https://www.flipkart.com/oneplus-nord-ce-3-lite-5g/product-reviews/itma27b2cd0bd3b53?pid=MOBGMFHRGZHHKFHF&lid=LSTMOBGMFHRGZHHKFHF",
        "OnePlus Nord CE 3 Lite",
    ),
    (
        "https://www.flipkart.com/redmi-note-13-5g/product-reviews/itm6e9c4b8f1fa8f?pid=MOBGRHN3JBGHYYGP",
        "Redmi Note 13 5G",
    ),
    (
        "https://www.flipkart.com/boat-airdopes-141/product-reviews/itm9baf1c4a7ba86?pid=ACCGXZZYHUJXPB6W",
        "boAt Airdopes 141",
    ),
    (
        "https://www.flipkart.com/hp-15s-eq2144au-ryzen-5-hexa-core-5500u-8-gb-512-gb-ssd-windows-11-home-laptop/product-reviews/itm9b35e55c83e38?pid=COMGPPHQGHF5PKJF",
        "HP 15s Laptop",
    ),
]


# ─── Data model ──────────────────────────────────────────────────────────────

@dataclass
class Review:
    source: str
    product: str
    rating: Optional[str]
    title: Optional[str]
    review_text: str
    reviewer: Optional[str]
    date: Optional[str]


# ─── Helpers ─────────────────────────────────────────────────────────────────

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
    """undetected-chromedriver with a persistent profile."""
    os.makedirs(CHROME_PROFILE_DIR, exist_ok=True)
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=en-IN")
    options.add_argument("--disable-notifications")
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=146)
    return driver


def wait_for_user(driver, message: str):
    """Pause and let the user resolve login / CAPTCHA manually."""
    print("\n" + "=" * 60)
    print(message)
    print("After resolving it in the browser, come back here and")
    print("press ENTER to continue...")
    print("=" * 60)
    input()


def is_amazon_blocked(driver) -> bool:
    url = driver.current_url
    title = driver.title
    return (
        "ap/signin" in url
        or "Sign-In" in title
        or "Enter the characters" in driver.page_source[:3000]
    )


def is_flipkart_blocked(driver) -> bool:
    return (
        "recaptcha" in driver.page_source[:5000].lower()
        or "verify" in driver.title.lower()
    )


# ─── Amazon Scraper ───────────────────────────────────────────────────────────

def _parse_amazon_page(driver, product_name: str) -> list[Review]:
    soup = BeautifulSoup(driver.page_source, "lxml")
    reviews = []

    for card in soup.select("div[data-hook='review']"):
        rating_el = card.select_one("i[data-hook='review-star-rating'] span.a-icon-alt")
        title_el  = card.select_one("a[data-hook='review-title'] span:not(.a-icon-alt)")
        body_el   = card.select_one("span[data-hook='review-body'] span")
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


def _discover_asins(driver, query: str, max_products: int = 2) -> list[tuple[str, str]]:
    """Search Amazon.in, skip sponsored ads, return real product ASINs."""
    search_url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    log.info("  Searching: %s", search_url)
    driver.get(search_url)
    sleep(3, 5)

    soup = BeautifulSoup(driver.page_source, "lxml")
    products = []

    # Only real search result divs — skip ads/sponsored
    for item in soup.select("div[data-component-type='s-search-result']"):
        # Skip sponsored items
        if item.select_one("span.s-label-popover-default, .puis-sponsored-label-text"):
            continue
        asin = item.get("data-asin", "").strip()
        if not asin or len(asin) != 10:
            continue
        name_el = item.select_one("h2 span.a-text-normal, h2 a span")
        name = name_el.get_text(strip=True)[:60] if name_el else query
        products.append((asin, name))
        if len(products) >= max_products:
            break

    log.info("  Found %d non-sponsored products for '%s'", len(products), query)
    return products


def scrape_amazon(target: int = 500) -> list[Review]:
    driver = build_driver()
    all_reviews: list[Review] = []
    login_handled = False

    try:
        # Step 1: Discover valid ASINs from search results
        log.info("Discovering ASINs from Amazon.in search...")
        discovered: list[tuple[str, str]] = []
        for query in AMAZON_SEARCH_QUERIES:
            discovered.extend(_discover_asins(driver, query, max_products=2))
            sleep(2, 4)

        # Deduplicate by ASIN
        seen = set()
        products = []
        for asin, name in discovered:
            if asin not in seen:
                seen.add(asin)
                products.append((asin, name))

        log.info("Discovered %d unique products to scrape.", len(products))
        per_product = max(10, (target // max(len(products), 1)) + 10)

        # Step 2: Scrape reviews for each discovered product
        for asin, name in products:
            if len(all_reviews) >= target:
                break

            collected = 0
            page = 1

            while collected < per_product:
                url = (
                    f"https://www.amazon.in/product-reviews/{asin}/"
                    f"ref=cm_cr_dp_d_show_all_btm"
                    f"?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
                )
                log.info("Amazon | %-40s | page=%d | total=%d", name[:40], page, len(all_reviews))
                driver.get(url)
                sleep(4, 7)

                log.info("  Title: %s", driver.title[:80])

                # Handle login wall (pause and ask user once)
                if is_amazon_blocked(driver):
                    if not login_handled:
                        wait_for_user(
                            driver,
                            "Amazon is asking for login.\n"
                            "Please log in to your Amazon account in the browser window.\n"
                            "After logging in, come back here and press ENTER."
                        )
                        login_handled = True
                        driver.get(url)
                        sleep(5, 8)
                    if is_amazon_blocked(driver):
                        log.warning("Still blocked — skipping %s", name)
                        break

                # Wait for review cards
                try:
                    WebDriverWait(driver, 25).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "div[data-hook='review']")
                        )
                    )
                except TimeoutException:
                    log.warning("Timeout on page %d — trying to parse anyway", page)

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


# ─── Flipkart Scraper ─────────────────────────────────────────────────────────

def _parse_flipkart_page(driver, product_name: str) -> list[Review]:
    soup = BeautifulSoup(driver.page_source, "lxml")
    reviews = []

    # ── Strategy: find review containers structurally ──
    # Each review on Flipkart has a numeric star rating (1-5) in a small div
    # and a paragraph of text. We anchor on the rating div and walk up to
    # find the review container, then extract text from siblings.

    # Find all star-rating elements (small divs with a single digit 1-5)
    rating_divs = []
    for div in soup.find_all("div"):
        txt = div.get_text(strip=True)
        # A rating div is tiny — just "1"–"5"
        if txt in ("1","2","3","4","5") and len(div.get_text()) <= 2:
            rating_divs.append(div)

    BAD_PHRASES = {"add to cart", "buy now", "log in", "sign in",
                   "flipkart", "seller", "delivery", "emi available"}

    for r_div in rating_divs:
        # Walk up to find the review card container (2-4 levels up)
        card = r_div
        for _ in range(5):
            card = card.parent
            if card is None:
                break
            # The card should contain at least 30 chars of review text
            card_text = card.get_text(separator=" ", strip=True)
            if len(card_text) > 80:
                break

        if card is None:
            continue

        # Extract the longest meaningful text block as the review body
        body = ""
        for el in card.find_all(["p", "div", "span"]):
            if el.find(["p", "div", "span"]):
                continue
            txt = el.get_text(strip=True)
            if len(txt) > len(body) and 20 < len(txt) < 3000:
                body = txt

        if not body:
            continue
        if any(ph in body.lower() for ph in BAD_PHRASES):
            continue

        # Title: short text (10-80 chars) that isn't the body
        title = None
        for el in card.find_all(["p", "span"]):
            txt = el.get_text(strip=True)
            if 8 < len(txt) < 80 and txt != body:
                title = txt
                break

        reviews.append(Review(
            source="flipkart",
            product=product_name,
            rating=r_div.get_text(strip=True),
            title=title,
            review_text=body,
            reviewer=None,
            date=None,
        ))

    # Deduplicate by review_text
    seen = set()
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
    per_product = (target // len(FLIPKART_PRODUCTS)) + 20
    captcha_handled = False

    try:
        for base_url, name in FLIPKART_PRODUCTS:
            if len(all_reviews) >= target:
                break

            collected = 0
            page = 1

            while collected < per_product:
                url = f"{base_url}&page={page}"
                log.info("Flipkart | %-30s | page=%d | total=%d", name, page, len(all_reviews))
                driver.get(url)
                sleep(3, 6)

                # Handle reCAPTCHA (ask user once)
                if is_flipkart_blocked(driver):
                    if not captcha_handled:
                        wait_for_user(
                            driver,
                            "Flipkart is showing a CAPTCHA or verification page.\n"
                            "Please solve it in the browser window."
                        )
                        captcha_handled = True
                        driver.get(url)
                        sleep(4, 7)
                    if is_flipkart_blocked(driver):
                        log.warning("Still blocked after CAPTCHA — skipping %s", name)
                        break

                # Wait for review cards
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR,
                             "div._27M-vq, div.RcXBOT, div.col.EPCmJX, div._23sxH9, div.XQDdHH")
                        )
                    )
                except TimeoutException:
                    log.warning("Timeout on page %d for '%s'", page, name)
                    break

                sleep(2, 4)
                page_reviews = _parse_flipkart_page(driver, name)

                if not page_reviews:
                    log.info("No reviews on page %d — moving to next product.", page)
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
    log.info("=== Amazon scrape (target=%d) ===", TARGET_PER_PLATFORM)
    log.info("Chrome profile saved at: %s", CHROME_PROFILE_DIR)
    log.info("If login is required, the script will pause and wait for you.")
    amazon_reviews = scrape_amazon(TARGET_PER_PLATFORM)
    save_csv(amazon_reviews, os.path.join(OUTPUT_DIR, "amazon_product_reviews.csv"))
    log.info("Amazon collected: %d", len(amazon_reviews))

    log.info("=== Flipkart scrape (target=%d) ===", TARGET_PER_PLATFORM)
    flipkart_reviews = scrape_flipkart(TARGET_PER_PLATFORM)
    save_csv(flipkart_reviews, os.path.join(OUTPUT_DIR, "flipkart_product_reviews.csv"))
    log.info("Flipkart collected: %d", len(flipkart_reviews))

    all_reviews = amazon_reviews + flipkart_reviews
    save_csv(all_reviews, os.path.join(OUTPUT_DIR, "all_product_reviews.csv"))
    log.info("Done! Amazon=%d | Flipkart=%d | Total=%d",
             len(amazon_reviews), len(flipkart_reviews), len(all_reviews))


if __name__ == "__main__":
    main()
