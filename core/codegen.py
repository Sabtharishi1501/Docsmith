import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_prompt() -> str:
    with open("prompts/codegen_prompt.txt", "r") as f:
        return f.read()


def generate_wrapper(
    parsed_data: dict,
    intent_data: dict,
    language: str,
    api_name: str = "API"
) -> str:
    """
    Generates a production-ready wrapper class for the API.
    """
    relevant_endpoints = intent_data.get("relevant_endpoints", [])[:5]
    integration_path = intent_data.get("integration_path", "REST")
    sdk_recommended = intent_data.get("sdk_recommended", False)
    explanation = intent_data.get("explanation", "")

    system_prompt = load_prompt()
    user_message = f"""Generate a {language} wrapper class for the {api_name} API.

API Details:
- Base URL: {parsed_data.get('base_url', 'https://api.example.com')}
- Auth Method: {parsed_data.get('auth_method', 'API Key')}
- Auth Header: {parsed_data.get('auth_header', '')}
- Integration Path: {integration_path}
- SDK Recommended: {sdk_recommended}
- SDK Name: {parsed_data.get('sdk_name', 'None')}
- SDK Install: {parsed_data.get('sdk_install', 'None')}

Relevant Endpoints:
{json.dumps(relevant_endpoints, indent=2)}

Integration Notes:
{explanation}

Generate a complete, ready-to-use {language} wrapper class."""

    print(f"[codegen] Generating {language} wrapper...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.2,
        max_tokens=2048
    )

    code = response.choices[0].message.content.strip()

    if "```" in code:
        parts = code.split("```")
        if len(parts) >= 3:
            code = parts[1]
            for prefix in [language.lower(), "python", "javascript", "typescript", "java"]:
                if code.startswith(prefix):
                    code = code[len(prefix):]
                    break
        code = code.strip()

    print("[codegen] Wrapper class generated")
    return code