# PDF2PPt Studio

Turn slide PDFs into PowerPoint files with editable text.

Each rendered page becomes the slide background after detected text is removed.
Native PDF text is rebuilt as PowerPoint text boxes. Pages without embedded text
are sent to the selected layout provider.

Requires Python 3.10 or later. The commands below use PowerShell on Windows.

## Quick start

```powershell
git clone https://github.com/Ansenchen123/PDF2PPt.git
cd PDF2PPt
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder for the provider you plan to use:

```env
OPENAI_API_KEY=...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
MISTRAL_API_KEY=...
```

## Desktop

```powershell
python gui.py
```

Choose a PDF, output path, page range, provider, and authentication mode. Keys
saved through the desktop app are stored in the operating system keyring.

## Command line

```powershell
python main.py slides.pdf --output slides.pptx --provider gemini
```

Process a page range:

```powershell
python main.py slides.pdf --output sample.pptx --provider openai --start-page 2 --end-page 6
```

Run an offline pipeline check with the mock provider:

```powershell
python main.py slides.pdf --output mock-output.pptx --provider mock
```

| Option | Purpose |
| --- | --- |
| `--provider` | `gemini`, `openai`, `anthropic`, `mistral`, or `mock` |
| `--model` | Override the provider's default model |
| `--start-page`, `--end-page` | Select a 1-based inclusive page range |
| `--auth-mode` | Read a local key with `byok`, or route through `proxy` |
| `--api-key` | Use a key for the current command |
| `--proxy-url`, `--proxy-token` | Connect to the provider proxy |
| `--keep-temp` | Keep the `pdf2ppt_*` work directory beside the output file |

## Conversion pipeline

1. Render each PDF page at its original aspect ratio.
2. Read text and style data embedded in the PDF.
3. Send image-only pages to the selected provider for layout extraction.
4. Validate coordinates, text styles, and provider responses with Pydantic.
5. Remove text from the page image with generated masks and inpainting.
6. Write the cleaned background and editable text boxes to the PPTX file.

## Providers

| Provider | CLI value | Environment variable |
| --- | --- | --- |
| Google Gemini | `gemini` | `GEMINI_API_KEY` |
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Anthropic Claude | `anthropic` | `ANTHROPIC_API_KEY` |
| Mistral | `mistral` | `MISTRAL_API_KEY` |
| Mock (offline) | `mock` | None |

## Provider proxy

Set the provider API key on the server, then configure the proxy:

```env
GEMINI_API_KEY=...
PDF2PPT_PROXY_TOKEN=change-me
PDF2PPT_RATE_LIMIT_PER_MINUTE=60
```

```powershell
python -m uvicorn server.app:app --env-file .env --host 127.0.0.1 --port 8000
```

Point the CLI at the proxy:

```powershell
python main.py slides.pdf `
  --output slides.pptx `
  --provider gemini `
  --auth-mode proxy `
  --proxy-url http://127.0.0.1:8000 `
  --proxy-token change-me
```

HTTP endpoints:

- `GET /v1/providers`
- `GET /v1/usage`
- `POST /v1/extract-layout`

Requests use `Authorization: Bearer <token>`. Authentication and provider errors
use this JSON shape:

```json
{"error":{"code":"UNAUTHORIZED","message":"Bearer token is required"}}
```

## Tests

```powershell
python -m pytest -q
```

The live test calls Gemini and may consume API quota. It runs only when
`PDF2PPT_LIVE_TESTS=1` and `GEMINI_API_KEY` are both set:

```powershell
$env:PDF2PPT_LIVE_TESTS="1"
python -m pytest tests/test_live_providers.py -q
```

## Windows build

```powershell
pyinstaller pdf2pptsoft.spec
```

The PyInstaller spec includes the QML files under `pdf2ppt/desktop/ui`.

## Repository layout

| Path | Contents |
| --- | --- |
| `pdf2ppt/models.py` | Layout models and conversion result types |
| `pdf2ppt/providers/` | Provider and proxy adapters |
| `pdf2ppt/pdf.py` | PDF rendering and native text extraction |
| `pdf2ppt/background.py` | Text masks, inpainting, and debug overlays |
| `pdf2ppt/pptx_export.py` | PowerPoint generation |
| `pdf2ppt/pipeline.py` | Conversion orchestration |
| `pdf2ppt/desktop/` | PySide6 and Qt Quick desktop UI |
| `server/app.py` | FastAPI provider proxy |
| `tests/` | Unit, integration, desktop, proxy, and live-provider tests |

## License

[MIT](LICENSE)
