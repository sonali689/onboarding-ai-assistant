import os
import re
import sys
import unicodedata
from PIL import Image
from pptx import Presentation
from config import SLIDE_IMAGE_FOLDER, SLIDE_EXPORT_DPI


def sanitize_for_filename(name: str) -> str:
    """Make a Japanese/mixed string safe to use as a filename."""
    name = name.replace("・", "_")
    name = name.replace("＆", "and")
    name = name.replace("　", "_")
    name = name.replace("·", "_")
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^\w\-_.]", "_", name)
    return name.strip("_")


def export_slides_with_powerpoint(
    pptx_path: str,
    output_folder: str,
    dpi: int,
) -> list[tuple[int, str]]:
    """
    Use PowerPoint COM (Windows only) to export slides as PNG images.
    Requires Microsoft PowerPoint to be installed.
    """
    import comtypes.client

    pptx_basename = os.path.splitext(os.path.basename(pptx_path))[0]
    safe_basename = sanitize_for_filename(pptx_basename)
    abs_pptx_path = os.path.abspath(pptx_path)
    abs_output_folder = os.path.abspath(output_folder)

    results = []

    powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
    powerpoint.Visible = 1

    try:
        presentation = powerpoint.Presentations.Open(
            abs_pptx_path,
            ReadOnly=True,
            Untitled=False,
            WithWindow=False,
        )

        for i, slide in enumerate(presentation.Slides, start=1):
            image_filename = f"{safe_basename}_slide_{i:03d}.png"
            image_path = os.path.join(abs_output_folder, image_filename)

            # Export slide as PNG
            slide.Export(image_path, "PNG")
            results.append((i, image_path))

        presentation.Close()

    finally:
        powerpoint.Quit()

    return results


def export_slides_as_placeholder(
    pptx_path: str,
    output_folder: str,
    dpi: int,
) -> list[tuple[int, str]]:
    """
    Fallback: create blank white images when PowerPoint is not available.
    LLaVA will produce empty descriptions but pipeline won't crash.
    """
    pptx_basename = os.path.splitext(os.path.basename(pptx_path))[0]
    safe_basename = sanitize_for_filename(pptx_basename)

    prs = Presentation(pptx_path)
    width_px  = int(prs.slide_width  / 914400 * dpi)
    height_px = int(prs.slide_height / 914400 * dpi)

    results = []
    for slide_num in range(1, len(prs.slides) + 1):
        image_filename = f"{safe_basename}_slide_{slide_num:03d}.png"
        image_path = os.path.join(output_folder, image_filename)
        img = Image.new("RGB", (width_px, height_px), color=(255, 255, 255))
        img.save(image_path, format="PNG")
        results.append((slide_num, image_path))

    return results


def export_slides_as_images(
    pptx_path: str,
    output_folder: str = SLIDE_IMAGE_FOLDER,
    dpi: int = SLIDE_EXPORT_DPI,
) -> list[tuple[int, str]]:
    """
    Main export function.
    Tries PowerPoint COM first (Windows), falls back to placeholder images.
    """
    os.makedirs(output_folder, exist_ok=True)

    if sys.platform == "win32":
        try:
            import comtypes
            return export_slides_with_powerpoint(pptx_path, output_folder, dpi)
        except Exception as e:
            print(f"  ⚠️  PowerPoint COM failed ({e}), using placeholder images.")
            return export_slides_as_placeholder(pptx_path, output_folder, dpi)
    else:
        # Linux/Mac — placeholder for now
        # On Linux GPU machine we'll use LibreOffice
        return export_slides_as_placeholder(pptx_path, output_folder, dpi)