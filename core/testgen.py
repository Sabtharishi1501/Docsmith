import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_prompt() -> str:
    with open("prompts/testgen_prompt.txt", "r") as f:
        return f.read()


def generate_tests(
    wrapper_code: str,
    language: str,
    api_name: str = "API"
) -> str:
    """
    Generates unit tests for the wrapper class.

    Args:
        wrapper_code: The generated wrapper class code
        language: Target programming language
        api_name: Name of the API

    Returns:
        Test file as a string
    """
    system_prompt = load_prompt()

    user_message = f"""Generate unit tests for this {language} {api_name} wrapper class:

{wrapper_code}

Generate complete, runnable {language} unit tests with mocked HTTP requests.
Cover happy path, error cases, and edge cases for every method."""

    print(f"[testgen] Generating {language} tests...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.2,
        max_tokens=2048
    )

    tests = response.choices[0].message.content.strip()

    # Clean markdown if present
    if "```" in tests:
        parts = tests.split("```")
        if len(parts) >= 3:
            tests = parts[1]
            for prefix in [language.lower(), "python", "javascript",
                           "typescript", "java"]:
                if tests.startswith(prefix):
                    tests = tests[len(prefix):]
                    break
        tests = tests.strip()

    print("[testgen] Tests generated")
    return tests