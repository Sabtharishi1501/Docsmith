import json
import os
from groq import Groq
from dotenv import load_dotenv
from core.retriever import retrieve_context

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_prompt() -> str:
    with open("prompts/parser_prompt.txt", "r") as f:
        return f.read()


def parse_endpoints(scraped_data: dict, index_data: dict) -> dict:
    """
    Uses hybrid RAG + Groq to extract structured endpoints and auth
    from the scraped documentation.
    """
    print("[parser] Retrieving relevant chunks...")
    context = retrieve_context(
        query="API endpoints authentication base URL SDK",
        index_data=index_data,
        top_k=3,
        max_chars=3000
    )

    system_prompt = load_prompt()
    user_message = f"""Here is the API documentation:

{context}

Extract all endpoints, authentication method, base URL, and SDK information from this documentation."""

    print("[parser] Calling Groq...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1,
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
            "endpoints": []
        }