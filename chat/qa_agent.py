import os
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
    chat_history: list = []
) -> str:
    """
    Answers a developer's question using hybrid RAG over the indexed docs.
    """
    print(f"[qa_agent] Question: {question}")

    context = retrieve_context(
        query=question,
        index_data=index_data,
        top_k=3,
        max_chars=2500
    )

    system_prompt = load_prompt()
    system_with_context = f"""{system_prompt}

--- DOCUMENTATION CONTEXT ---
{context}
--- END CONTEXT ---"""

    messages = [{"role": "system", "content": system_with_context}]
    messages.extend(chat_history[-4:])
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=1024
    )

    answer = response.choices[0].message.content.strip()
    print("[qa_agent] Answer generated")
    return answer