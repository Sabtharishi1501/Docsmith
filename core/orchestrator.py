import os

from core.scraper import scrape_docs
from core.chunker import chunk_text
from core.indexer import build_index
from core.parser import parse_endpoints
from core.intent import filter_by_intent
from core.codegen import generate_wrapper
from core.testgen import generate_tests
from core.postman import generate_postman_collection, collection_to_json
from core.formatter import format_code
from core.validator import validate
from core.fixer import fix_code

MAX_RETRIES = 3


def run_pipeline(
    url: str,
    use_case: str,
    language: str,
    api_name: str = "API",
    max_pages: int = 40,          # raised — more pages = better endpoint coverage
) -> dict:

    print("\n========== DOCSMITH PIPELINE START ==========")

    # Step 1: Scrape
    print("\n[pipeline] Step 1: Scraping documentation...")
    scraped = scrape_docs(url, max_pages=max_pages, user_query=use_case)
    if not scraped["content"]:
        raise ValueError("Could not extract content from the provided URL.")

    print(f"[pipeline] Pages scraped: {scraped['pages_scraped']}")
    print(f"[pipeline] Endpoints pre-extracted by scraper: {len(scraped['endpoints'])}")

    # Step 2: Chunk — use per-page chunks for better retrieval accuracy
    print("\n[pipeline] Step 2: Chunking text...")
    # Chunk each page separately so source URLs are preserved in metadata
    all_chunks = []
    for page in scraped["pages"]:
        page_chunks = chunk_text(page["text"], chunk_size=500, overlap=50)
        for chunk in page_chunks:
            chunk["source"] = page["url"]   # attach URL to every chunk
        all_chunks.extend(page_chunks)
    chunks = all_chunks

    # Step 3: Index
    print("\n[pipeline] Step 3: Building hybrid index...")
    index_data = build_index(chunks)

    # Step 4: Parse — seed with scraper-extracted endpoints to avoid re-extraction
    print("\n[pipeline] Step 4: Extracting endpoints and auth...")
    parsed = parse_endpoints(
        scraped,
        index_data,
        seed_endpoints=scraped["endpoints"],   # <-- NEW: pass pre-extracted endpoints
    )

    if not isinstance(parsed, dict):
        parsed = {
            "base_url": "",
            "auth_method": "Unknown",
            "auth_header": "",
            "sdk_available": False,
            "sdk_name": None,
            "sdk_install": None,
            "endpoints": []
        }

    # Merge: if parser returned fewer endpoints than the scraper found, keep both
    parser_paths = {ep.get("path") for ep in parsed.get("endpoints", [])}
    for raw_ep in scraped["endpoints"]:
        if raw_ep["path"] not in parser_paths:
            parsed["endpoints"].append({
                "method": raw_ep["method"],
                "path": raw_ep["path"],
                "description": "",
                "parameters": [],
                "returns": ""
            })

    print(f"[pipeline] Total endpoints after merge: {len(parsed['endpoints'])}")

    # Step 5: Intent
    print("\n[pipeline] Step 5: Filtering by use case...")
    intent = filter_by_intent(use_case, parsed, index_data)

    if not isinstance(intent, dict):
        intent = {
            "relevant_endpoints": parsed.get("endpoints", []),
            "integration_path": "REST",
            "sdk_recommended": False,
            "explanation": ""
        }

    # Step 6: Generate wrapper + validate loop
    print("\n[pipeline] Step 6: Generating wrapper class...")
    code = generate_wrapper(parsed, intent, language, api_name)

    if not isinstance(code, str):
        code = str(code)

    os.makedirs("generated", exist_ok=True)
    wrapper_path = "generated/wrapper.py"

    with open(wrapper_path, "w", encoding="utf-8") as f:
        f.write(code)

    for attempt in range(MAX_RETRIES):
        print(f"\n========== ITERATION {attempt + 1}/{MAX_RETRIES} ==========")

        print("[pipeline] Formatting wrapper...")
        success, message = format_code(wrapper_path, language)
        print("[formatter]", message)

        with open(wrapper_path, "r", encoding="utf-8") as f:
            code = f.read()

        print("[pipeline] Validating wrapper...")
        valid, report = validate(wrapper_path)

        if valid:
            print("[validator] Validation passed.")
            break

        print("[validator] Validation failed.")
        for check, output in report.items():
            print(f"{check.upper()}\n{output}\n{'-'*60}")

        errors = "\n\n".join(f"{k}\n{v}" for k, v in report.items())
        code = fix_code(
            code=code,
            errors=errors,
            language=language,
            api_name=api_name,
        )

        if not isinstance(code, str):
            code = str(code)

        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write(code)
    else:
        print("[pipeline] Max retries reached — using last valid code.")

    with open(wrapper_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Step 7: Tests
    print("\n[pipeline] Step 7: Generating unit tests...")
    tests = generate_tests(wrapper_code=code, language=language, api_name=api_name)
    if not isinstance(tests, str):
        tests = str(tests)

    # Step 8: Postman
    print("\n[pipeline] Step 8: Generating Postman collection...")
    postman_collection = generate_postman_collection(parsed, api_name)
    postman_json = collection_to_json(postman_collection)

    print("\n========== DOCSMITH PIPELINE COMPLETE ==========")

    return {
        "scraped": scraped,
        "index_data": index_data,
        "parsed": parsed,
        "intent": intent,
        "code": code,
        "tests": tests,
        "postman_json": postman_json,
        "api_name": api_name,
        "language": language,
    }