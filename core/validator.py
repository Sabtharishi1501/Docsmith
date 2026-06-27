import subprocess
import sys


def validate(filepath: str) -> tuple:
    """
    Validates code using only syntax check + Ruff.
    Skips MyPy and Pylint — too slow for a pipeline.

    Returns:
        (is_valid: bool, report: dict)
    """
    report = {}

    # ── Syntax check ──
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", filepath],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        report["SYNTAX"] = result.stderr.strip()
        return False, report
    report["SYNTAX"] = "Syntax check passed."

    # ── Ruff (fast linter) ──
    result = subprocess.run(
        ["ruff", "check", filepath],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        report["RUFF"] = result.stdout.strip() or result.stderr.strip()
        return False, report
    report["RUFF"] = "Ruff passed."

    return True, report