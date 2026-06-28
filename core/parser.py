import json
import os
from groq import Groq
from dotenv import load_dotenv
from core.retriever import retrieve_context
from core.endpoint_extractor import extract_candidates

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_prompt() -> str:
    with open("prompts/parser_prompt.txt", "r") as f:
        return f.read()


def parse_endpoints(
    scraped_data: dict,
    index_data: dict,
    seed_endpoints: list | None = None,
) -> dict:
    """
    Parses API documentation into structured endpoint definitions.

    Args:
        scraped_data:    Output from scrape_docs()
        index_data:      Output from build_index()
        seed_endpoints:  Optional list of {method, path} dicts already
                         extracted by the scraper — skips re-extraction
                         when provided, saving time and improving accuracy.
    """
    print("[parser] Retrieving relevant chunks...")

    # Use RAG retrieval instead of a raw content slice —
    context = retrieve_context(
        query="API endpoints authentication base URL parameters",
        index_data=index_data,
        top_k=6,
        max_chars=8000,
    )

    # Use seeds if provided, otherwise fall back to regex extraction
    if seed_endpoints:
        print(f"[parser] Using {len(seed_endpoints)} pre-extracted endpoints from scraper")
        candidate_endpoints = [
            {"method": ep["method"], "path": ep["path"]}
            for ep in seed_endpoints
        ]
    else:
        print("[parser] No seed endpoints — running regex extraction...")
        candidate_endpoints = extract_candidates(context)

    print("[parser] Candidate endpoints:")
    for ep in candidate_endpoints:
        print(f"  {ep['method']} {ep['path']}")

    system_prompt = load_prompt()
    endpoint_list = "\n".join(
        f"{ep['method']} {ep['path']}"
        for ep in candidate_endpoints
    )

    user_message = f"""
The following API endpoints have already been extracted from the documentation:

{endpoint_list}

Documentation:

{context}

Your task:
1. Use ONLY the endpoints listed above — do NOT invent new ones.
2. For each endpoint extract:
   - description
   - parameters (name, type, required, description)
   - returns
3. Also extract:
   - base_url
   - auth_method
   - auth_header
   - sdk_available (true/false)
   - sdk_name
   - sdk_install
4. For any endpoint whose method is "?", infer the correct HTTP method
   from REST conventions and its description:
   - Retrieve / List / Get → GET
   - Create / Add / Submit → POST
   - Update / Modify (full) → PUT
   - Update / Modify (partial) → PATCH
   - Delete / Remove → DELETE

Return ONLY valid JSON, no markdown fences.
"""

    print("[parser] Calling Groq...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0,
        max_tokens=2048
    )

    raw = response.choices[0].message.content.strip()

    try:
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        print(f"[parser] Extracted {len(parsed.get('endpoints', []))} endpoints")
        return parsed
    except json.JSONDecodeError as e:
        print(f"[parser] JSON parse error: {e}")

        return {
            "base_url": "",
            "auth_method": "Unknown",
            "auth_header": "",
            "sdk_available": False,
            "sdk_name": None,
            "sdk_install": None,
            "endpoints": [
                {"method": ep["method"], "path": ep["path"],
                 "description": "", "parameters": [], "returns": ""}
                for ep in candidate_endpoints
            ]
        }