import re
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_prompt() -> str:
    try:
        with open("prompts/fixer_prompt.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        return """You are an expert Python/JavaScript developer.
Fix the code errors shown below. Return ONLY the fixed code, no explanation, no markdown backticks."""


def _fix_unused_imports(code: str, ruff_output: str) -> str:
    """Remove unused imports locally without calling Groq."""
    lines = code.split('\n')
    lines_to_remove = set()

    for line in ruff_output.split('\n'):
        # F401 unused import pattern
        if 'F401' in line and 'imported but unused' in line:
            # Extract the import name
            match = re.search(r'`(.+?)`', line)
            if match:
                import_name = match.group(1).split('.')[-1]
                for i, code_line in enumerate(lines):
                    stripped = code_line.strip()
                    if (stripped.startswith('import ') or
                            stripped.startswith('from ')):
                        if import_name in stripped:
                            lines_to_remove.add(i)

    return '\n'.join(
        line for i, line in enumerate(lines)
        if i not in lines_to_remove
    )


def _fix_import_order(code: str) -> str:
    """Sort imports: stdlib first, then third-party."""
    stdlib_modules = {
        'os', 'sys', 'json', 're', 'time', 'datetime', 'typing',
        'collections', 'itertools', 'functools', 'pathlib', 'io',
        'math', 'random', 'string', 'copy', 'abc', 'dataclasses',
        'enum', 'logging', 'threading', 'subprocess', 'urllib',
        'http', 'base64', 'hashlib', 'hmac', 'uuid', 'tempfile'
    }

    lines = code.split('\n')
    stdlib_imports = []
    third_party_imports = []
    other_lines = []
    in_imports = True

    for line in lines:
        stripped = line.strip()
        if in_imports and (
            stripped.startswith('import ') or
            stripped.startswith('from ')
        ):
            # Determine if stdlib or third-party
            module = stripped.split()[1].split('.')[0]
            if module in stdlib_modules:
                stdlib_imports.append(line)
            else:
                third_party_imports.append(line)
        else:
            if stripped and not stripped.startswith('#'):
                in_imports = False
            other_lines.append(line)

    result = []
    if stdlib_imports:
        result.extend(stdlib_imports)
    if third_party_imports:
        if stdlib_imports:
            result.append('')
        result.extend(third_party_imports)
    if other_lines:
        result.append('')
        result.extend(other_lines)

    return '\n'.join(result)


def _is_simple_error(errors: str) -> bool:
    """Check if errors are simple enough to fix locally."""
    simple_patterns = [
        'F401',   # unused import
        'C0411',  # wrong import order
        'E401',   # multiple imports on one line
    ]
    complex_patterns = [
        'SyntaxError',
        'error:',      # MyPy type errors
        'undefined',
        'NameError',
        'AttributeError',
    ]
    for pattern in complex_patterns:
        if pattern in errors:
            return False
    for pattern in simple_patterns:
        if pattern in errors:
            return True
    return False


def fix_code(
    code: str,
    errors: str,
    language: str,
    api_name: str = "API",
    tests: str = ""
) -> str:
    """
    Fix code errors. Tries local fixes first, falls back to Groq
    only for complex errors.
    """
    print(f"[fixer] Analysing errors...")

    # ── Try local fixes first (no Groq call) ──
    if 'F401' in errors and 'imported but unused' in errors:
        print("[fixer] Fixing unused imports locally...")
        code = _fix_unused_imports(code, errors)
        return code

    if 'C0411' in errors or 'wrong-import-order' in errors:
        print("[fixer] Fixing import order locally...")
        code = _fix_import_order(code)
        return code

    # ── Complex errors — use Groq ──
    print("[fixer] Calling Groq for complex fix...")

    system_prompt = load_prompt()
    user_message = f"""Fix the following {language} code errors.

CODE:
{code}

ERRORS:
{errors}

Return ONLY the fixed code. No explanation. No markdown backticks."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1,
        max_tokens=2048
    )

    fixed = response.choices[0].message.content.strip()

    # Clean markdown if present
    if "```" in fixed:
        parts = fixed.split("```")
        if len(parts) >= 3:
            fixed = parts[1]
            for prefix in [language.lower(), "python",
                           "javascript", "typescript"]:
                if fixed.startswith(prefix):
                    fixed = fixed[len(prefix):]
                    break
        fixed = fixed.strip()

    print("[fixer] Groq fix applied")
    return fixed