"""
Comparison utility functions for the py-reform library.
"""

from pathlib import Path
from typing import List, Tuple, Union

import PIL.Image


def create_comparison(
    before: Union[PIL.Image.Image, List[PIL.Image.Image], str, Path],
    after: Union[PIL.Image.Image, List[PIL.Image.Image], str, Path],
    orientation: str = "horizontal",
    spacing: int = 0,
    background_color: Union[str, Tuple[int, int, int]] = "white",
) -> Union[PIL.Image.Image, List[PIL.Image.Image]]:
    """
    Create a comparison image or images showing before and after processing.

    Args:
        before: Original image(s) or path to image file
        after: Processed image(s) or path to image file
        orientation: How to arrange the images - "horizontal" or "vertical"
        spacing: Pixels of space between images
        background_color: Color for the background/spacing

    Returns:
        A single comparison image or a list of comparison images
    """
    # Handle different input types
    before_images = _ensure_image_list(before)
    after_images = _ensure_image_list(after)

    # Ensure we have the same number of before and after images
    if len(before_images) != len(after_images):
        raise ValueError(
            f"Number of before images ({len(before_images)}) must match "
            f"number of after images ({len(after_images)})"
        )

    # Create comparison images
    comparisons = []
    for before_img, after_img in zip(before_images, after_images):
        # Create the comparison image
        comparison = _create_single_comparison(
            before_img, after_img, orientation, spacing, background_color
        )
        comparisons.append(comparison)

    # Return a single image or a list depending on input
    return comparisons[0] if len(comparisons) == 1 else comparisons


def _ensure_image_list(
    images: Union[PIL.Image.Image, List[PIL.Image.Image], str, Path]
) -> List[PIL.Image.Image]:
    """Convert various input types to a list of PIL Images."""
    if isinstance(images, (str, Path)):
        # Load image from file
        return [PIL.Image.open(images)]
    elif isinstance(images, PIL.Image.Image):
        # Single PIL Image
        return [images]
    elif isinstance(images, list):
        # List of images
        if all(isinstance(img, PIL.Image.Image) for img in images):
            return images
        else:
            raise TypeError("All items in the list must be PIL Image objects")
    else:
        raise TypeError(
            f"Expected PIL.Image.Image, list of images, or path, got {type(images)}"
        )


def _create_single_comparison(
    before_img: PIL.Image.Image,
    after_img: PIL.Image.Image,
    orientation: str,
    spacing: int,
    background_color: Union[str, Tuple[int, int, int]],
) -> PIL.Image.Image:
    """Create a single comparison image from before and after images."""
    # Determine dimensions based on orientation
    if orientation.lower() == "horizontal":
        width = before_img.width + after_img.width + spacing
        height = max(before_img.height, after_img.height)

        # Create new image with background color
        comparison = PIL.Image.new("RGB", (width, height), background_color)

        # Paste images
        comparison.paste(before_img, (0, 0))
        comparison.paste(after_img, (before_img.width + spacing, 0))

    elif orientation.lower() == "vertical":
        width = max(before_img.width, after_img.width)
        height = before_img.height + after_img.height + spacing

        # Create new image with background color
        comparison = PIL.Image.new("RGB", (width, height), background_color)

        # Paste images
        comparison.paste(before_img, (0, 0))
        comparison.paste(after_img, (0, before_img.height + spacing))

    else:
        raise ValueError(
            f"Orientation must be 'horizontal' or 'vertical', got '{orientation}'"
        )

    return comparison
