from bs4 import BeautifulSoup
from readability import Document
from playwright.sync_api import sync_playwright

from src.brand import extract_branding


def fetch_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1440, "height": 1600},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
        )

        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        try:
            page.wait_for_timeout(2500)
        except Exception:
            pass

        html = page.content()
        browser.close()
        return html


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def get_meta(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return clean_text(tag["content"])
    return ""


def extract_author(soup: BeautifulSoup) -> str:
    candidates = [
        get_meta(soup, "author"),
        get_meta(soup, "article:author"),
    ]

    for selector in [
        '[class*="author"]',
        'a[href*="/people/"]',
        'a[href*="/profile/"]',
    ]:
        found = soup.select_one(selector)
        if found:
            candidates.append(found.get_text(" ", strip=True))

    for c in candidates:
        if c and len(c) < 120:
            return c

    return "Unknown Author"


def extract_date(soup: BeautifulSoup) -> str:
    candidates = [
        get_meta(soup, "article:published_time"),
        get_meta(soup, "date"),
        get_meta(soup, "pubdate"),
    ]

    time_tag = soup.find("time")
    if time_tag:
        candidates.append(time_tag.get("datetime") or time_tag.get_text(" ", strip=True))

    for c in candidates:
        if c:
            return c[:10]

    return ""


def extract_publication(soup: BeautifulSoup) -> str:
    site = get_meta(soup, "og:site_name")
    if site:
        return site

    title = soup.find("title")
    if title:
        text = title.get_text(" ", strip=True)
        if "|" in text:
            return text.split("|")[-1].strip()
        if " - " in text:
            return text.split(" - ")[-1].strip()

    return "Substack"


def extract_title(soup: BeautifulSoup, doc: Document) -> str:
    title = get_meta(soup, "og:title", "twitter:title")
    if title:
        return title

    h1 = soup.find("h1")
    if h1:
        return h1.get_text(" ", strip=True)

    return clean_text(doc.short_title())


def absolutize_images(soup: BeautifulSoup, base_url: str):
    from urllib.parse import urljoin

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            img["src"] = urljoin(base_url, src)


def extract_body(html: str, url: str) -> str:
    doc = Document(html)
    summary = doc.summary(html_partial=True)
    body_soup = BeautifulSoup(summary, "lxml")

    for bad in body_soup.select("script, style, iframe, form, button, nav, aside"):
        bad.decompose()

    absolutize_images(body_soup, url)

    return str(body_soup)


def scrape_article(url: str) -> dict:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    doc = Document(html)

    branding = extract_branding(soup, url)

    return {
        "url": url,
        "title": extract_title(soup, doc),
        "author": extract_author(soup),
        "date": extract_date(soup),
        "publication": extract_publication(soup),
        "body_html": extract_body(html, url),
        "logo_url": branding.get("logo_url", ""),
        "primary_color": branding.get("primary_color", "#7A1F1F"),
    }
