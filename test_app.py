import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import app


def test_all_input_files_exist():
    assert app.CASES_FILE.exists()
    assert app.POLICY_FILE.exists()
    assert app.DEMO_FILE.exists()


def test_cases_json_structure():
    cases = app.load_cases()
    assert "C1" in cases
    assert "C2" in cases
    assert "C3" in cases


def test_policy_md_content():
    policy = app.load_policy()
    assert "P1" in policy
    assert "P2" in policy
    assert "P3" in policy
    assert "P4" in policy


def test_successful_c1(monkeypatch, capsys):
    fake_result = {
        "draft_reply": "Thank you for reporting...",
        "evidence_refs": ["P1"],
        "missing_information": [],
        "review_status": "READY_FOR_HUMAN_REVIEW",
    }
    monkeypatch.setattr(app, "call_model", lambda *args, **kwargs: fake_result)
    monkeypatch.setattr(app, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(app, "get_model", lambda: "test-model")

    monkeypatch.setattr(sys, "argv", ["app.py", "--case", "C1"])
    app.main()

    captured = capsys.readouterr()
    assert "SUPPLIED FACTS" in captured.out
    assert "SUPPLIED POLICY" in captured.out
    assert "DRAFT RESULT FOR HUMAN REVIEW" in captured.out
    assert "READY_FOR_HUMAN_REVIEW" in captured.out


def test_invalid_model_output(monkeypatch, capsys):
    invalid_result = {"wrong": "structure"}
    monkeypatch.setattr(app, "call_model", lambda *args, **kwargs: invalid_result)
    monkeypatch.setattr(app, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(app, "get_model", lambda: "test-model")

    monkeypatch.setattr(sys, "argv", ["app.py", "--case", "C1"])
    app.main()

    captured = capsys.readouterr()
    assert "UNAVAILABLE" in captured.out


def test_timeout_behaviour(monkeypatch, capsys):
    def raise_timeout(*args, **kwargs):
        raise Exception("timeout")
    monkeypatch.setattr(app, "call_model", raise_timeout)
    monkeypatch.setattr(app, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(app, "get_model", lambda: "test-model")

    monkeypatch.setattr(sys, "argv", ["app.py", "--case", "C1"])
    app.main()

    captured = capsys.readouterr()
    assert "UNAVAILABLE" in captured.out


def test_simulate_timeout_flag(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["app.py", "--case", "C1", "--simulate-timeout"])
    app.main()

    captured = capsys.readouterr()
    assert "UNAVAILABLE" in captured.out
    assert "SIMULATED TIMEOUT" in captured.out


def test_offline_demo(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["app.py", "--case", "C1", "--offline-demo"])
    app.main()

    captured = capsys.readouterr()
    assert "OFFLINE DEMO" in captured.out
    assert "No model API was called" in captured.out


def test_missing_delivery_date_skips_model(monkeypatch, capsys):
    """C2 has no delivery_date — model must not be called."""
    def forbidden_model(*args, **kwargs):
        raise AssertionError("Model should not be called when delivery_date is missing")

    monkeypatch.setattr(app, "call_model", forbidden_model)
    monkeypatch.setattr(app, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(app, "get_model", lambda: "test-model")

    monkeypatch.setattr(sys, "argv", ["app.py", "--case", "C2"])
    app.main()

    captured = capsys.readouterr()
    assert "PRE-MODEL CHECK" in captured.out
    assert "NEEDS_INFORMATION" in captured.out
    assert "delivery_date" in captured.out
    assert "P2" in captured.out
    assert "P4" in captured.out
