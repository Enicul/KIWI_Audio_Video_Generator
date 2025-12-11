#!/usr/bin/env python
"""Check if environment is properly configured."""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("⚠️  Warning: Python 3.10+ recommended")
        return False
    return True

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "loguru": "Loguru",
        "google.genai": "Google GenAI",
        "google.cloud.storage": "Google Cloud Storage",
        "moviepy": "MoviePy",
    }

    missing = []

    for module, name in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} NOT installed")
            missing.append(name)

    return len(missing) == 0, missing

def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")

    if env_file.exists():
        print("✓ .env file exists")

        # Check for key variables
        with open(env_file) as f:
            content = f.read()

        required_vars = [
            "GEMINI_API_KEY",
            "GCP_PROJECT_ID",
            "GCS_BUCKET",
            "ELEVENLABS_API_KEY"
        ]

        for var in required_vars:
            if var in content and not content.split(f"{var}=")[1].split("\n")[0].startswith("your_"):
                print(f"  ✓ {var} configured")
            else:
                print(f"  ⚠️  {var} not configured or using placeholder")

        return True
    else:
        print("✗ .env file NOT found")
        print("  Run: cp .env.example .env")
        return False

def check_workspace():
    """Check if workspace directory exists."""
    workspace = Path("workspaces")

    if not workspace.exists():
        print("⚠️  workspaces directory not found, creating...")
        workspace.mkdir(parents=True, exist_ok=True)
        print("✓ workspaces directory created")
    else:
        print("✓ workspaces directory exists")

    return True

def main():
    """Run all checks."""
    print("=" * 50)
    print("KIWI-Video Environment Check")
    print("=" * 50)
    print()

    all_good = True

    print("1. Checking Python version...")
    all_good &= check_python_version()
    print()

    print("2. Checking dependencies...")
    deps_ok, missing = check_dependencies()
    all_good &= deps_ok
    print()

    print("3. Checking configuration...")
    all_good &= check_env_file()
    print()

    print("4. Checking workspace...")
    all_good &= check_workspace()
    print()

    print("=" * 50)
    if all_good:
        print("✅ Environment is ready!")
        print("\nTo start the API server:")
        print("  uvicorn kiwi_video.api.app:app --reload")
    else:
        print("⚠️  Some issues found. Please fix them.")
        if missing:
            print("\nInstall missing packages:")
            print("  pip install -e .")
    print("=" * 50)

if __name__ == "__main__":
    main()

