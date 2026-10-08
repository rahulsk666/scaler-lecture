# Meridian Retail Support Draft Review Tool

A minimal CLI tool that drafts customer support replies for human review, using the Gemini API and a supplied policy.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the setup script to configure your API key:
   ```bash
   python setup_env.py
   ```
   This will prompt for your Gemini API key (hidden input) and model name, then write a `.env` file.

## Usage

```bash
# Draft a reply for a case
python app.py --case C1

# Simulate a timeout (no API call)
python app.py --case C1 --simulate-timeout

# Use prerecorded demo output (no API call)
python app.py --case C1 --offline-demo
```

## Safety

- This tool drafts for human review only. It cannot approve refunds, send messages, or change records.
- The API key is read only from `APP_GEMINI_API_KEY` (via `.env` or environment variable).
- The model defaults to `gemini-2.0-flash` but can be overridden via `APP_GEMINI_MODEL`.

## Files

- `app.py` - Main CLI entry point
- `setup_env.py` - Interactive setup script
- `cases.json` - Sample case data
- `policy.md` - Support drafting policy
- `demo_outputs.json` - Prerecorded synthetic results for offline demo
- `requirements.txt` - Pinned dependencies
