import json
import os
from groq import Groq
from dotenv import load_dotenv
from core.retriever import retrieve_context

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def load_prompt() -> str:
    with open("prompts/intent_prompt.txt", "r") as f:
        return f.read()

def filter_by_intent(
    use_case: str,
    parsed_data: dict,
    index_data: dict
) -> dict:
    """
    Filters extracted endpoints to only those relevant to the use case.
    Also suggests SDK vs REST integration path.

    Args:
        use_case: Developer's plain English description
        parsed_data: Output from parser.parse_endpoints()
        index_data: Output from indexer.build_index()

    Returns:
        Dict with relevant endpoints + integration recommendation
    """
    print("[intent] Retrieving context for use case...")
    context = retrieve_context(
        query=use_case,
        index_data=index_data,
        top_k=4
    )

    system_prompt = load_prompt()
    user_message = f"""Developer use case: {use_case}

Available endpoints:
{json.dumps(parsed_data.get('endpoints', []), indent=2)}

Additional context from documentation:
{context}

Auth method: {parsed_data.get('auth_method', 'Unknown')}
SDK available: {parsed_data.get('sdk_available', False)}
SDK name: {parsed_data.get('sdk_name', 'None')}

Identify the relevant endpoints for this use case and recommend integration path."""

    print("[intent] Calling Groq...")
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
        result = json.loads(raw)
        print(f"[intent] Identified {len(result.get('relevant_endpoints', []))} relevant endpoints")
        return result
    except json.JSONDecodeError as e:
        print(f"[intent] JSON parse error: {e}")
        return {
            "relevant_endpoints": parsed_data.get("endpoints", []),
            "integration_path": "REST",
            "sdk_recommended": False,
            "explanation": "Could not filter endpoints automatically."
        }