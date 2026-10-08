#!/usr/bin/env python3
"""Meridian Retail support-draft review tool."""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = Path(__file__).parent
CASES_FILE = BASE_DIR / "cases.json"
POLICY_FILE = BASE_DIR / "policy.md"
DEMO_FILE = BASE_DIR / "demo_outputs.json"

DEFAULT_MODEL = "gemini-2.0-flash"
VALID_REVIEW_STATUSES = {"READY_FOR_HUMAN_REVIEW", "NEEDS_INFORMATION", "BLOCKED", "UNAVAILABLE"}


def load_cases():
    with open(CASES_FILE) as f:
        return json.load(f)


def load_policy():
    with open(POLICY_FILE) as f:
        return f.read()


def load_demo_outputs():
    with open(DEMO_FILE) as f:
        return json.load(f)


def get_api_key():
    return os.environ.get("APP_GEMINI_API_KEY")


def get_model():
    return os.environ.get("APP_GEMINI_MODEL", DEFAULT_MODEL)


def build_system_prompt(policy_text):
    return f"""You are a support draft assistant for Meridian Retail. You draft replies for human review only.

POLICY:
{policy_text}

RULES:
- Use ONLY the supplied facts and policy.
- Return ONLY valid JSON with exactly these fields:
  - draft_reply: string (the draft reply text)
  - evidence_refs: list of strings (policy IDs like "P1", "P2", etc.)
  - missing_information: list of strings (field names that are missing)
  - review_status: one of "READY_FOR_HUMAN_REVIEW", "NEEDS_INFORMATION", "BLOCKED"
- Never send messages, approve refunds, or change records.
- If information is missing, set review_status to "NEEDS_INFORMATION" and list the missing fields.
"""


def build_user_prompt(case):
    return f"""CASE:
{json.dumps(case, indent=2)}

Draft a reply following the policy. Return only the JSON object."""


def call_model(case, policy_text, api_key, model_name):
    if genai is None:
        raise RuntimeError("google-genai package is not installed")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=build_user_prompt(case),
        config=types.GenerateContentConfig(
            system_instruction=build_system_prompt(policy_text)
        )
    )
    text = response.text
    return json.loads(text)


def validate_result(result):
    if not isinstance(result, dict):
        return False
    if not isinstance(result.get("draft_reply"), str):
        return False
    if not isinstance(result.get("evidence_refs"), list):
        return False
    if not isinstance(result.get("missing_information"), list):
        return False
    if result.get("review_status") not in VALID_REVIEW_STATUSES:
        return False
    return True


def print_section(title, content):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(content)


def unavailable_result():
    return {
        "draft_reply": "",
        "evidence_refs": [],
        "missing_information": [],
        "review_status": "UNAVAILABLE",
    }


def run_simulate_timeout(case):
    result = unavailable_result()
    print("\n[SIMULATED TIMEOUT] No API call was made.")
    print("Manual fallback: Please review this case manually. The model API is unavailable.")
    print_section("DRAFT RESULT FOR HUMAN REVIEW", json.dumps(result, indent=2))


def run_offline_demo(case):
    demo_outputs = load_demo_outputs()
    case_id = case["case_id"]
    if case_id not in demo_outputs:
        print(f"No offline demo output for case {case_id}")
        return
    result = demo_outputs[case_id]
    print("\n[OFFLINE DEMO] No model API was called.")
    print_section("DRAFT RESULT FOR HUMAN REVIEW", json.dumps(result, indent=2))


def missing_delivery_date_result():
    return {
        "draft_reply": "Before Meridian Retail can assess whether this case falls within the two-day damage-reporting rule, please provide the delivery date. A human support agent will review the request once that information is available.",
        "evidence_refs": ["P2", "P4"],
        "missing_information": ["delivery_date"],
        "review_status": "NEEDS_INFORMATION",
    }


def run_live(case, policy_text):
    # Pre-model check: if delivery_date is missing or empty, return deterministic result
    if not case.get("delivery_date"):
        result = missing_delivery_date_result()
        print("\n[PRE-MODEL CHECK] delivery_date is missing — skipping model call.")
        print_section("DRAFT RESULT FOR HUMAN REVIEW", json.dumps(result, indent=2))
        return

    api_key = get_api_key()
    if not api_key:
        print("Error: APP_GEMINI_API_KEY is not set.")
        sys.exit(1)

    model_name = get_model()

    try:
        result = call_model(case, policy_text, api_key, model_name)
    except Exception as e:
        print(f"\n[ERROR] Model API call failed: {e}")
        result = unavailable_result()
        print("Manual fallback: Please review this case manually. The model API is unavailable.")
        print_section("DRAFT RESULT FOR HUMAN REVIEW", json.dumps(result, indent=2))
        return

    if not validate_result(result):
        print("\n[ERROR] Model returned invalid structure.")
        result = unavailable_result()
        print("Manual fallback: Please review this case manually. The model returned an invalid response.")

    print_section("DRAFT RESULT FOR HUMAN REVIEW", json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Meridian Retail support draft review tool")
    parser.add_argument("--case", choices=["C1", "C2", "C3"], required=True, help="Case ID to process")
    parser.add_argument("--simulate-timeout", action="store_true", help="Simulate a timeout (no API call)")
    parser.add_argument("--offline-demo", action="store_true", help="Use prerecorded demo output (no API call)")
    args = parser.parse_args()

    if args.simulate_timeout and args.offline_demo:
        parser.error("--simulate-timeout and --offline-demo are mutually exclusive")

    # Load data
    cases = load_cases()
    policy_text = load_policy()
    case = cases[args.case]

    # Print supplied facts and policy
    print_section("SUPPLIED FACTS", json.dumps(case, indent=2))
    print_section("SUPPLIED POLICY", policy_text)

    # Run the appropriate mode
    if args.simulate_timeout:
        run_simulate_timeout(case)
    elif args.offline_demo:
        run_offline_demo(case)
    else:
        run_live(case, policy_text)


if __name__ == "__main__":
    main()
