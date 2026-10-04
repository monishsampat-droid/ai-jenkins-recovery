import json
import os
import subprocess
import sys
from pathlib import Path

from google import genai

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "pipeline_config.json"
REPORTS = ROOT / "reports"


def run_tests(directory, log_name):
    result = subprocess.run(
        [sys.executable, "-m", "pytest", directory, "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    output = result.stdout + result.stderr
    print(output)
    (REPORTS / log_name).write_text(output, encoding="utf-8")
    return result.returncode, output


def main():
    REPORTS.mkdir(exist_ok=True)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
    directory = config["test_directory"]

    # Only simple folder names are permitted.
    if not isinstance(directory, str) or not directory.isidentifier():
        raise ValueError("Invalid test directory setting")

    print(f"\n[1] Running tests using configured folder: {directory}")
    exit_code, output = run_tests(directory, "initial_test.log")

    if exit_code == 0:
        print("Tests already passed. Recovery is unnecessary.")
        return 0
    
    if "--no-ai" in sys.argv:
        print("\nAI recovery is disabled. Build remains failed.")
        return 1

    # This demo repairs missing test-folder configuration only.
    if exit_code != 4 or "file or directory not found" not in output:
        print("Failure is outside this demo's supported recovery scope.")
        return 1

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing")

    candidates = sorted(
        folder.name
        for folder in ROOT.iterdir()
        if folder.is_dir()
        and not folder.name.startswith(".")
        and folder.name.isidentifier()
        and any(folder.glob("test_*.py"))
    )

    if not candidates:
        raise ValueError("No test folders were found")

    prompt = f"""
Diagnose this pytest configuration failure.

Current configuration:
{json.dumps(config)}

Existing folders containing test files:
{json.dumps(candidates)}

Test output:
{output[-6000:]}

Return ONLY a JSON object with these fields:
"diagnosis": a brief explanation
"test_directory": the correct existing test folder

Choose a folder from the supplied list.
Do not propose shell commands, code changes, or changes to tests.
"""

    print("\n[2] Requesting an AI diagnosis...")
    client = genai.Client(api_key=api_key)
    response = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt,
    )

    raw = response.output_text or ""
    (REPORTS / "ai_response.txt").write_text(raw, encoding="utf-8")

    # Accept JSON with or without a Markdown code fence.
    cleaned = raw.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = "\n".join(cleaned.splitlines()[1:-1]).strip()

    suggestion = json.loads(cleaned)
    diagnosis = suggestion.get("diagnosis")
    corrected_directory = suggestion.get("test_directory")

    if not isinstance(diagnosis, str) or not diagnosis.strip():
        raise ValueError("AI returned no valid diagnosis")

    if (
        not isinstance(corrected_directory, str)
        or corrected_directory not in candidates
        or corrected_directory == directory
    ):
        raise ValueError("AI correction failed validation")

    print(f"\n[3] AI diagnosis: {diagnosis}")
    print(f"Validated correction: {directory} -> {corrected_directory}")

    original_config = CONFIG_FILE.read_bytes()
    config["test_directory"] = corrected_directory
    CONFIG_FILE.write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\n[4] Configuration updated. Rerunning tests...")
    try:
        final_code, _ = run_tests(
            corrected_directory, "recovery_test.log"
        )
    except Exception:
        CONFIG_FILE.write_bytes(original_config)
        raise

    if final_code != 0:
        CONFIG_FILE.write_bytes(original_config)
        print("Recovery failed. Original configuration restored.")
        return 1

    summary = {
        "status": "recovered",
        "diagnosis": diagnosis,
        "original_directory": directory,
        "corrected_directory": corrected_directory,
        "initial_exit_code": exit_code,
        "final_exit_code": final_code,
    }
    (REPORTS / "recovery_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("\nSUCCESS: AI-assisted recovery completed.")
    print("Evidence saved in the reports folder.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        # Prevent the API key from appearing in printed errors.
        message = str(error)
        key = os.environ.get("GEMINI_API_KEY")
        if key:
            message = message.replace(key, "[REDACTED]")
        print(f"\nRecovery stopped: {message}")
        sys.exit(1)