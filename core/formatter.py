import subprocess
from pathlib import Path


def format_code(file_path: str, language: str = "python") -> tuple[bool, str]:
    """
    Format the generated code.

    Returns:
        (success, message)
    """

    file_path = Path(file_path)

    if not file_path.exists():
        return False, f"{file_path} not found."

    try:

        if language.lower() == "python":

            result = subprocess.run(
                ["black", str(file_path)],
                capture_output=True,
                text=True,
            )

        elif language.lower() in ["javascript", "typescript"]:

            result = subprocess.run(
                ["prettier", "--write", str(file_path)],
                capture_output=True,
                text=True,
            )

        else:
            return False, f"Formatting not supported for {language}"

        if result.returncode == 0:
            return True, "Formatting successful."

        return False, result.stderr

    except Exception as e:
        return False, str(e)