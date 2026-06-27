import os
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_prompt() -> str:
    with open("prompts/testgen_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def clean_markdown(text: str, language: str) -> str:
    """
    Remove Markdown code fences from LLM output.
    """

    if "```" not in text:
        return text.strip()

    parts = text.split("```")

    if len(parts) >= 3:
        code = parts[1]

        prefixes = [
            language.lower(),
            "python",
            "javascript",
            "typescript",
            "java",
        ]

        for prefix in prefixes:
            if code.startswith(prefix):
                code = code[len(prefix):]
                break

        return code.strip()

    return text.strip()


def generate_tests(
    wrapper_code: str,
    language: str = "Python",
    api_name: str = "API",
    output_path: str = "generated/test_wrapper.py",
) -> str:
    """
    Generate runnable unit tests for the wrapper.
    """

    system_prompt = load_prompt()

    user_prompt = f"""
Generate production-quality unit tests.

API Name:
{api_name}

Language:
{language}

Wrapper Code:

{wrapper_code}

Requirements:

1. Use pytest.
2. Mock every HTTP request.
3. Never call the real API.
4. Test every public method.
5. Test authentication.
6. Test invalid inputs.
7. Test HTTP errors.
8. Test exceptions.
9. Test successful responses.
10. Tests must run without modification.

Return ONLY code.
"""

    print(f"[testgen] Generating {language} tests...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0,
        max_tokens=4096,
    )

    tests = clean_markdown(
        response.choices[0].message.content,
        language,
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_file.write_text(
        tests,
        encoding="utf-8",
    )

    print(f"[testgen] Tests saved to {output_path}")

    return tests