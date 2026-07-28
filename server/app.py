from __future__ import annotations

import os
import secrets
import tempfile
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from PIL import Image

from pdf2ppt.models import ProviderOptions
from pdf2ppt.providers import get_provider
from pdf2ppt.providers.base import ProviderError


SUPPORTED_PROVIDERS = ["openai", "gemini", "anthropic", "mistral", "mock"]
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
security = HTTPBearer(auto_error=False)


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass
class ProxyState:
    proxy_token: str
    rate_limit_per_minute: int = 60
    request_times: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))
    usage: dict[str, int] = field(default_factory=lambda: defaultdict(int))


def create_app(
    *,
    proxy_token: str | None = None,
    rate_limit_per_minute: int | None = None,
) -> FastAPI:
    state = ProxyState(
        proxy_token=proxy_token or os.getenv("PDF2PPT_PROXY_TOKEN", ""),
        rate_limit_per_minute=rate_limit_per_minute
        if rate_limit_per_minute is not None
        else int(os.getenv("PDF2PPT_RATE_LIMIT_PER_MINUTE", "60")),
    )
    app = FastAPI(title="PDF2PPt Managed Proxy", version="0.1.0")
    app.state.proxy_state = state

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    @app.exception_handler(APIError)
    async def api_error_handler(_request: Request, exc: APIError):
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(ProviderError)
    async def provider_error_handler(_request: Request, exc: ProviderError):
        return _error_response(502, "PROVIDER_ERROR", str(exc))

    @app.get("/v1/providers")
    async def providers(_token: Annotated[str, Depends(_authenticate)]):
        return {"providers": SUPPORTED_PROVIDERS}

    @app.get("/v1/usage")
    async def usage(token: Annotated[str, Depends(_authenticate)], request: Request):
        proxy_state: ProxyState = request.app.state.proxy_state
        return {"requests": proxy_state.usage[token]}

    @app.post("/v1/extract-layout")
    async def extract_layout(
        request: Request,
        token: Annotated[str, Depends(_authenticate)],
        file: Annotated[UploadFile, File()],
        provider: Annotated[str, Form()],
        model: Annotated[str, Form()] = "",
        pageNumber: Annotated[int, Form()] = 1,
    ):
        _ = token
        normalized_provider = provider.lower()
        if normalized_provider not in SUPPORTED_PROVIDERS:
            raise APIError(422, "VALIDATION_ERROR", "Unsupported provider")
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise APIError(415, "UNSUPPORTED_MEDIA_TYPE", "Only PNG, JPEG, and WebP images are accepted")

        suffix = Path(file.filename or "page.png").suffix or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)
        try:
            with Image.open(tmp_path) as image:
                image_size = image.size
            adapter = get_provider(normalized_provider)
            result = adapter.extract_layout(
                image_path=tmp_path,
                page_number=pageNumber,
                image_size=image_size,
                options=ProviderOptions(provider=normalized_provider, model=model or None),
            )
            return JSONResponse(result.model_dump(mode="json"))
        finally:
            tmp_path.unlink(missing_ok=True)

    return app


def _authenticate(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    proxy_state: ProxyState = request.app.state.proxy_state
    if not proxy_state.proxy_token:
        raise APIError(500, "SERVER_NOT_CONFIGURED", "Proxy token is not configured")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise APIError(401, "UNAUTHORIZED", "Bearer token is required")
    token = credentials.credentials
    if not secrets.compare_digest(token, proxy_state.proxy_token):
        raise APIError(401, "UNAUTHORIZED", "Bearer token is invalid")
    _enforce_rate_limit(proxy_state, token)
    proxy_state.usage[token] += 1
    return token


def _enforce_rate_limit(proxy_state: ProxyState, token: str) -> None:
    now = time.monotonic()
    window = 60.0
    bucket = proxy_state.request_times[token]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= proxy_state.rate_limit_per_minute:
        raise APIError(429, "RATE_LIMITED", "Rate limit exceeded")
    bucket.append(now)


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


app = create_app()
