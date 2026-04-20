from contextlib import contextmanager
import time
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin
from playwright.sync_api import sync_playwright
try:
    from Config import LINKEDIN_USER_DATA_DIR
except ImportError:
    LINKEDIN_USER_DATA_DIR = ""

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


@contextmanager
def playwright_page(p, headless: bool = True):
    """Utility to launch a browser page using either persistent context or a new browser."""
    obj = None  # This will store either a BrowserContext or a Browser
    try:
        if LINKEDIN_USER_DATA_DIR:
            obj = p.chromium.launch_persistent_context(
                LINKEDIN_USER_DATA_DIR,
                headless=headless,
                viewport={"width": 1280, "height": 800}
            )
            page = obj.pages[0] if obj.pages else obj.new_page()
        else:
            obj = p.chromium.launch(headless=headless)
            # Pass default headers to the browser context
            context = obj.new_context(user_agent=DEFAULT_HEADERS["User-Agent"])
            page = context.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})
        yield page
    finally:
        if obj:
            obj.close()


def fetch_jobs(keyword="data analyst", location="India", max_jobs=50):
    keyword_q = quote(keyword)
    location_q = quote(location)
    url = (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={keyword_q}&location={location_q}"
    )

    jobs = []
    
    with sync_playwright() as p:
        with playwright_page(p) as page:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                # Wait for any of the common job card selectors
                page.wait_for_selector(".base-card, .job-card-container, .jobs-search-results__list-item", timeout=15000)
                content = page.content()
            except Exception as e:
                print(f"Playwright could not fetch jobs: {e}")
                return pd.DataFrame(columns=["title", "company", "link"])

    soup = BeautifulSoup(content, "html.parser")

    # Try multiple card selectors (LinkedIn changes DOM often)
    card_selectors = [
        "div.base-card",
        "div.job-card-container",
        "li.jobs-search-results__list-item",
        "div.scaffold-layout__list-container li",
    ]

    cards = []
    for sel in card_selectors:
        cards = soup.select(sel)
        if cards:
            break

    if not cards:
        print("No job cards found (DOM changed or content is JS-rendered).")
        return pd.DataFrame(columns=["title", "company", "link"])

    for card in cards[:max_jobs]:
        # Title
        title_el = (
            card.select_one("h3")
            or card.select_one("a[aria-label]")
            or card.select_one("span.job-title")
        )
        title = title_el.get_text(strip=True) if title_el else ""

        # Company
        company_el = (
            card.select_one("h4")
            or card.select_one(".base-search-card__subtitle")
            or card.select_one(".job-details-jobs-unified-top-card__subtitle")
        )
        company = company_el.get_text(strip=True) if company_el else ""

        # Link
        link_el = card.find("a", href=True)
        href = link_el["href"] if link_el else ""
        full_link = urljoin("https://www.linkedin.com", href) if href else ""

        jobs.append({"title": title, "company": company, "link": full_link})

    return pd.DataFrame(jobs)


def fetch_job_description(url: str, timeout: int = 25, page=None) -> str:
    """Best-effort plain text from a public LinkedIn job URL. Often empty if login/captcha required."""
    if not url or not str(url).strip():
        return ""

    clean = str(url).split("?")[0].strip()
    content = ""

    if page:
        try:
            page.goto(clean, wait_until="domcontentloaded", timeout=timeout*1000)
            content = page.content()
        except:
            return ""
    else:
        with sync_playwright() as p:
            with playwright_page(p) as temp_page:
                try:
                    temp_page.goto(clean, wait_until="domcontentloaded", timeout=timeout*1000)
                    content = temp_page.content()
                except:
                    return ""

    soup = BeautifulSoup(content, "html.parser")
    candidates = []
    for sel in (
        "div.show-more-less-html__full-size",
        "div.description__text",
        "article.jobs-description__container",
        "div.jobs-description-content",
        "div.jobs-box__html-content",
        "div[class*='job-details']",
    ):
        for el in soup.select(sel):
            t = el.get_text("\n", strip=True)
            if len(t) > 80:
                candidates.append(t)

    if candidates:
        return max(candidates, key=len)[:20000]

    meta = soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        return str(meta["content"]).strip()[:20000]

    return ""


def enrich_jobs_with_descriptions(
    df: pd.DataFrame,
    limit: int,
    delay_sec: float = 1.5,
) -> pd.DataFrame:
    """Add a ``description`` column by fetching each job page (first ``limit`` rows)."""
    if df is None or df.empty:
        return df

    out = df.copy()
    if "description" not in out.columns:
        out["description"] = ""

    n = min(int(limit), len(out))

    with sync_playwright() as p:
        with playwright_page(p) as page:
            for i in range(n):
                link = str(out.iloc[i].get("link") or "")
                out.at[out.index[i], "description"] = fetch_job_description(link, page=page)
                if i < n - 1 and delay_sec > 0:
                    time.sleep(delay_sec)

    return out