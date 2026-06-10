# PDF2PPt

PDF2PPt converts slide-oriented PDF files into editable PowerPoint decks using PDF rasterization, Gemini OCR, OpenCV inpainting, and `python-pptx`.

## Features

- Converts selected PDF page ranges into PowerPoint slide decks.
- Provides both a Tkinter desktop interface and a command-line workflow.
- Uses Gemini to extract text and bounding boxes from rendered page images.
- Removes detected source text from slide images before rebuilding editable text layers.
- Saves partial output when at least one page is processed before a later page fails.
- Can keep temporary page images for debugging through the CLI.

## Requirements

- Python 3.10 or newer.
- A Gemini API key available as `GEMINI_API_KEY`.
- Python packages listed in `requirements.txt`: `google-generativeai`, `opencv-python`, `Pillow`, `PyMuPDF`, `python-dotenv`, and `python-pptx`.
- On Linux, a Tkinter-capable Python installation is required for the desktop GUI.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to a local .env file.
4. Set the Gemini API key:

```env
GEMINI_API_KEY=your-real-key
```

The GUI can also create or update the local environment file when the API key is entered and saved from the application.

## Usage

Run the desktop application:

```bash
python gui.py
```

Run the command-line converter:

```bash
python main.py input.pdf --output output.pptx --start-page 1 --end-page 5
```

CLI options:

- `--output`: output PowerPoint path. Defaults to output.pptx.
- `--start-page`: first page to process, using 1-based numbering. Defaults to `1`.
- `--end-page`: last page to process, using 1-based numbering.
- `--api-key`: Gemini API key override. When omitted, the converter uses `GEMINI_API_KEY` from the local environment file.
- `--keep-temp`: keeps generated page images and cleaned images beside the output file for debugging.

## Project Structure

- `main.py`: command-line entry point and end-to-end conversion pipeline.
- `gui.py`: Tkinter desktop interface for selecting a PDF, output folder, API key, and page range.
- `pdf_utils.py`: PDF page counting and page-to-image rendering with PyMuPDF.
- `ocr_service.py`: Gemini configuration, OCR prompting, and bounding-box parsing.
- `image_processor.py`: OpenCV-based text mask creation and inpainting.
- `ppt_generator.py`: PowerPoint slide generation with background images and editable text boxes.
- `requirements.txt`: Python runtime dependencies.
- `.env.example`: sample environment file containing `GEMINI_API_KEY`.
- `pdf2pptsoft.spec`: PyInstaller specification for packaging the GUI application.

## 摘要

PDF2PPt 是一個將簡報型 PDF 轉成可編輯 PowerPoint 檔案的 Python 工具。
主要流程會先把 PDF 頁面轉成圖片，再使用 Gemini 擷取文字與位置資訊。
程式會用 OpenCV 嘗試移除原圖片上的文字，接著用 `python-pptx` 重建投影片。
使用前需安裝 `requirements.txt` 內的套件，並在本機環境檔設定 `GEMINI_API_KEY`。
桌面版可執行 `python gui.py`，命令列版可執行 `python main.py input.pdf --output output.pptx`。
若轉換中途發生 OCR 或 API 錯誤，只要已有成功處理的頁面，程式仍會先輸出部分結果。
