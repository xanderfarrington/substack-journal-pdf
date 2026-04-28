import argparse
import os
from pathlib import Path

import feedparser
from slugify import slugify

from src.scraper import scrape_article
from src.formatter import render_article_html
from src.pdf import html_to_pdf


def read_input_file(path: str) -> list[str]:
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            clean = line.strip()
            if clean and not clean.startswith("#"):
                urls.append(clean)
    return urls


def is_feed(url: str) -> bool:
    return url.endswith("/feed") or "substack.com/feed" in url or url.endswith(".xml")


def expand_feed(feed_url: str) -> list[str]:
    parsed = feedparser.parse(feed_url)
    links = []
    for entry in parsed.entries:
        if hasattr(entry, "link"):
            links.append(entry.link)
    return links


def build_one(url: str, output_dir: str):
    article = scrape_article(url)
    html = render_article_html(article)

    publication = slugify(article.get("publication") or "substack")
    title = slugify(article.get("title") or "article")
    filename = f"{publication}_{title}.pdf"

    output_path = Path(output_dir) / filename
    html_debug_path = Path(output_dir) / filename.replace(".pdf", ".html")

    os.makedirs(output_dir, exist_ok=True)

    with open(html_debug_path, "w", encoding="utf-8") as f:
        f.write(html)

    html_to_pdf(html, str(output_path))

    print(f"Generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Substack to journal-style PDF generator")
    parser.add_argument("--url", help="Single Substack article URL or RSS feed URL")
    parser.add_argument("--input", help="Text file containing URLs")
    parser.add_argument("--output", default="output", help="Output directory")

    args = parser.parse_args()

    raw_urls = []

    if args.url:
        raw_urls.append(args.url)

    if args.input:
        raw_urls.extend(read_input_file(args.input))

    if not raw_urls:
        raise ValueError("Provide --url or --input")

    article_urls = []

    for url in raw_urls:
        if is_feed(url):
            article_urls.extend(expand_feed(url))
        else:
            article_urls.append(url)

    seen = set()
    unique_urls = []

    for url in article_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    for url in unique_urls:
        try:
            build_one(url, args.output)
        except Exception as e:
            print(f"Failed: {url}")
            print(f"Reason: {e}")


if __name__ == "__main__":
    main()
