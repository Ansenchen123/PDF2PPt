# PDF2PPt Studio

PDF2PPt Studio converts slide-oriented PDFs into editable PowerPoint decks. The commercial rebuild uses a structured layout pipeline instead of sending bounding boxes directly to PowerPoint: every page is rendered, text/layout is normalized into a validated intermediate representation, backgrounds are cleaned with inspectable masks, and PPTX output is generated from that verified layout model.

## What changed

- Native Windows-first desktop app entrypoint powered by PySide6 / Qt Quick.
- Provider-neutral multimodal extraction layer for OpenAI, Gemini, Claude, Mistral, a managed proxy, and a deterministic mock provider.
- Pydantic layout IR for `TextBlock`, `TextStyle`, `SlideLayout`, `ProviderResult`, and quality reports.
- Improved background cleanup with text-shaped masks, inpainted clean images, and debug overlays.
- PPTX generation uses real page aspect ratio, estimated font size, color, weight, alignment, and line spacing.
- FastAPI managed proxy with bearer auth, rate limiting, request counting, and structured errors.
- Test suite covering schema validation, PDF rendering, PPTX export, provider payloads, proxy behavior, CLI, desktop contracts, and visual quality primitives.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set one or more provider keys in `.env`, or store keys from the desktop app:

```env
OPENAI_API_KEY=...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
MISTRAL_API_KEY=...
```

## Desktop App

```powershell
python gui.py
```

The desktop app supports:

- PDF selection, output path selection, and page range control.
- BYOK mode for local provider keys.
- Managed proxy mode for server-side keys.
- Provider switching between Gemini, OpenAI, Claude, Mistral, and mock.
- Background progress and completion status.

## CLI

```powershell
python main.py PDFs\Financial_Analysis_and_Value.pdf --output output.pptx --provider gemini --start-page 1 --end-page 3
```

Useful options:

- `--provider gemini|openai|anthropic|mistral|mock`
- `--model`: provider model override
- `--auth-mode byok|proxy`
- `--api-key`: one-off local key override
- `--proxy-url` and `--proxy-token`
- `--keep-temp`: keep rendered pages, clean backgrounds, masks, and overlays

## Managed Proxy

Run the proxy locally:

```powershell
uvicorn server.app:app --host 127.0.0.1 --port 8000
```

Required server-side environment:

```env
PDF2PPT_PROXY_TOKEN=change-me
PDF2PPT_RATE_LIMIT_PER_MINUTE=60
```

Endpoints:

- `GET /v1/providers`
- `GET /v1/usage`
- `POST /v1/extract-layout`

All proxy endpoints require `Authorization: Bearer <token>` and return structured errors:

```json
{"error":{"code":"UNAUTHORIZED","message":"Bearer token is required"}}
```

## Tests

Run the default suite:

```powershell
python -m pytest -q
```

Run paid live provider smoke tests only when explicitly enabled:

```powershell
$env:PDF2PPT_LIVE_TESTS="1"
python -m pytest tests/test_live_providers.py -q
```

The live smoke currently exercises Gemini when `GEMINI_API_KEY` is configured.

## Packaging

Build the Windows desktop executable:

```powershell
pyinstaller pdf2pptsoft.spec
```

The spec bundles the QML workspace under `pdf2ppt/desktop/ui`.

## Project Structure

- `pdf2ppt/models.py`: validated layout IR and conversion result types.
- `pdf2ppt/providers/`: OpenAI, Gemini, Claude, Mistral, proxy, and mock adapters.
- `pdf2ppt/pdf.py`: PDF page counting, rendering, and native text extraction.
- `pdf2ppt/background.py`: text-shaped mask generation and inpainting.
- `pdf2ppt/pptx_export.py`: PPTX generation from `SlideLayout`.
- `pdf2ppt/pipeline.py`: end-to-end conversion orchestration.
- `pdf2ppt/desktop/`: PySide6/Qt Quick desktop app.
- `server/app.py`: managed provider proxy.
- `tests/`: unit, integration, proxy, CLI, desktop contract, quality, and opt-in live tests.
