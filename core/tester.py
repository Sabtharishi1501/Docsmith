import subprocess
from pathlib import Path


def run_tests(
    test_directory: str = "generated",
    test_file: str | None = None,
) -> tuple[bool, str]:
    """
    Run pytest on generated tests.

    Args:
        test_directory: Folder containing tests.
        test_file: Optional specific test file.

    Returns:
        (success, output)
    """

    if test_file:
        target = Path(test_directory) / test_file
    else:
        target = Path(test_directory)

    if not target.exists():
        return False, f"{target} does not exist."

    try:

        result = subprocess.run(
            [
                "pytest",
                str(target),
                "-v",
                "--tb=short",
                "--disable-warnings",
            ],
            capture_output=True,
            text=True,
        )

        output = result.stdout + "\n" + result.stderr

        return result.returncode == 0, output

    except Exception as e:
        return False, str(e)


def run_single_test(test_path: str) -> tuple[bool, str]:
    """
    Run a single pytest file.
    """

    return run_tests(
        test_directory=".",
        test_file=test_path,
    )


if __name__ == "__main__":

    success, output = run_tests()

    print("Success:", success)
    print(output)