"""
PDF utility functions for the py-reform library.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import PIL.Image

logger = logging.getLogger(__name__)

try:
    import pypdfium2 as pdfium

    PDFIUM_AVAILABLE = True
except ImportError:
    PDFIUM_AVAILABLE = False


def pdf_to_images(
    pdf_path: Union[str, Path],
    pages: Optional[List[int]] = None,
    dpi: int = 300,
) -> List[PIL.Image.Image]:
    """
    Extract pages from a PDF as PIL Images.

    Args:
        pdf_path: Path to the PDF file
        pages: List of page indices to extract (0-indexed)
        dpi: Resolution for the extracted images

    Returns:
        List of PIL Images
    """
    if not PDFIUM_AVAILABLE:
        raise ImportError(
            "PyPDFium2 is required for PDF processing. "
            "Install it with 'pip install pypdfium2'."
        )

    # Convert to Path if string
    if isinstance(pdf_path, str):
        pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    logger.info(f"Extracting images from PDF: {pdf_path}")

    # Load the PDF
    pdf = pdfium.PdfDocument(pdf_path)

    try:
        # Determine which pages to process
        if pages is None:
            pages = list(range(len(pdf)))

        # Extract images
        images = []
        for page_idx in pages:
            if page_idx < 0 or page_idx >= len(pdf):
                logger.warning(f"Page index {page_idx} out of range, skipping")
                continue

            # Render the page to a PIL Image
            page = pdf[page_idx]
            try:
                bitmap = page.render(
                    scale=dpi / 72.0,  # Convert DPI to scale factor
                    rotation=0,
                )
                image = bitmap.to_pil()
                images.append(image)
            finally:
                # Explicitly close the page to prevent memory leaks
                page.close()

        return images
    finally:
        # Ensure the PDF is closed properly
        pdf.close()


def save_pdf(
    images: List[PIL.Image.Image],
    output_path: Union[str, Path],
) -> Path:
    """
    Save a list of PIL Images as a PDF.

    Args:
        images: List of PIL Images to save
        output_path: Path where the PDF will be saved

    Returns:
        Path to the saved PDF file
    """
    if not images:
        raise ValueError("No images provided to save as PDF")

    # Convert to Path if string
    if isinstance(output_path, str):
        output_path = Path(output_path)

    # Create parent directories if they don't exist
    output_path.parent.mkdir(exist_ok=True, parents=True)

    # Save the first image and append the rest
    first_image = images[0]
    remaining_images = images[1:] if len(images) > 1 else []

    logger.info(f"Saving {len(images)} images as PDF: {output_path}")

    # Convert to RGB if needed (PDF doesn't support RGBA)
    if first_image.mode == "RGBA":
        first_image = first_image.convert("RGB")

    # Convert remaining images to RGB if needed
    rgb_remaining = []
    for img in remaining_images:
        if img.mode == "RGBA":
            rgb_remaining.append(img.convert("RGB"))
        else:
            rgb_remaining.append(img)

    # Save as PDF
    first_image.save(
        output_path, "PDF", resolution=100.0, save_all=True, append_images=rgb_remaining
    )

    return output_path


def image_to_pdf(
    images: List[PIL.Image.Image],
    output_path: Union[str, Path],
    compression: str = "jpeg",
    quality: int = 95,
) -> Path:
    """
    Save images as a PDF with custom settings.

    Args:
        images: List of PIL Images to save
        output_path: Path where the PDF will be saved
        compression: Compression method ('jpeg', 'png', etc.)
        quality: Compression quality (1-100, higher is better)

    Returns:
        Path to the saved PDF file
    """
    if not images:
        raise ValueError("No images provided to save as PDF")

    # Convert to Path if string
    if isinstance(output_path, str):
        output_path = Path(output_path)

    # Create parent directories if they don't exist
    output_path.parent.mkdir(exist_ok=True, parents=True)

    # Save the first image and append the rest
    first_image = images[0]
    remaining_images = images[1:] if len(images) > 1 else []

    logger.info(
        f"Saving {len(images)} images as PDF with {compression} compression: {output_path}"
    )

    # Convert to RGB if needed (PDF doesn't support RGBA)
    if first_image.mode == "RGBA":
        first_image = first_image.convert("RGB")

    # Convert remaining images to RGB if needed
    rgb_remaining = []
    for img in remaining_images:
        if img.mode == "RGBA":
            rgb_remaining.append(img.convert("RGB"))
        else:
            rgb_remaining.append(img)

    # Save as PDF with custom settings
    first_image.save(
        output_path,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=rgb_remaining,
        compression=compression,
        quality=quality,
    )

    return output_path
