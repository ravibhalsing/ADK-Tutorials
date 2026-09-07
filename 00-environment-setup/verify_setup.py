"""Module 00 — environment self-check.

Run it with your venv active:
    python 00-environment-setup/verify_setup.py

It checks (and explains any failure):
  1. Python version is 3.10–3.13
  2. Running inside a virtual environment
  3. `google-adk` importable and version is 2.x
  4. The `adk` CLI is on PATH
  5. Credentials resolve — Vertex path (project + location + ADC) or AI Studio key.
     Reads examples/ex01_hello_agent/.env if your shell env doesn't have them.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import sys
from importlib import metadata

GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def ok(msg: str) -> bool:
    print(f"{GREEN}[ OK ]{RESET} {msg}")
    return True


def fail(msg: str, fix: str) -> bool:
    print(f"{RED}[FAIL]{RESET} {msg}\n       fix: {fix}")
    return False


def warn(msg: str, fix: str) -> bool:
    print(f"{YELLOW}[WARN]{RESET} {msg}\n       {fix}")
    return True


def check_python() -> bool:
    major, minor = sys.version_info[:2]
    v = f"{major}.{minor}.{sys.version_info.micro}"
    if major == 3 and 10 <= minor <= 13:
        return ok(f"Python {v}")
    if major == 3 and minor >= 14:
        return fail(
            f"Python {v} — too new; some ADK/GCP deps lack wheels",
            "recreate the venv with 3.13:  py -3.13 -m venv .venv",
        )
    return fail(f"Python {v} — ADK needs >=3.10", "install Python 3.13 and rebuild the venv")


def check_venv() -> bool:
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        return ok(f"virtual env active: {sys.prefix}")
    return fail(
        "not running inside a virtual environment",
        r"activate it:  .\.venv\Scripts\Activate.ps1  (Windows)  /  source .venv/bin/activate",
    )


def check_adk_package() -> bool:
    try:
        import google.adk  # noqa: F401
    except ImportError:
        return fail(
            "cannot import google.adk",
            'python -m pip install "google-adk>=2,<3"',
        )
    try:
        ver = metadata.version("google-adk")
    except metadata.PackageNotFoundError:
        ver = getattr(__import__("google.adk", fromlist=["__version__"]), "__version__", "unknown")
    major = ver.split(".")[0]
    if major == "2":
        return ok(f"google-adk {ver}")
    return warn(
        f"google-adk {ver} — course targets 2.x",
        'upgrade:  python -m pip install -U "google-adk>=2,<3"',
    )


def check_adk_cli() -> bool:
    path = shutil.which("adk")
    if path:
        return ok(f"adk CLI on PATH: {path}")
    return fail(
        "`adk` not found on PATH",
        "activate the venv (the CLI lives in .venv\\Scripts). If still missing: "
        'python -m pip install --force-reinstall "google-adk>=2,<3"',
    )


def _load_example_env() -> None:
    """Best-effort: load the hello-agent .env so this check reflects course config."""
    env_path = (
        pathlib.Path(__file__).parent / "examples" / "ex01_hello_agent" / ".env"
    )
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def _adc_present() -> bool:
    """True if gcloud Application Default Credentials look configured."""
    candidates = [
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        os.path.expandvars(r"%APPDATA%\gcloud\application_default_credentials.json"),
        os.path.expanduser("~/.config/gcloud/application_default_credentials.json"),
    ]
    return any(c and pathlib.Path(c).exists() for c in candidates)


def check_credentials() -> bool:
    _load_example_env()
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower()
    if use_vertex in {"1", "true", "yes"}:
        proj = os.getenv("GOOGLE_CLOUD_PROJECT")
        loc = os.getenv("GOOGLE_CLOUD_LOCATION")
        if not (proj and loc):
            return fail(
                "Vertex path selected but GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION missing",
                "set both in the agent's .env",
            )
        if not _adc_present():
            return fail(
                f"Vertex path (project={proj}, {loc}) but no ADC found",
                "run: gcloud auth application-default login",
            )
        return ok(f"Vertex path: project={proj} location={loc}, ADC present")
    if os.getenv("GOOGLE_API_KEY"):
        return ok("AI Studio path: GOOGLE_API_KEY is set")
    return warn(
        "no credential resolved",
        "expected only if you haven't filled in examples/ex01_hello_agent/.env yet.",
    )


def main() -> int:
    print("ADK environment check\n" + "-" * 40)
    results = [
        check_python(),
        check_venv(),
        check_adk_package(),
        check_adk_cli(),
        check_credentials(),
    ]
    print("-" * 40)
    if all(results):
        print(f"{GREEN}All checks passed — you're ready for Module 01.{RESET}")
        return 0
    print(f"{RED}Some checks failed — fix the items above, then re-run.{RESET}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
