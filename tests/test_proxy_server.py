from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from server.app import create_app


def _make_image(path: Path) -> None:
    Image.new("RGB", (320, 180), "#ffffff").save(path)


def test_providers_endpoint_requires_bearer_token():
    app = create_app(proxy_token="secret")
    client = TestClient(app)

    response = client.get("/v1/providers")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_providers_endpoint_returns_supported_providers():
    app = create_app(proxy_token="secret")
    client = TestClient(app)

    response = client.get("/v1/providers", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    assert "openai" in response.json()["providers"]
    assert "mock" in response.json()["providers"]


def test_extract_layout_with_mock_provider(tmp_path: Path):
    image = tmp_path / "page.png"
    _make_image(image)
    app = create_app(proxy_token="secret")
    client = TestClient(app)

    with image.open("rb") as handle:
        response = client.post(
            "/v1/extract-layout",
            headers={"Authorization": "Bearer secret"},
            data={"provider": "mock", "model": "mock-layout-v1", "pageNumber": "3"},
            files={"file": ("page.png", handle, "image/png")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["page_number"] == 3
    assert body["text_blocks"]


def test_rate_limit_returns_structured_error():
    app = create_app(proxy_token="secret", rate_limit_per_minute=1)
    client = TestClient(app)
    headers = {"Authorization": "Bearer secret"}

    assert client.get("/v1/providers", headers=headers).status_code == 200
    response = client.get("/v1/providers", headers=headers)

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"


def test_usage_endpoint_counts_requests():
    app = create_app(proxy_token="secret")
    client = TestClient(app)
    headers = {"Authorization": "Bearer secret"}

    client.get("/v1/providers", headers=headers)
    response = client.get("/v1/usage", headers=headers)

    assert response.status_code == 200
    assert response.json()["requests"] >= 2
