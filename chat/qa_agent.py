import os
import json
from groq import Groq
from dotenv import load_dotenv
from core.retriever import retrieve_context

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_prompt() -> str:
    with open("prompts/qa_prompt.txt", "r") as f:
        return f.read()


def answer_question(
    question: str,
    index_data: dict,
    chat_history: list = [],
    parsed_data: dict = None
) -> str:
    chat_history = chat_history
    """
    Answers a developer's question using hybrid RAG over the indexed docs.
    Also injects extracted endpoints directly so the agent always knows them.

    Args:
        question: Developer's question
        index_data: Output from indexer.build_index()
        chat_history: List of previous messages
        parsed_data: Output from parser — contains endpoints, auth, base_url

    Returns:
        Answer string from Groq
    """
    print(f"[qa_agent] Question: {question}")

    # RAG context from scraped docs
    context = retrieve_context(
        query=question,
        index_data=index_data,
        top_k=3,
        max_chars=2500
    )

    # Build structured endpoints section from parsed data
    endpoints_section = ""
    if parsed_data and parsed_data.get("endpoints"):
        endpoints = parsed_data["endpoints"]
        base_url = parsed_data.get("base_url", "")
        auth_method = parsed_data.get("auth_method", "")
        auth_header = parsed_data.get("auth_header", "")

        ep_lines = []
        for ep in endpoints:
            method = ep.get("method", "?")
            path = ep.get("path", "?")
            desc = ep.get("description", "")
            params = ep.get("parameters", [])
            param_str = ", ".join(
                f"{p.get('name')} ({p.get('type','')})"
                for p in params
            ) if params else "none"
            ep_lines.append(
                f"  - {method} {path} — {desc} | params: {param_str}"
            )

        endpoints_section = f"""
--- EXTRACTED API ENDPOINTS ---
Base URL: {base_url}
Auth Method: {auth_method}
Auth Header: {auth_header}

Endpoints:
{chr(10).join(ep_lines)}
--- END ENDPOINTS ---
"""

    system_prompt = load_prompt()
    system_with_context = f"""{system_prompt}

{endpoints_section}

--- DOCUMENTATION CONTEXT ---
{context}
--- END CONTEXT ---

IMPORTANT: You have the extracted endpoints listed above. Always use them to answer questions about available endpoints, methods, paths, and parameters. Never say endpoints are not available if they are listed above."""

    messages = [{"role": "system", "content": system_with_context}]
    messages.extend(chat_history[-6:])
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=1024
    )

    answer = response.choices[0].message.content.strip()
    print("[qa_agent] Answer generated...")
    return answer