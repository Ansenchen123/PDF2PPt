import cv2
import numpy as np
from typing import List, Dict, Any

def remove_text_from_image(image_path: str, text_blocks: List[Dict[str, Any]], output_path: str):
    """
    Removes text from the image using inpainting based on bounding boxes.
    
    Args:
        image_path: Path to the source image.
        text_blocks: List of text blocks with 'box_2d' [ymin, xmin, ymax, xmax] (0-1000).
        output_path: Path to save the clean image.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image {image_path}")
        return

    h, w, _ = img.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    
    for block in text_blocks:
        box = block.get('box_2d')
        if not box:
            continue
            
        ymin, xmin, ymax, xmax = box
        
        # Convert normalized 0-1000 coordinates to pixel coordinates
        y1 = int(ymin / 1000 * h)
        x1 = int(xmin / 1000 * w)
        y2 = int(ymax / 1000 * h)
        x2 = int(xmax / 1000 * w)
        
        # Add some padding to the box to ensure full coverage
        pad = 5
        y1 = max(0, y1 - pad)
        x1 = max(0, x1 - pad)
        y2 = min(h, y2 + pad)
        x2 = min(w, x2 + pad)
        
        # Draw white rectangle on the mask
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
    
    # Dilate mask slightly to handle edge artifacts
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Inpaint
    # CV_INPAINT_TELEA or CV_INPAINT_NS
    clean_img = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    
    cv2.imwrite(output_path, clean_img)
    print(f"Saved clean background: {output_path}")
