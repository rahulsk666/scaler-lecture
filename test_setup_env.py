import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import setup_env


def test_setup_env_writes_key_without_printing(capsys, tmp_path):
    env_file = tmp_path / ".env"

    with patch("getpass.getpass", return_value="test-api-key-123"):
        with patch("builtins.input", return_value=""):
            with patch.object(setup_env, "ENV_FILE", env_file):
                setup_env.main()

    content = env_file.read_text()
    assert "APP_GEMINI_API_KEY=test-api-key-123" in content
    assert "APP_GEMINI_MODEL=gemini-2.0-flash" in content

    captured = capsys.readouterr()
    assert "test-api-key-123" not in captured.out


def test_setup_env_custom_model(capsys, tmp_path):
    env_file = tmp_path / ".env"

    with patch("getpass.getpass", return_value="my-key"):
        with patch("builtins.input", return_value="gemini-2.5-pro"):
            with patch.object(setup_env, "ENV_FILE", env_file):
                setup_env.main()

    content = env_file.read_text()
    assert "APP_GEMINI_API_KEY=my-key" in content
    assert "APP_GEMINI_MODEL=gemini-2.5-pro" in content
