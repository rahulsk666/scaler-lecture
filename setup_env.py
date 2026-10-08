#!/usr/bin/env python3
"""Interactive setup for Meridian Retail support draft tool."""

import getpass
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
DEFAULT_MODEL = "gemini-2.0-flash"


def main():
    print("Meridian Retail Support Draft Tool - Setup")
    print("=" * 40)

    api_key = getpass.getpass("Enter your Gemini API key: ")
    if not api_key:
        print("Error: API key is required.")
        return

    model = input(f"Enter model name (default: {DEFAULT_MODEL}): ").strip()
    if not model:
        model = DEFAULT_MODEL

    env_content = f"APP_GEMINI_API_KEY={api_key}\nAPP_GEMINI_MODEL={model}\n"

    with open(ENV_FILE, "w") as f:
        f.write(env_content)

    print(f"\nConfiguration written to {ENV_FILE}")
    print("You can now run: python app.py --case C1")


if __name__ == "__main__":
    main()
