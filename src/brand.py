import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}")


def find_logo(soup: BeautifulSoup, base_url: str) -> str:
    selectors = [
        'meta[property="og:image"]',
        'meta[name="twitter:image"]',
        'link[rel="icon"]',
        'link[rel="shortcut icon"]',
        'img[alt*="logo" i]',
        'img[src*="logo" i]',
    ]

    for selector in selectors:
        tag = soup.select_one(selector)
        if not tag:
            continue

        value = tag.get("content") or tag.get("href") or tag.get("src")
        if value:
            return urljoin(base_url, value)

    return ""


def find_primary_color(soup: BeautifulSoup) -> str:
    meta_theme = soup.find("meta", attrs={"name": "theme-color"})
    if meta_theme and meta_theme.get("content"):
        return meta_theme["content"]

    style_text = ""

    for style in soup.find_all("style"):
        style_text += style.get_text(" ", strip=True) + " "

    matches = HEX_RE.findall(style_text)

    blacklist = {
        "#fff",
        "#ffffff",
        "#000",
        "#000000",
        "#111",
        "#222",
        "#333",
        "#666",
        "#999",
    }

    for color in matches:
        if color.lower() not in blacklist:
            return color

    return "#7A1F1F"


def extract_branding(soup: BeautifulSoup, base_url: str) -> dict:
    return {
        "logo_url": find_logo(soup, base_url),
        "primary_color": find_primary_color(soup),
    }
