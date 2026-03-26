import argparse
import os
import shutil
import tempfile
from pathlib import Path

from pdf_utils import pdf_to_images
from ocr_service import extract_text_and_coords, configure_gemini
from image_processor import remove_text_from_image
from ppt_generator import create_ppt

def _build_temp_dirs(base_dir: Path | None = None) -> tuple[Path, Path, Path]:
    root = Path(tempfile.mkdtemp(prefix="pdf2ppt_", dir=base_dir))
    temp_img_folder = root / "temp_images"
    temp_clean_folder = root / "temp_clean_images"
    temp_img_folder.mkdir(parents=True, exist_ok=True)
    temp_clean_folder.mkdir(parents=True, exist_ok=True)
    return root, temp_img_folder, temp_clean_folder


def convert_pdf_to_ppt(
    pdf_path: str,
    output_ppt: str,
    api_key: str | None = None,
    start_page: int = 1,
    end_page: int | None = None,
    callback=None,
    keep_temp: bool = False,
):
    """
    Main Logic to convert PDF to PPT.
    
    Args:
        pdf_path: Input PDF.
        output_ppt: Output PPTX.
        api_key: Optional API key to use/configure.
        start_page: Start page (1-based).
        end_page: End page (1-based).
        callback: Function to call with status updates (cur_page, total_pages, message).
    """
    pdf_path = Path(pdf_path).expanduser().resolve()
    output_ppt = Path(output_ppt).expanduser().resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    if start_page < 1:
        raise ValueError("start_page must be 1 or greater.")
    if end_page is not None and end_page < start_page:
        raise ValueError("end_page must be greater than or equal to start_page.")

    output_ppt.parent.mkdir(parents=True, exist_ok=True)
        
    # Check if output is writable (rudimentary check)
    if output_ppt.exists():
        try:
            with output_ppt.open("ab"):
                pass
        except PermissionError:
            raise PermissionError(f"Output file {output_ppt} is open or locked. Please close it.")

    # Configure API
    if api_key:
        configure_gemini(api_key)

    msg = "Step 1: Converting PDF to Images..."
    print(msg)
    if callback: callback(0, 0, msg)
    
    temp_root, temp_img_folder, temp_clean_folder = _build_temp_dirs(output_ppt.parent)

    try:
        image_paths = pdf_to_images(
            str(pdf_path),
            output_folder=str(temp_img_folder),
            start_page=start_page,
            end_page=end_page,
        )

        total_pages = len(image_paths)
        slides_data = []

        error_occurred = None
        current_page_num = start_page

        for i, img_path in enumerate(image_paths):
            current_page_num = start_page + i
            msg = f"Processing page {current_page_num}..."
            print(msg)
            if callback:
                callback(i + 1, total_pages, msg)

            try:
                text_blocks = extract_text_and_coords(img_path)

                clean_img_filename = f"clean_page_{current_page_num}.png"
                clean_img_path = temp_clean_folder / clean_img_filename
                remove_text_from_image(img_path, text_blocks, str(clean_img_path))

                slides_data.append(
                    {
                        "clean_image_path": str(clean_img_path),
                        "text_blocks": text_blocks,
                    }
                )
            except Exception as exc:
                print(f"Error processing page {current_page_num}: {exc}")
                error_occurred = exc
                if callback:
                    callback(i + 1, total_pages, f"Stopping early due to error: {exc}")
                break

        if not slides_data:
            if error_occurred:
                raise error_occurred
            raise RuntimeError("No slides were processed successfully.")

        msg = f"Generating PowerPoint ({len(slides_data)} slides)..."
        if error_occurred:
            msg += " (partial output)"

        print(msg)
        if callback:
            callback(len(slides_data), total_pages, msg)

        create_ppt(slides_data, str(output_ppt))

        print("Done!")

        if error_occurred:
            raise RuntimeError(
                f"Stopped on page {current_page_num}. Partial content was saved to {output_ppt}. "
                f"Original error: {error_occurred}"
            )
    finally:
        if not keep_temp and temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Convert PDF to PPTX using Gemini OCR and Inpainting.")
    parser.add_argument("pdf_path", help="Path to the input PDF file.")
    parser.add_argument("--output", default="output.pptx", help="Path to the output PPTX file.")
    parser.add_argument("--start-page", type=int, default=1, help="First page to process (1-based).")
    parser.add_argument("--end-page", type=int, help="Last page to process (1-based, inclusive).")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary page images for debugging.")
    parser.add_argument("--api-key", help="Gemini API key. Defaults to GEMINI_API_KEY from .env.")
    
    args = parser.parse_args()
    
    try:
        convert_pdf_to_ppt(
            args.pdf_path,
            args.output,
            api_key=args.api_key,
            start_page=args.start_page,
            end_page=args.end_page,
            keep_temp=args.keep_temp,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
