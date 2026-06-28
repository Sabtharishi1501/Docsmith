import re
import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque


def get_base_domain(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_same_domain(url: str, base_domain: str) -> bool:
    return urlparse(url).netloc == urlparse(base_domain).netloc


def clean_url(url: str) -> str:
    """Strip fragments and query strings."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


SKIP_PATTERNS = [
    "/changelog", "/blog", "/pricing", "/login", "/signup",
    "/register", "/careers", "/about", "/contact", "/press",
    "/legal", "/privacy", "/terms", "/cookies", "/sitemap",
    "/404", "/error", "/news", "/events", "/downloads",
    "/support/community", "/forum", "/webinar", "/podcast",
    "javascript:", "mailto:", "#",
]

PRIORITY_PATTERNS = [
    "/api/", "/reference", "/endpoints", "/rest", "/v1/", "/v2/", "/v3/",
    "/authentication", "/quickstart", "/getting-started", "/guides",
    "/resources", "/methods", "/objects", "/requests", "/responses",
    "/errors", "/pagination", "/webhooks", "/sdk",
]


def url_priority(url: str) -> int:
    """Lower number = higher priority in the crawl queue."""
    url_lower = url.lower()
    for p in SKIP_PATTERNS:
        if p in url_lower:
            return 999
    for p in PRIORITY_PATTERNS:
        if p in url_lower:
            return 0
    return 1


def should_skip(url: str) -> bool:
    url_lower = url.lower()
    return any(p in url_lower for p in SKIP_PATTERNS)


HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Docsmith/1.0)"}


def fetch_html(url: str, timeout: int = 10) -> str | None:
    try:
        r = requests.get(url, timeout=timeout, headers=HEADERS)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[scraper] fetch_html failed {url}: {e}")
        return None


def scrape_page(url: str) -> tuple[str, str | None]:
    """
    Extract clean text from a URL.
    Returns (text, raw_html) — html is kept so we can extract endpoints
    from it without fetching the page a second time.
    Falls back to BeautifulSoup if trafilatura returns nothing.
    """
    html = fetch_html(url)
    if not html:
        return "", None

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_links=True,
        no_fallback=False,
        favor_recall=True,
    ) or ""

    if len(text) < 200:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

    return text, html


def get_links(url: str, base_domain: str, html: str | None = None) -> list[str]:
    """Return all same-domain links found on the page."""
    if html is None:
        html = fetch_html(url) or ""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all("a", href=True):
        full = urljoin(url, tag["href"])
        c = clean_url(full)
        if (
            is_same_domain(c, base_domain)
            and c.startswith("http")
            and c != url
            and not should_skip(c)
        ):
            links.append(c)
    return list(set(links))



def scrape_single(args: tuple) -> tuple:
    """Returns (url, text, html) so the crawl loop can reuse the html."""
    url, idx, total = args
    text, html = scrape_page(url)
    print(f"[scraper] ({idx}/{total}) {url}  [{len(text)} chars]")
    return url, text, html


# ── Endpoint extractors ────────────────────────────────────────────────────────

HTTP_METHODS = r"(?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)"

ENDPOINT_PATTERNS = [
    re.compile(rf"\b({HTTP_METHODS})\s+(/[\w/{{}}:.-]+)", re.IGNORECASE),
    re.compile(rf"({HTTP_METHODS})\s*\n\s*(/[\w/{{}}:.-]+)", re.IGNORECASE | re.MULTILINE),
    re.compile(r"[`'\"](/(?:v\d+/|api/)[\w/{}:.-]+)[`'\"]"),
    re.compile(r"\b(/(?:v\d+|api)/[\w/{}:.-]{4,})\b"),
]


_REAL_ID_RE = re.compile(
    r"(?<=/)"                                       
    r"("
    r"[a-z]{1,12}_(?:test_)?[A-Za-z0-9]{8,}"         
    r"|[0-9]{6,}"                                      
    r")"
    r"(?=/|$)"                                          
)


def normalize_path(path: str) -> str:
    """
    Replace real Stripe ID segments with {id} placeholder.
    Strips trailing slash. Collapses consecutive {id}/{id} into {id}.
    """
    path = path.rstrip("/")                             
    path = _REAL_ID_RE.sub("{id}", path)                
    path = re.sub(r"\{id\}/\{id\}", "{id}", path)
    return path


def extract_endpoints_from_html(html: str, source_url: str) -> list[dict]:
    """
    Pull method+path pairs directly from raw HTML before stripping.
    Handles Stripe-style badge markup where method and path are siblings.
    """
    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    results = []


    for tag in soup.find_all(string=re.compile(
        r"^\s*(GET|POST|PUT|PATCH|DELETE)\s*$", re.IGNORECASE
    )):
        method = tag.strip().upper()
        node = tag.parent
        for _ in range(5):                      
            if node is None:
                break
            nearby_text = node.get_text(" ", strip=True)
            path_match = re.search(r"(/(?:v\d+|api)/[A-Za-z0-9_./{}:-]+)", nearby_text)
            if path_match:
                path = normalize_path(path_match.group(1))
                key = (method, path)
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "method": method,
                        "path": path,
                        "source": source_url,
                    })
                break
            node = node.parent

    full_text = soup.get_text(separator="\n")
    for pattern in ENDPOINT_PATTERNS:
        for match in pattern.finditer(full_text):
            groups = match.groups()
            if len(groups) == 2:
                method = groups[0].upper()
                path = normalize_path(groups[1])
            else:
                method = "?"
                path = normalize_path(groups[0])
            key = (method, path)
            if key not in seen:
                seen.add(key)
                results.append({
                    "method": method,
                    "path": path,
                    "source": source_url,
                })

    return results


def extract_endpoints(pages: list[dict]) -> list[dict]:
    """
    Walk all scraped pages (text only) and pull out HTTP endpoint definitions.
    Used as a final pass over combined text after all pages are scraped.
    Returns a deduplicated list of {method, path, source}.
    """
    seen = set()
    results = []

    for page in pages:
        text = page["text"]
        url = page["url"]

        for pattern in ENDPOINT_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) == 2:
                    method = groups[0].upper()
                    path = groups[1]
                else:
                    method = "?"
                    path = groups[0]

                path = normalize_path(path)
                key = f"{method}:{path}"
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "method": method,
                        "path": path,
                        "source": url,
                    })

    method_order = {"GET": 0, "POST": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}
    results.sort(key=lambda e: (method_order.get(e["method"], 9), e["path"]))

    seen_clean: set[str] = set()
    deduped = []
    for ep in results:
        key = f"{ep['method']}:{ep['path'].rstrip('/')}"
        if key not in seen_clean:
            seen_clean.add(key)
            deduped.append(ep)
    return deduped



def answer_query(query: str, pages: list[dict], endpoints: list[dict]) -> str:
    """
    Simple keyword search across all scraped pages to answer a user query.
    Returns the most relevant snippets.
    """
    query_lower = query.lower()
    keywords = [w for w in re.split(r"\W+", query_lower) if len(w) > 2]

    scored = []
    for page in pages:
        text = page["text"]
        score = sum(text.lower().count(kw) for kw in keywords)
        if score > 0:
            scored.append((score, page))

    scored.sort(key=lambda x: -x[0])
    top_pages = scored[:3]

    if not top_pages:
        return "No relevant content found for your query."

    snippets = []
    for _, page in top_pages:
        text = page["text"]
        pos = -1
        for kw in keywords:
            pos = text.lower().find(kw)
            if pos != -1:
                break
        if pos == -1:
            pos = 0
        start = max(0, pos - 200)
        end = min(len(text), pos + 600)
        snippets.append(
            f"[From {page['url']}]\n{text[start:end].strip()}"
        )

    return "\n\n---\n\n".join(snippets)


def scrape_docs(
    start_url: str,
    max_pages: int = 40,
    max_workers: int = 8,
    user_query: str | None = None,
) -> dict:
    """
    Crawl API documentation recursively from start_url.

    Returns:
        {
            "url": str,
            "pages_scraped": int,
            "content": str,
            "pages": list[dict],
            "endpoints": list[dict],
            "answer": str | None,
        }
    """
    base_domain = get_base_domain(start_url)
    visited: set[str] = set()
    pages: list[dict] = []
    all_html_endpoints: list[dict] = []  

    queue: deque[str] = deque()
    queue.append(start_url)
    visited.add(start_url)

    print(f"[scraper] Starting recursive crawl: {start_url}")
    print(f"[scraper] Max pages: {max_pages}")

    while queue and len(visited) <= max_pages:
        batch: list[str] = []
        while queue and len(batch) < max_workers:
            batch.append(queue.popleft())

        if not batch:
            break

        args_list = [(u, len(visited) - len(queue), max_pages) for u in batch]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(scrape_single, a): a for a in args_list}
            for future in as_completed(futures):
                try:
                    url, text, html = future.result()  

                    if text:
                        pages.append({"url": url, "text": text})

                    if html:
                        html_eps = extract_endpoints_from_html(html, url)
                        all_html_endpoints.extend(html_eps)

                        if len(visited) < max_pages:
                            new_links = get_links(url, base_domain, html)
                            new_links.sort(key=url_priority)
                            for link in new_links:
                                if link not in visited and len(visited) < max_pages:
                                    visited.add(link)
                                    queue.append(link)

                except Exception as e:
                    print(f"[scraper] Thread error: {e}")

    text_endpoints = extract_endpoints(pages)

    seen_keys: set[str] = set()
    endpoints: list[dict] = []
    for ep in all_html_endpoints + text_endpoints:
        key = f"{ep['method']}:{ep['path']}"
        if key not in seen_keys:
            seen_keys.add(key)
            endpoints.append(ep)

    method_order = {"GET": 0, "POST": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}
    endpoints.sort(key=lambda e: (method_order.get(e["method"], 9), e["path"]))

    known_method_keys: set[str] = {
        f"{ep['method']}:{ep['path']}"
        for ep in endpoints if ep["method"] != "?"
    }
    final: list[dict] = []
    seen_final: set[str] = set()
    for ep in endpoints:
        clean_key = f"{ep['method']}:{ep['path'].rstrip('/')}"
        if clean_key in seen_final:
            continue
        # Drop ?-method entries when a known-method version already exists
        if ep["method"] == "?":
            for m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                if f"{m}:{ep['path']}" in known_method_keys:
                    break
            else:
                seen_final.add(clean_key)
                final.append(ep)
        else:
            seen_final.add(clean_key)
            final.append(ep)
    endpoints = final

    combined_text = "\n\n".join(
        f"[SOURCE: {p['url']}]\n{p['text']}" for p in pages
    )

    answer = None
    if user_query:
        answer = answer_query(user_query, pages, endpoints)

    print(f"[scraper] Done. Pages: {len(pages)}  Endpoints found: {len(endpoints)}")

    return {
        "url": start_url,
        "pages_scraped": len(pages),
        "content": combined_text,
        "pages": pages,
        "endpoints": endpoints,
        "answer": answer,
    }



if __name__ == "__main__":
    import json
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "https://stripe.com/docs/api"
    query = sys.argv[2] if len(sys.argv) > 2 else None

    result = scrape_docs(url, max_pages=40, user_query=query)

    print(f"\n{'='*60}")
    print(f"Pages scraped : {result['pages_scraped']}")
    print(f"Endpoints     : {len(result['endpoints'])}")
    print(f"{'='*60}\n")

    print("ENDPOINTS:")
    for ep in result["endpoints"]:
        print(f"  {ep['method']:<8} {ep['path']}")

    if query and result["answer"]:
        print(f"\nANSWER TO: {query!r}")
        print(result["answer"])

    with open("scrape_result.json", "w") as f:
        json.dump(
            {k: v for k, v in result.items() if k != "content"},
            f, indent=2
        )
    print("\n[scraper] Full result saved to scrape_result.json")