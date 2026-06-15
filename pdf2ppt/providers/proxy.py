from __future__ import annotations

from pathlib import Path

import requests

from pdf2ppt.config import get_proxy_config
from pdf2ppt.models import ProviderOptions, ProviderResult
from pdf2ppt.providers.base import LayoutProvider, ProviderError


class ProxyProvider(LayoutProvider):
    name = "proxy"

    def extract_layout(
        self,
        image_path: Path,
        page_number: int,
        image_size: tuple[int, int],
        options: ProviderOptions,
    ) -> ProviderResult:
        _ = image_size
        proxy_url = options.proxy_url
        proxy_token = options.proxy_token
        if not proxy_url or not proxy_token:
            env_url, env_token = get_proxy_config()
            proxy_url = proxy_url or env_url
            proxy_token = proxy_token or env_token
        if not proxy_url or not proxy_token:
            raise ProviderError("PDF2PPT proxy URL/token are not configured")

        with image_path.open("rb") as handle:
            response = requests.post(
                f"{proxy_url.rstrip('/')}/v1/extract-layout",
                headers={"Authorization": f"Bearer {proxy_token}"},
                data={"provider": options.provider, "model": options.model or ""},
                files={"file": (image_path.name, handle, "image/png")},
                timeout=options.timeout_seconds,
            )
        if response.status_code >= 400:
            raise ProviderError(f"Proxy returned HTTP {response.status_code}")
        return ProviderResult.model_validate(response.json())
