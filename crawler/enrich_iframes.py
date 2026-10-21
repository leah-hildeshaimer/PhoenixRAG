
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "results_full.jsonl"
OUTPUT_FILE = BASE_DIR / "iframe_enriched.json"

MAX_TEXT_LENGTH = 100
REQUEST_DELAY = 1.5

HEADERS = {
    "User-Agent": "PhoenixRAG-HackathonBot/1.0"
}

session = requests.Session()
session.headers.update(HEADERS)


def get_html(url):
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if "html" not in content_type:
            return None

        return BeautifulSoup(
            response.content,
            "html.parser"
        )

    except requests.RequestException as error:
        print(f"Request failed: {url}")
        print(f"  {error}")
        return None


def is_phoenix_url(url):
    hostname = urlparse(url).hostname or ""

    return (
        hostname == "fnx.co.il"
        or hostname.endswith(".fnx.co.il")
    )


def get_page_text(page):
    return " ".join(
        element.get("text", "")
        for element in page.get("content", [])
    ).strip()


def extract_documents(soup, base_url):
    documents = []
    seen_urls = set()

    for link in soup.select("a[href]"):
        href = link.get("href", "").strip()

        if not href:
            continue

        document_url = urljoin(base_url, href)

        parsed = urlparse(document_url)

        if not parsed.path.lower().endswith(".pdf"):
            continue

        if not is_phoenix_url(document_url):
            continue

        if document_url in seen_urls:
            continue

        seen_urls.add(document_url)

        title = link.get_text(" ", strip=True)

        documents.append({
            "title": title or "PDF document",
            "url": document_url
        })

    return documents

def is_blocked_page(soup):
    text = soup.get_text(" ", strip=True).lower()

    blocked_signatures = [
        "radware page",
        "verifying your browser",
        "incident id:",
        "access denied",
        "captcha"
    ]

    return any(
        signature in text
        for signature in blocked_signatures
    )


def extract_iframe_content(soup):
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return " ".join(
        soup.get_text(" ", strip=True).split()
    )


def enrich_page(page):
    page_url = page["url"]

    print(f"\nChecking: {page_url}")

    soup = get_html(page_url)

    if soup is None:
        return None

    enriched_iframes = []

    for iframe in soup.select("iframe[src]"):
        src = iframe.get("src", "").strip()

        if not src:
            continue

        iframe_url = urljoin(page_url, src)

        if not is_phoenix_url(iframe_url):
            continue

        time.sleep(REQUEST_DELAY)

        iframe_soup = get_html(iframe_url)

        if iframe_soup is None:
            continue

        
        if is_blocked_page(iframe_soup):
         print(f"  Blocked by site protection: {iframe_url}")
         continue


        iframe_text = extract_iframe_content(
            iframe_soup
        )

        documents = extract_documents(
            iframe_soup,
            iframe_url
        )

        if not iframe_text and not documents:
            continue

        enriched_iframes.append({
            "iframe_url": iframe_url,
            "text": iframe_text,
            "documents": documents
        })

    if not enriched_iframes:
        return None

    return {
        "url": page_url,
        "title": page.get("title", ""),
        "iframes": enriched_iframes
    }


def main():
    pages_by_url = {}

    with INPUT_FILE.open(
        "r", encoding="utf-8"
    ) as file:
        for line in file:
            if not line.strip():
                continue

            page = json.loads(line)
            url = page.get("url", "")

            if url:
                pages_by_url[url] = page

    short_pages = [
        page
        for page in pages_by_url.values()
        if len(get_page_text(page)) < MAX_TEXT_LENGTH
    ]

    print(f"Short pages to inspect: {len(short_pages)}")

    results = []

    for index, page in enumerate(
        short_pages, start=1
    ):
        print(f"[{index}/{len(short_pages)}]")

        result = enrich_page(page)

        if result:
            results.append(result)

            print(
                f"  Found {len(result['iframes'])} "
                "relevant iframe(s)"
            )

        time.sleep(REQUEST_DELAY)

    with OUTPUT_FILE.open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\n=== ENRICHMENT COMPLETE ===")
    print(f"Pages checked: {len(short_pages)}")
    print(f"Pages enriched: {len(results)}")
    print(f"Saved to: {OUTPUT_FILE.name}")


if __name__ == "__main__":
    main()
