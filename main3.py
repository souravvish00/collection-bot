from __future__ import annotations

import csv
import datetime as dt
import time
from pathlib import Path
from urllib.parse import quote_plus

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


# =========================
# PATH SETUP
# =========================

ROOT = Path(__file__).resolve().parent

DATA_DIR = ROOT / "data"
PROFILE_DIR = ROOT / "browser_profile"

KEYWORDS_CSV = DATA_DIR / "keywords.csv"
PROSPECTS_CSV = DATA_DIR / "prospects.csv"


# =========================
# CSV HEADERS
# =========================

KEYWORD_HEADERS = ["keyword", "location"]

PROSPECT_HEADERS = [
    "name",
    "headline",
    "profile_url",
    "search_keyword",
    "collected_date",
]


# =========================
# CSV HELPERS
# =========================

def read_csv(path: Path):
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)

        writer.writeheader()
        writer.writerows(rows)


# =========================
# CREATE FILES
# =========================

def create_default_files():

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not KEYWORDS_CSV.exists():

        write_csv(
            KEYWORDS_CSV,
            KEYWORD_HEADERS,
            [
                {
                    "keyword": "MBA students",
                    "location": "India",
                },
                {
                    "keyword": "Data Analyst",
                    "location": "Bangalore",
                },
                {
                    "keyword": "Python Developer",
                    "location": "India",
                },
            ],
        )

        print(f"Created: {KEYWORDS_CSV}")

    if not PROSPECTS_CSV.exists():

        write_csv(
            PROSPECTS_CSV,
            PROSPECT_HEADERS,
            [],
        )

        print(f"Created: {PROSPECTS_CSV}")


# =========================
# LOAD KEYWORDS
# =========================

def get_keywords():

    rows = read_csv(KEYWORDS_CSV)

    final_rows = []

    for row in rows:

        keyword = row.get("keyword", "").strip()
        location = row.get("location", "").strip()

        if keyword:
            final_rows.append({
                "keyword": keyword,
                "location": location,
            })

    return final_rows


# =========================
# LOAD OLD PROSPECTS
# =========================

def get_old_prospects():

    rows = read_csv(PROSPECTS_CSV)

    urls = set()

    for row in rows:

        url = row.get("profile_url", "").strip()

        if url:
            urls.add(url)

    return rows, urls


# =========================
# DATE
# =========================

def today():

    return dt.date.today().isoformat()


# =========================
# PLAYWRIGHT INSTALL HELP
# =========================

def print_install_help():

    print("\nPlaywright not installed.\n")

    print("Run these commands:\n")

    print("pip install playwright")
    print("python -m playwright install")


# =========================
# AUTO SCRAPER
# =========================

def auto_collect_leads():

    if sync_playwright is None:
        print_install_help()
        return

    create_default_files()

    keywords = get_keywords()

    if not keywords:
        print("No keywords found.")
        return

    prospects, existing_urls = get_old_prospects()

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            viewport={
                "width": 1400,
                "height": 900,
            },
        )

        page = browser.new_page()

        print("\nLinkedIn automation started...\n")

        for item in keywords:

            keyword = item["keyword"]
            location = item["location"]

            query = keyword

            if location:
                query += f" {location}"

            search_url = (
                "https://www.linkedin.com/search/results/people/?keywords="
                + quote_plus(query)
            )

            print(f"\nSearching: {query}")

            page.goto(
                search_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            # wait for page load
            time.sleep(8)

            # scroll for loading more profiles
            for _ in range(5):

                page.mouse.wheel(0, 5000)

                time.sleep(2)

            # get profile links
            profile_elements = page.locator(
                "a[href*='/in/']"
            ).all()

            collected = 0

            for element in profile_elements:

                try:

                    href = element.get_attribute("href")

                    if not href:
                        continue

                    if "/in/" not in href:
                        continue

                    clean_url = href.split("?")[0].strip()

                    if clean_url in existing_urls:
                        continue

                    name = element.inner_text().strip()

                    if not name:
                        continue

                    headline = ""

                    try:

                        parent = element.locator("xpath=../../../..")

                        text = parent.inner_text()

                        lines = text.split("\n")

                        if len(lines) >= 2:
                            headline = lines[1]

                    except:
                        pass

                    row = {
                        "name": name,
                        "headline": headline,
                        "profile_url": clean_url,
                        "search_keyword": query,
                        "collected_date": today(),
                    }

                    prospects.append(row)

                    existing_urls.add(clean_url)

                    collected += 1

                    print(f"Collected: {name}")

                except Exception as e:

                    print("Skipped profile:", e)

            # save every keyword cycle
            write_csv(
                PROSPECTS_CSV,
                PROSPECT_HEADERS,
                prospects,
            )

            print(f"Saved {collected} profiles.\n")

            time.sleep(5)

        browser.close()

    print("\nCompleted Successfully.")
    print(f"\nSaved File: {PROSPECTS_CSV}")


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    auto_collect_leads()