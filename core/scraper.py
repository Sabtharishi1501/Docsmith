import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time


def get_base_domain(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_same_domain(url: str, base_domain: str) -> bool:
    return urlparse(url).netloc == urlparse(base_domain).netloc


def scrape_page(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            return text or ""
    except Exception as e:
        print(f"[scraper] Failed to extract {url}: {e}")
    return ""


def get_links(url: str, base_domain: str) -> list:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])
            if (
                is_same_domain(full_url, base_domain)
                and full_url.startswith("http")
                and "#" not in full_url
                and full_url != url
            ):
                links.append(full_url)
        return list(set(links))
    except Exception as e:
        print(f"[scraper] Failed to get links from {url}: {e}")
        return []


def scrape_docs(start_url: str, max_pages: int = 20, delay: float = 0.5) -> dict:
    base_domain = get_base_domain(start_url)
    visited = set()
    to_visit = [start_url]
    pages = []

    print(f"[scraper] Starting crawl: {start_url}")

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        print(f"[scraper] Scraping ({len(visited)+1}/{max_pages}): {url}")
        text = scrape_page(url)
        visited.add(url)

        if text:
            pages.append({"url": url, "text": text})
            new_links = get_links(url, base_domain)
            for link in new_links:
                if link not in visited and link not in to_visit:
                    to_visit.append(link)

        time.sleep(delay)

    combined_text = "\n\n".join(
        f"[SOURCE: {p['url']}]\n{p['text']}" for p in pages
    )

    print(f"[scraper] Done. Pages scraped: {len(pages)}")

    return {
        "url": start_url,
        "pages_scraped": len(pages),
        "content": combined_text,
        "pages": pages
    }