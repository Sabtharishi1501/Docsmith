import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_base_domain(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_same_domain(url: str, base_domain: str) -> bool:
    return urlparse(url).netloc == urlparse(base_domain).netloc


def is_api_relevant(url: str) -> bool:
    """
    Prioritize URLs that are likely to contain API endpoint info.
    Deprioritize changelog, blog, pricing, login pages.
    """
    url_lower = url.lower()

    # Always skip these — never useful for endpoint extraction
    skip_patterns = [
        "/changelog", "/blog", "/pricing", "/login", "/signup",
        "/register", "/careers", "/about", "/contact", "/press",
        "/legal", "/privacy", "/terms", "/cookies", "/sitemap",
        "/404", "/error", "/search", "javascript:", "mailto:",
        "/videos", "/webinar", "/podcast", "/news", "/events",
        "/downloads", "/support/community", "/forum",
        "/no-code", "/payments/no-code", "/declines",
        "/error-codes", "/versioning", "/keys"
    ]
    for pattern in skip_patterns:
        if pattern in url_lower:
            return False

    # High priority — these pages have actual endpoint definitions
    priority_patterns = [
        "/api/charges", "/api/payment_intents", "/api/customers",
        "/api/refunds", "/api/subscriptions", "/api/invoices",
        "/api/products", "/api/prices", "/api/events",
        "/api/webhooks", "/api/balance", "/api/payouts",
        "/api/transfers", "/api/disputes", "/api/authentication",
        "/reference", "/endpoints", "/rest",
        "/authentication", "/quickstart", "/getting-started",
    ]
    for pattern in priority_patterns:
        if pattern in url_lower:
            return True

    # Allow /api/ paths generally
    if "/api/" in url_lower:
        return True

    return False


def scrape_page(url: str) -> str:
    """Scrape a single page and return clean text."""
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
    """Get all same-domain links from a page."""
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; Docsmith/1.0)"
            }
        )
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])
            parsed = urlparse(full_url)
            # Clean URL — remove fragments and query strings
            clean_url = (
                f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            )
            if (
                is_same_domain(clean_url, base_domain)
                and clean_url.startswith("http")
                and clean_url != url
            ):
                links.append(clean_url)
        return list(set(links))
    except Exception as e:
        print(f"[scraper] Failed to get links from {url}: {e}")
        return []


def scrape_single(args: tuple) -> tuple:
    """Worker function for parallel scraping."""
    url, idx, total = args
    text = scrape_page(url)
    print(f"[scraper] Done ({idx}/{total}): {url}")
    return url, text


def scrape_docs(
    start_url: str,
    max_pages: int = 15,
    delay: float = 0.0
) -> dict:
    """
    Main scraper — crawls API docs starting from start_url.
    Prioritizes API-relevant pages using parallel scraping.

    Args:
        start_url: The API documentation URL
        max_pages: Maximum pages to crawl
        delay: Delay between requests (unused in parallel mode)

    Returns:
        {
            "url": str,
            "pages_scraped": int,
            "content": str,
            "pages": list
        }
    """
    base_domain = get_base_domain(start_url)
    visited = set()
    pages = []

    print(f"[scraper] Starting parallel crawl: {start_url}")
    print(f"[scraper] Max pages: {max_pages}")

    # Scrape the start URL first
    start_text = scrape_page(start_url)
    visited.add(start_url)
    if start_text:
        pages.append({"url": start_url, "text": start_text})

    # Get all links from the start page
    all_links = get_links(start_url, base_domain)

    # Sort — API-relevant links first, others after
    priority_links = [l for l in all_links if is_api_relevant(l)]
    other_links = [l for l in all_links if not is_api_relevant(l)]
    sorted_links = priority_links + other_links

    # Select up to max_pages - 1 unvisited links
    to_scrape = []
    for link in sorted_links:
        if link not in visited and len(to_scrape) < (max_pages - 1):
            to_scrape.append(link)
            visited.add(link)

    print(f"[scraper] Scraping {len(to_scrape)} pages in parallel...")

    # Build args list for parallel workers
    args_list = [
        (url, idx + 1, len(to_scrape))
        for idx, url in enumerate(to_scrape)
    ]

    # Parallel scrape with thread pool
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(scrape_single, args): args
            for args in args_list
        }
        for future in as_completed(futures):
            try:
                url, text = future.result()
                if text:
                    pages.append({"url": url, "text": text})
            except Exception as e:
                print(f"[scraper] Thread error: {e}")

    # Combine all page texts with source labels
    combined_text = "\n\n".join(
        f"[SOURCE: {p['url']}]\n{p['text']}"
        for p in pages
    )

    print(f"[scraper] Done. Pages scraped: {len(pages)}")

    return {
        "url": start_url,
        "pages_scraped": len(pages),
        "content": combined_text,
        "pages": pages
    }