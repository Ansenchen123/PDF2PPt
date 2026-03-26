# PDF2PPt

`PDF2PPt` converts slide-style PDF files into editable PowerPoint decks by combining:

- PDF rasterization with PyMuPDF
- OCR + layout extraction with Gemini
- background cleanup with OpenCV inpainting
- slide regeneration with `python-pptx`

The project includes both a command-line entry point and a Tkinter desktop GUI.

## Why This Project Matters

This is a practical AI automation project aimed at a real workflow problem: turning static presentation PDFs into editable slides quickly enough for business, consulting, and academic reuse.

It is a strong portfolio piece because it demonstrates:

- desktop application development with Python
- document processing and OCR workflows
- integration with external AI services
- pipeline design for partially recoverable long-running jobs

## Features

- Select a PDF and convert only a chosen page range
- Save Gemini API credentials locally via `.env`
- Remove source text from rendered slide images before rebuilding slides
- Produce partial output even if a later OCR page fails
- Use either a GUI (`gui.py`) or CLI (`main.py`)

## Project Structure

- `main.py`: CLI entry point and end-to-end conversion pipeline
- `gui.py`: Tkinter desktop interface
- `pdf_utils.py`: PDF page counting and rasterization
- `ocr_service.py`: Gemini OCR extraction and bounding box parsing
- `image_processor.py`: text removal via inpainting
- `ppt_generator.py`: PowerPoint generation

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set your Gemini API key:

```env
GEMINI_API_KEY=your-real-key
```

## Usage

Run the desktop app:

```bash
python gui.py
```

Run the CLI:

```bash
python main.py input.pdf --output output.pptx --start-page 1 --end-page 5
```

Optional CLI flags:

- `--api-key`: override the API key from the command line
- `--keep-temp`: keep temporary page images for debugging

## Notes

- Generated `.pptx` outputs and packaged executables are intentionally ignored by git.
- Temporary working folders are cleaned automatically unless `--keep-temp` is enabled.
- Best results come from PDFs that already resemble presentation slides rather than dense scanned documents.

## Portfolio Positioning

If you use this in job applications, frame it as:

"An AI-assisted document transformation tool that reconstructs editable PowerPoint slides from PDF source material using OCR, layout extraction, and image cleanup."
