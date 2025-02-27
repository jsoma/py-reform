"""
Core functionality for the py-reform library.
"""

import logging
from pathlib import Path
from typing import List, Literal, Optional, Union

import PIL.Image
from tqdm import tqdm

from py_reform.models import get_model
from py_reform.utils.pdf import pdf_to_images

logger = logging.getLogger(__name__)


def straighten(
    source: Union[str, Path, PIL.Image.Image],
    pages: Optional[List[int]] = None,
    model: str = "uvdoc",
    errors: Literal["raise", "ignore", "warn"] = "raise",
    **model_params,
) -> Union[PIL.Image.Image, List[PIL.Image.Image]]:
    """
    Dewarp/straighten document images or PDF pages.

    Args:
        source: Path to image or PDF file, or PIL Image object
        pages: List of page indices to process (for PDFs only)
        model: Name of the dewarping model to use
        errors: How to handle errors during processing
        **model_params: Additional parameters to pass to the model

    Returns:
        A single PIL Image or a list of PIL Images
    """
    # Get the appropriate model
    dewarping_model = get_model(model, **model_params)

    # Handle different input types
    if isinstance(source, PIL.Image.Image):
        # Process a single PIL image
        try:
            return dewarping_model.process(source)
        except Exception as e:
            result = _handle_error(e, source, errors)
            if result is None:
                # If ignore mode returns None, we need to return an empty list to match the return type
                return []
            return result

    # Convert string to Path if needed
    if isinstance(source, str):
        source_path = Path(source)
    else:
        source_path = source

    # Check if the source is a PDF
    if source_path.suffix.lower() == ".pdf":
        # Extract images from PDF
        images = pdf_to_images(source_path, pages=pages)

        # Process each image
        processed_images = []
        for img in tqdm(images, desc="Processing pages"):
            try:
                processed = dewarping_model.process(img)
                processed_images.append(processed)
            except Exception as e:
                result = _handle_error(e, img, errors)
                if result is not None:
                    processed_images.append(result)

        return processed_images

    # Process a single image file
    try:
        img = PIL.Image.open(source_path)
        return dewarping_model.process(img)
    except Exception as e:
        result = _handle_error(e, PIL.Image.open(source_path), errors)
        if result is None:
            # If ignore mode returns None, we need to return an empty list to match the return type
            return []
        return result


def _handle_error(
    error: Exception, original_image: PIL.Image.Image, 
    error_mode: Literal["raise", "ignore", "warn"]
) -> Optional[PIL.Image.Image]:
    """Handle errors based on the specified error mode."""
    if error_mode == "raise":
        raise error
    elif error_mode == "warn":
        logger.warning(f"Error during processing: {error}. Using original image.")
        return original_image
    elif error_mode == "ignore":
        logger.warning(f"Error during processing: {error}. Skipping image.")
        return None
    else:
        raise ValueError(f"Invalid error mode: {error_mode}")
