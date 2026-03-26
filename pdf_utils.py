import fitz  # pymupdf
import os
from typing import List

def get_page_count(pdf_path: str) -> int:
    """Returns the total number of pages in the PDF."""
    doc = fitz.open(pdf_path)
    count = doc.page_count
    doc.close()
    return count

def pdf_to_images(pdf_path: str, output_folder: str = "output_images", zoom: int = 2, start_page: int = 1, end_page: int = None) -> List[str]:
    """
    Renders pages of the PDF to images.
    
    Args:
        pdf_path: Path to the source PDF file.
        output_folder: Folder to save the generated images.
        zoom: Zoom factor for higher resolution.
        start_page: First page to process (1-based).
        end_page: Last page to process (1-based, inclusive). If None, process until the end.
        
    Returns:
        List of paths to the generated image files.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    doc = fitz.open(pdf_path)
    if end_page is None or end_page > doc.page_count:
        end_page = doc.page_count
    
    # helper for 0-based indexing
    start_idx = max(0, start_page - 1)
    end_idx = min(doc.page_count, end_page)
    
    image_paths = []
    
    mat = fitz.Matrix(zoom, zoom)
    
    print(f"Processing PDF: {pdf_path}, Pages: {start_page} to {end_page} (Total: {doc.page_count})")
    
    for page_num in range(start_idx, end_idx):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat)
        
        image_filename = f"page_{page_num + 1}.png"
        image_path = os.path.join(output_folder, image_filename)
        
        pix.save(image_path)
        image_paths.append(image_path)
        print(f"Saved: {image_path}")
        
    doc.close()
    return image_paths

def get_pdf_dims(pdf_path: str) -> tuple:
    """Returns the dimensions of the first page (width, height) in points."""
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    rect = page.rect
    doc.close()
    return rect.width, rect.height
