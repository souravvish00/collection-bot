from playwright.sync_api import sync_playwright
import pandas as pd
import time

KEYWORDS = [
    "Accounts Executive",
    "Commerce Graduate",
    "Business Analyst",
    "Accountant",
    "Finance Executive",
    "B.Com",
    "Accounts Manager"
]

all_data = []

with sync_playwright() as p:

    browser = p.chromium.launch_persistent_context(
        user_data_dir="linkedin_profile",
        headless=False
    )

    page = browser.new_page()

    page.set_default_timeout(60000)

    # LOGIN
    page.goto("https://www.linkedin.com/login")

    print("Login manually then press ENTER")
    input()

    for keyword in KEYWORDS:

        try:

            print(f"\nSearching: {keyword}")

            search_url = (
                f"https://www.linkedin.com/search/results/people/?keywords={keyword}"
            )

            page.goto(search_url)

            page.wait_for_timeout(5000)

            # SCROLL
            for i in range(6):

                page.mouse.wheel(0, 12000)

                page.wait_for_timeout(1500)

            # GET ALL PROFILE LINKS
            profile_elements = page.locator(
                'a[href*="/in/"]'
            ).all()

            print(f"Found {len(profile_elements)} links")

            seen = set()

            for element in profile_elements:

                try:

                    profile = element.get_attribute("href")

                    if not profile:
                        continue

                    profile = profile.split("?")[0]

                    if not profile.startswith("https://"):

                        profile = (
                            "https://www.linkedin.com" + profile
                        )

                    # REMOVE DUPLICATES
                    if profile in seen:
                        continue

                    seen.add(profile)

                    # GET NAME
                    name = element.inner_text().strip()

                    # SKIP BLANKS
                    if len(name) < 2:
                        continue

                    # GET CARD
                    parent = element.locator("xpath=ancestor::div[contains(@class,'entity-result')]").first

                    headline = "N/A"

                    try:

                        headline = parent.locator(
                            'div.t-14'
                        ).first.inner_text().strip()

                    except:
                        pass

                    data = {
                        "Search Keyword": keyword,
                        "Candidate Name": name,
                        "Professional Title": headline,
                        "LinkedIn Profile": profile
                    }

                    # REMOVE GLOBAL DUPLICATES
                    already_exists = any(
                        d["LinkedIn Profile"] == profile
                        for d in all_data
                    )

                    if not already_exists:

                        all_data.append(data)

                        print(data)

                except Exception as e:

                    print("PROFILE ERROR:", e)

            # SAVE EXCEL
            df = pd.DataFrame(all_data)

            df.to_excel(
                "linkedin_fast_data.xlsx",
                index=False
            )

            print(f"\nSaved {len(all_data)} profiles")

        except Exception as e:

            print("SEARCH ERROR:", e)

    browser.close()

    print("\nALL DATA SAVED")