from core.scraper import scrape_docs
from core.chunker import chunk_text
from core.indexer import build_index
from core.parser import parse_endpoints
from core.intent import filter_by_intent
from core.codegen import generate_wrapper


def run_pipeline(
    url: str,
    use_case: str,
    language: str,
    api_name: str = "API",
    max_pages: int = 15
) -> dict:
    """
    Main pipeline — runs all agents in sequence.
    """
    print("\n========== INTEGRAMIND PIPELINE START ==========")

    # Step 1: Scrape
    print("\n[pipeline] Step 1: Scraping documentation...")
    scraped = scrape_docs(url, max_pages=max_pages)

    if not scraped["content"]:
        raise ValueError("Could not extract content from the provided URL.")

    # Step 2: Chunk
    print("\n[pipeline] Step 2: Chunking text...")
    chunks = chunk_text(scraped["content"], chunk_size=300, overlap=30)

    # Step 3: Index
    print("\n[pipeline] Step 3: Building hybrid index...")
    index_data = build_index(chunks)

    # Step 4: Parse
    print("\n[pipeline] Step 4: Extracting endpoints and auth...")
    parsed = parse_endpoints(scraped, index_data)

    # Step 5: Intent
    print("\n[pipeline] Step 5: Filtering by use case...")
    intent = filter_by_intent(use_case, parsed, index_data)

    # Step 6: Code generation
    print("\n[pipeline] Step 6: Generating wrapper class...")
    code = generate_wrapper(parsed, intent, language, api_name)

    print("\n========== INTEGRAMIND PIPELINE COMPLETE ==========")

    return {
        "scraped": scraped,
        "index_data": index_data,
        "parsed": parsed,
        "intent": intent,
        "code": code,
        "api_name": api_name,
        "language": language
    }