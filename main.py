from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re

KEYWORDS = [
    "Accounts",
    "Commerce",
    "Business Analyst"
]

all_data = []


# EXTRACT EMAIL
def extract_email(text):

    emails = re.findall(
        r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        text
    )

    return list(set(emails))


# EXTRACT PHONE
def extract_phone(text):

    phones = re.findall(
        r'(\+?\d[\d\s\-\(\)]{8,}\d)',
        text
    )

    cleaned = []

    for p in phones:

        p = p.strip()

        if len(p) >= 10:
            cleaned.append(p)

    return list(set(cleaned))


with sync_playwright() as p:

    browser = p.chromium.launch_persistent_context(
        user_data_dir="linkedin_profile",
        headless=False,
        viewport={"width": 1400, "height": 900}
    )

    page = browser.new_page()

    # BIG TIMEOUT
    page.set_default_timeout(120000)
    page.set_default_navigation_timeout(120000)

    # LOGIN
    page.goto("https://www.linkedin.com/login")

    print("Login manually and press ENTER")
    input()

    # MAIN LOOP
    for keyword in KEYWORDS:

        print(f"\nSearching for: {keyword}")

        search_url = (
            f"https://www.linkedin.com/search/results/people/?keywords={keyword}"
        )

        page.goto(search_url)

        page.wait_for_timeout(8000)

        # SCROLL SEARCH PAGE
        for i in range(30):

            page.mouse.wheel(0, 15000)

            page.wait_for_timeout(2500)

        # GET PROFILE LINKS
        profile_links = []

        links = page.locator("a[href*='/in/']").all()

        seen = set()

        for link in links:

            try:

                href = link.get_attribute("href")

                if href:

                    clean = href.split("?")[0]

                    if "/in/" in clean:

                        if not clean.startswith("https://"):
                            clean = "https://www.linkedin.com" + clean

                        if clean not in seen:

                            seen.add(clean)

                            profile_links.append(clean)

            except:
                pass

        print(f"Found {len(profile_links)} profiles")

        # OPEN EVERY PROFILE
        for profile in profile_links:

            try:

                print(f"\nOpening Profile: {profile}")

                page.goto(profile)

                page.wait_for_timeout(7000)

                # SCROLL PROFILE
                for i in range(3):

                    page.mouse.wheel(0, 4000)

                    page.wait_for_timeout(2000)

                # NAME
                try:
                    name = page.locator("h1").first.inner_text().strip()
                except:
                    name = "N/A"

                # HEADLINE
                try:
                    headline = page.locator(
                        "div.text-body-medium"
                    ).first.inner_text().strip()
                except:
                    headline = "N/A"

                # ABOUT SECTION
                about = "N/A"

                try:

                    about = page.locator(
                        "section"
                    ).filter(has_text="About").inner_text()

                except:
                    pass

                # DEFAULTS
                email = []
                phone = []
                website = []
                contact_text = ""

                # OPEN CONTACT INFO
                try:

                    contact_button = page.locator(
                        'a[href*="overlay/contact-info"]'
                    ).first

                    if contact_button.count() > 0:

                        print("Opening Contact Info")

                        contact_button.click()

                        page.wait_for_timeout(5000)

                        # GET CONTACT DATA
                        try:

                            contact_popup = page.locator(
                                "section.pv-contact-info"
                            )

                            contact_text = contact_popup.inner_text()

                            print(contact_text)

                            # EXTRACT EMAIL
                            email = extract_email(contact_text)

                            # EXTRACT PHONE
                            phone = extract_phone(contact_text)

                            # EXTRACT WEBSITE
                            website = re.findall(
                                r'https?://[^\s]+',
                                contact_text
                            )

                        except Exception as e:

                            print("Cannot Read Contact")

                        # CLOSE CONTACT POPUP
                        page.keyboard.press("Escape")

                        page.wait_for_timeout(2000)

                except Exception as e:

                    print("No Contact Info")

                # IF NO EMAIL FOUND TRY WHOLE PAGE
                if len(email) == 0:

                    try:

                        body = page.locator("body").inner_text()

                        email = extract_email(body)

                    except:
                        pass

                # IF NO PHONE FOUND TRY WHOLE PAGE
                if len(phone) == 0:

                    try:

                        body = page.locator("body").inner_text()

                        phone = extract_phone(body)

                    except:
                        pass

                # SAVE ONLY VALID DATA
                data = {
                    "Keyword": keyword,
                    "Name": name,
                    "Headline": headline,
                    "About": about,
                    "Email": ", ".join(email) if email else "N/A",
                    "Phone": ", ".join(phone) if phone else "N/A",
                    "Website": ", ".join(website) if website else "N/A",
                    "Profile URL": profile
                }

                all_data.append(data)

                print("\nSAVED DATA")
                print(data)

                # SAVE LIVE TO EXCEL
                df = pd.DataFrame(all_data)

                df.to_excel(
                    "linkedin_valid_data.xlsx",
                    index=False
                )

                # SMALL DELAY
                time.sleep(5)

            except Exception as e:

                print(f"ERROR: {e}")

                continue

    print("\nALL DATA SAVED")

    browser.close()