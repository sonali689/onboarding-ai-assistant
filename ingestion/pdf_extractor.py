import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fitz  # PyMuPDF
from PIL import Image
import io
from config import SLIDE_IMAGE_FOLDER, SLIDE_EXPORT_DPI
from ingestion.slide_exporter import sanitize_for_filename


def scan_pdf_files(root_folder: str) -> list[str]:
    """Recursively find all PDF files across all subfolders."""
    pdf_files = []
    for root, dirs, files in os.walk(root_folder):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))
    print(f"Found {len(pdf_files)} PDF files under {root_folder}")
    return sorted(pdf_files)


def extract_pdf_slide_data(pdf_path: str) -> list[dict]:
    """
    Extract text from each page of a PDF.
    Returns list of dicts in same format as pptx_extractor
    so the rest of the pipeline works identically.
    """
    slides_data = []
    filename  = os.path.basename(pdf_path)
    subfolder = os.path.basename(os.path.dirname(pdf_path))

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"   Could not open {filename}: {e}")
        return []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Extract text — preserves Japanese characters natively
        text = page.get_text("text").strip()

        # First line as title if available
        lines = text.split("\n")
        slide_title = lines[0].strip() if lines else ""

        slides_data.append({
            "slide_number": page_num + 1,
            "slide_title":  slide_title,
            "text":         text,
            "notes":        "",        # PDFs have no speaker notes
            "filename":     filename,
            "subfolder":    subfolder,
        })

    doc.close()
    return slides_data


def export_pdf_pages_as_images(
    pdf_path: str,
    output_folder: str = SLIDE_IMAGE_FOLDER,
    dpi: int = SLIDE_EXPORT_DPI,
) -> list[tuple[int, str]]:
    """
    Export each PDF page as a PNG image for LLaVA.
    Uses PyMuPDF's built-in renderer — no PowerPoint needed.
    """
    os.makedirs(output_folder, exist_ok=True)

    pdf_basename  = os.path.splitext(os.path.basename(pdf_path))[0]
    safe_basename = sanitize_for_filename(pdf_basename)

    results = []

    try:
        doc = fitz.open(pdf_path)
        mat = fitz.Matrix(dpi / 72, dpi / 72)  # scale to target DPI

        for page_num in range(len(doc)):
            page          = doc[page_num]
            pix           = page.get_pixmap(matrix=mat)
            image_filename = f"{safe_basename}_page_{page_num + 1:03d}.png"
            image_path    = os.path.join(output_folder, image_filename)

            pix.save(image_path)
            results.append((page_num + 1, image_path))

        doc.close()

    except Exception as e:
        print(f"   Could not export pages from {pdf_path}: {e}")

    return results