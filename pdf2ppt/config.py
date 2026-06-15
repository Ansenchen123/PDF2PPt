from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

try:
    import keyring
except Exception:  # pragma: no cover - optional runtime dependency can fail on headless hosts.
    keyring = None


ENV_PATH = Path(".env")
SERVICE_NAME = "PDF2PPt"

PROVIDER_ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}


def load_environment(env_path: str | Path = ENV_PATH) -> None:
    load_dotenv(env_path, override=False)


def get_provider_api_key(
    provider: str,
    explicit_key: str | None = None,
    *,
    allow_keyring: bool = True,
) -> str | None:
    if explicit_key:
        return explicit_key
    load_environment()
    normalized = provider.lower()
    env_key = PROVIDER_ENV_KEYS.get(normalized)
    if env_key:
        value = os.getenv(env_key)
        if value:
            return value
    if allow_keyring and keyring is not None:
        try:
            return keyring.get_password(SERVICE_NAME, normalized)
        except Exception:
            return None
    return None


def get_proxy_config() -> tuple[str | None, str | None]:
    load_environment()
    return os.getenv("PDF2PPT_PROXY_URL"), os.getenv("PDF2PPT_PROXY_TOKEN")


def set_provider_api_key(provider: str, api_key: str) -> None:
    normalized = provider.lower()
    if keyring is None:
        env_key = PROVIDER_ENV_KEYS.get(normalized)
        if env_key:
            os.environ[env_key] = api_key
        return
    keyring.set_password(SERVICE_NAME, normalized, api_key)
