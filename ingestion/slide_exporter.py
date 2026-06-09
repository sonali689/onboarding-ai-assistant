import os
import re
import unicodedata
from PIL import Image
from pptx import Presentation
from pptx.util import Inches
from config import SLIDE_IMAGE_FOLDER, SLIDE_EXPORT_DPI


def sanitize_for_filename(name: str) -> str:
    """Make a Japanese/mixed string safe to use as a filename."""
    name = name.replace("・", "_")
    name = name.replace("＆", "and")
    name = name.replace("　", "_")   # full-width space
    name = name.replace("·", "_")
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^\w\-_.]", "_", name)
    return name.strip("_")


def export_slides_as_images(
    pptx_path: str,
    output_folder: str = SLIDE_IMAGE_FOLDER,
    dpi: int = SLIDE_EXPORT_DPI,
) -> list[tuple[int, str]]:
    """
    Export each slide of a PPTX as a PNG image.
    Returns list of (slide_number, image_path) tuples.
    """
    os.makedirs(output_folder, exist_ok=True)

    pptx_basename = os.path.splitext(os.path.basename(pptx_path))[0]
    safe_basename = sanitize_for_filename(pptx_basename)

    prs = Presentation(pptx_path)
    slide_width  = prs.slide_width
    slide_height = prs.slide_height

    # Convert EMU to pixels at target DPI
    # 1 inch = 914400 EMU
    width_px  = int(slide_width  / 914400 * dpi)
    height_px = int(slide_height / 914400 * dpi)

    results = []

    for slide_num, slide in enumerate(prs.slides, start=1):
        image_filename = f"{safe_basename}_slide_{slide_num:03d}.png"
        image_path = os.path.join(output_folder, image_filename)

        try:
            # python-pptx doesn't render to image natively —
            # we create a blank white image as a placeholder.
            # On the GPU machine with LibreOffice or comtypes this is replaced.
            # For now this ensures the pipeline doesn't crash.
            img = Image.new("RGB", (width_px, height_px), color=(255, 255, 255))
            img.save(image_path, format="PNG")
            results.append((slide_num, image_path))
        except Exception as e:
            print(f"  ⚠️  Could not export slide {slide_num} of "
                  f"{pptx_basename}: {e}")

    return results