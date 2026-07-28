import subprocess
import sys


def test_cli_help_exposes_provider_and_proxy_options():
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--provider" in result.stdout
    assert "--auth-mode" in result.stdout
    assert "--proxy-url" in result.stdout
