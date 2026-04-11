"""
Review Scraper — Google Play Store & Amazon (via requests)
---------------------------------------------------------------
Amazon/Flipkart block scrapers with login walls and reCAPTCHA.
We use:
  - Google Play Store  : google-play-scraper library (no login, no CAPTCHA)
  - Amazon.com         : requests + BeautifulSoup on public review pages

Collects 500 reviews from each source and saves:
  - google_play_reviews.csv
  - amazon_reviews.csv
  - all_reviews.csv  (combined)

Usage:
    python scraper.py
"""

import csv
import time
import random
import logging
import os
from dataclasses import dataclass, fields, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup
from google_play_scraper import reviews, Sort

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

TARGET_PER_PLATFORM = 500
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Google Play app IDs (popular Indian apps with lots of reviews)
PLAY_APPS = [
    ("com.amazon.mShop.android.shopping", "Amazon Shopping"),
    ("com.flipkart.android",              "Flipkart"),
    ("com.myntra.android",                "Myntra"),
    ("com.phonepe.app",                   "PhonePe"),
    ("in.swiggy.android",                 "Swiggy"),
    ("com.zomato.android",                "Zomato"),
    ("com.meesho.supply",                 "Meesho"),
    ("com.snapdeal.main",                 "Snapdeal"),
]

# Steam game app IDs (popular games with thousands of English reviews)
STEAM_APPS = [
    ("570",    "Dota 2"),
    ("730",    "CS2"),
    ("440",    "Team Fortress 2"),
    ("578080", "PUBG"),
    ("1091500","Cyberpunk 2077"),
    ("1172470","Apex Legends"),
    ("892970", "Valheim"),
    ("1245620","Elden Ring"),
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

def save_csv(reviews_list: list, path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[f.name for f in fields(Review)])
        writer.writeheader()
        for r in reviews_list:
            writer.writerow(asdict(r))
    log.info("Saved %d reviews → %s", len(reviews_list), path)


def sleep(lo: float = 1.5, hi: float = 3.5):
    time.sleep(random.uniform(lo, hi))


# ─── Google Play Scraper ──────────────────────────────────────────────────────

def scrape_google_play(target: int = 500) -> list[Review]:
    all_reviews: list[Review] = []
    per_app = (target // len(PLAY_APPS)) + 20

    for app_id, app_name in PLAY_APPS:
        if len(all_reviews) >= target:
            break

        log.info("Play Store: scraping '%s' (target per app: %d)", app_name, per_app)
        try:
            result, _ = reviews(
                app_id,
                lang="en",
                country="in",
                sort=Sort.MOST_RELEVANT,
                count=per_app,
            )

            for r in result:
                body = (r.get("content") or "").strip()
                if not body:
                    continue
                all_reviews.append(Review(
                    source="google_play",
                    product=app_name,
                    rating=str(r.get("score", "")),
                    title=None,
                    review_text=body,
                    reviewer=r.get("userName"),
                    date=str(r.get("at", ""))[:10],
                ))

            log.info("  Got %d reviews | total: %d", len(result), len(all_reviews))

        except Exception as e:
            log.warning("Failed for app '%s': %s", app_name, e)

        sleep(1, 2)

    return all_reviews[:target]


# ─── Steam Scraper (public JSON API, no login) ───────────────────────────────

STEAM_API = "https://store.steampowered.com/appreviews/{app_id}"
STEAM_PARAMS = {
    "json": "1",
    "filter": "recent",
    "language": "english",
    "num_per_page": "100",
}


def scrape_steam(target: int = 500) -> list[Review]:
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    all_reviews: list[Review] = []
    per_app = (target // len(STEAM_APPS)) + 20

    for app_id, app_name in STEAM_APPS:
        if len(all_reviews) >= target:
            break

        collected = 0
        cursor = "*"
        log.info("Steam: scraping '%s' (target per app: %d)", app_name, per_app)

        while collected < per_app:
            params = {**STEAM_PARAMS, "cursor": cursor}
            try:
                resp = session.get(
                    STEAM_API.format(app_id=app_id), params=params, timeout=15
                )
                data = resp.json()
            except Exception as e:
                log.warning("Steam error for '%s': %s", app_name, e)
                break

            batch = data.get("reviews", [])
            if not batch:
                log.info("  No more reviews for '%s'.", app_name)
                break

            for r in batch:
                body = (r.get("review") or "").strip()
                if not body or len(body) < 5:
                    continue
                all_reviews.append(Review(
                    source="steam",
                    product=app_name,
                    rating="positive" if r.get("voted_up") else "negative",
                    title=None,
                    review_text=body,
                    reviewer=str(r.get("author", {}).get("steamid", "")),
                    date=str(r.get("timestamp_created", ""))[:10],
                ))
                collected += 1

            log.info("  Got %d reviews | total: %d", len(batch), len(all_reviews))
            cursor = data.get("cursor", "")
            if not cursor:
                break
            sleep(1, 2)

        sleep(2, 3)

    return all_reviews[:target]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Google Play Store scrape (target=%d) ===", TARGET_PER_PLATFORM)
    play_reviews = scrape_google_play(TARGET_PER_PLATFORM)
    save_csv(play_reviews, os.path.join(OUTPUT_DIR, "google_play_reviews.csv"))
    log.info("Google Play collected: %d", len(play_reviews))

    log.info("=== Steam scrape (target=%d) ===", TARGET_PER_PLATFORM)
    steam_reviews = scrape_steam(TARGET_PER_PLATFORM)
    save_csv(steam_reviews, os.path.join(OUTPUT_DIR, "steam_reviews.csv"))
    log.info("Steam collected: %d", len(steam_reviews))

    # Combined dataset
    all_reviews = play_reviews + steam_reviews
    save_csv(all_reviews, os.path.join(OUTPUT_DIR, "all_reviews.csv"))
    log.info("Done! Google Play=%d | Steam=%d | Total=%d",
             len(play_reviews), len(steam_reviews), len(all_reviews))


if __name__ == "__main__":
    main()
