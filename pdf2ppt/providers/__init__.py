from pdf2ppt.providers.base import LayoutProvider, ProviderError
from pdf2ppt.providers.mock import MockProvider


def get_provider(name: str) -> LayoutProvider:
    normalized = name.lower()
    if normalized == "mock":
        return MockProvider()
    if normalized == "gemini":
        from pdf2ppt.providers.gemini import GeminiProvider

        return GeminiProvider()
    if normalized == "openai":
        from pdf2ppt.providers.openai import OpenAIProvider

        return OpenAIProvider()
    if normalized == "anthropic":
        from pdf2ppt.providers.anthropic import AnthropicProvider

        return AnthropicProvider()
    if normalized == "mistral":
        from pdf2ppt.providers.mistral import MistralProvider

        return MistralProvider()
    if normalized == "proxy":
        from pdf2ppt.providers.proxy import ProxyProvider

        return ProxyProvider()
    raise ProviderError(f"Unsupported provider: {name}")


__all__ = ["LayoutProvider", "MockProvider", "ProviderError", "get_provider"]
