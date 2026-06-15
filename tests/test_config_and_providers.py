import json
from pathlib import Path

import pytest

from pdf2ppt.config import get_provider_api_key
from pdf2ppt.models import ProviderOptions, ProviderResult
from pdf2ppt.providers.anthropic import AnthropicProvider
from pdf2ppt.providers.common import coerce_provider_result, extract_json_payload, layout_json_schema
from pdf2ppt.providers.gemini import GeminiProvider
from pdf2ppt.providers.mistral import MistralProvider
from pdf2ppt.providers.openai import OpenAIProvider


def test_get_provider_api_key_prefers_explicit_value(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    assert get_provider_api_key("openai", explicit_key="explicit-key") == "explicit-key"


def test_get_provider_api_key_reads_environment(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-anthropic")

    assert get_provider_api_key("anthropic") == "env-anthropic"


def test_extract_json_payload_accepts_markdown_wrapped_json():
    payload = extract_json_payload('```json\n{"text_blocks": [], "warnings": ["ok"]}\n```')

    assert payload == {"text_blocks": [], "warnings": ["ok"]}


def test_coerce_provider_result_validates_blocks():
    payload = {
        "text_blocks": [
            {
                "id": "title",
                "text": "Revenue",
                "box_2d": [100, 100, 200, 800],
                "style": {"font_size_pt": 30, "color_hex": "#111111"},
                "confidence": 0.9,
            }
        ],
        "warnings": ["low contrast"],
    }

    result = coerce_provider_result("openai", "gpt-test", 2, payload)

    assert isinstance(result, ProviderResult)
    assert result.page_number == 2
    assert result.text_blocks[0].text == "Revenue"
    assert result.warnings == ["low contrast"]


def test_layout_json_schema_has_required_text_blocks():
    schema = layout_json_schema()

    assert schema["type"] == "object"
    assert "text_blocks" in schema["required"]
    assert schema["additionalProperties"] is False


def test_openai_payload_uses_responses_text_format(tmp_path: Path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake")
    provider = OpenAIProvider()

    payload = provider.build_payload(image, ProviderOptions(provider="openai", model="gpt-test"))

    assert payload["model"] == "gpt-test"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["input"][1]["content"][0]["type"] == "input_image"


def test_anthropic_payload_puts_image_before_text(tmp_path: Path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake")
    provider = AnthropicProvider()

    payload = provider.build_payload(image, ProviderOptions(provider="anthropic", model="claude-test"))

    content = payload["messages"][0]["content"]
    assert content[0]["type"] == "image"
    assert content[1]["type"] == "text"
    assert payload["output_config"]["format"]["type"] == "json_schema"


def test_gemini_payload_uses_inline_data_and_response_schema(tmp_path: Path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake")
    provider = GeminiProvider()

    payload = provider.build_payload(image, ProviderOptions(provider="gemini", model="gemini-test"))

    assert payload["contents"][0]["parts"][0]["inline_data"]["mime_type"] == "image/png"
    assert payload["generationConfig"]["response_mime_type"] == "application/json"


def test_mistral_payload_uses_chat_vision_image_url(tmp_path: Path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake")
    provider = MistralProvider()

    payload = provider.build_payload(image, ProviderOptions(provider="mistral", model="mistral-test"))
    content = payload["messages"][0]["content"]

    assert payload["model"] == "mistral-test"
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image_url"


def test_provider_result_rejects_invalid_json_shape():
    with pytest.raises(ValueError):
        coerce_provider_result("openai", "gpt-test", 1, {"unexpected": []})
