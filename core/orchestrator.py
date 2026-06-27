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
    max_pages: int = 10
) -> dict:

    print("\n========== DOCSMITH PIPELINE START ==========")

    # Step 1: Scrape
    print("\n[pipeline] Step 1: Scraping documentation...")
    scraped = scrape_docs(url, max_pages=max_pages)
    if not scraped["content"]:
        raise ValueError("Could not extract content from the provided URL.")

    # Step 2: Chunk
    print("\n[pipeline] Step 2: Chunking text...")
    chunks = chunk_text(scraped["content"], chunk_size=500, overlap=50)

    # Step 3: Index
    print("\n[pipeline] Step 3: Building hybrid index...")
    index_data = build_index(chunks)

    # Step 4: Parse
    print("\n[pipeline] Step 4: Extracting endpoints and auth...")
    parsed = parse_endpoints(scraped, index_data)

    # Ensure parsed is a dict
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

    # Step 5: Intent
    print("\n[pipeline] Step 5: Filtering by use case...")
    intent = filter_by_intent(use_case, parsed, index_data)

    # Ensure intent is a dict
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

    # Ensure code is a string
    if not isinstance(code, str):
        code = str(code)

    os.makedirs("generated", exist_ok=True)
    wrapper_path = "generated/wrapper.py"

    with open(wrapper_path, "w", encoding="utf-8") as f:
        f.write(code)

    # Validation loop — wrapper only, no test running
    for attempt in range(MAX_RETRIES):
        print(f"\n========== ITERATION {attempt + 1}/{MAX_RETRIES} ==========")

        # Format
        print("[pipeline] Formatting wrapper...")
        success, message = format_code(wrapper_path, language)
        print("[formatter]", message)

        with open(wrapper_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Validate
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

        # Ensure fix returned a string
        if not isinstance(code, str):
            code = str(code)

        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write(code)
    else:
        print("[pipeline] Max retries reached — using last valid code.")

    # Read final wrapper
    with open(wrapper_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Step 7: Generate tests (display only — no test running)
    print("\n[pipeline] Step 7: Generating unit tests...")
    tests = generate_tests(
        wrapper_code=code,
        language=language,
        api_name=api_name,
    )
    if not isinstance(tests, str):
        tests = str(tests)

    # Step 8: Postman collection
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