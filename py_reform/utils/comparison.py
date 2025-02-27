"""
Comparison utility functions for the py-reform library.
"""

from pathlib import Path
from typing import List, Tuple, Union, Optional

import PIL.Image
from PIL import ImageDraw, ImageFont
import math


def create_comparison(
    images: Union[PIL.Image.Image, List[PIL.Image.Image], str, Path, List[Union[str, Path]]],
    labels: Optional[List[str]] = None,
    orientation: str = "horizontal",
    grid_size: Optional[Tuple[int, int]] = None,
    spacing: int = 10,
    label_height: int = 30,
    background_color: Union[str, Tuple[int, int, int]] = "white",
    text_color: Union[str, Tuple[int, int, int]] = "black",
    resize_mode: str = "fit",
    target_size: Optional[Tuple[int, int]] = None,
) -> Union[PIL.Image.Image, List[PIL.Image.Image]]:
    """
    Create a comparison image showing multiple images side by side or in a grid.

    Args:
        images: Images to compare. Can be:
            - A single image (PIL.Image.Image or path)
            - A list of images (List[PIL.Image.Image] or List[path])
            - For backward compatibility: if exactly two arguments are provided as
              positional args, they are treated as 'before' and 'after'
        labels: Optional list of labels for each image
        orientation: How to arrange the images - "horizontal", "vertical", or "grid"
        grid_size: Optional tuple of (rows, cols) for grid layout. If not provided,
                  will be calculated automatically based on the number of images
        spacing: Pixels of space between images and around the border
        label_height: Height in pixels for the label area (0 to disable labels)
        background_color: Color for the background/spacing
        text_color: Color for the label text
        resize_mode: How to handle different image sizes:
            - "fit": Resize all images to fit the smallest image
            - "stretch": Stretch all images to the same size
            - "none": Keep original sizes (may result in uneven grid)
        target_size: Optional target size for all images (width, height)

    Returns:
        A single comparison image
    """
    # Handle backward compatibility with before/after pattern
    if isinstance(images, (PIL.Image.Image, str, Path)) and 'after' in locals():
        # This is the old before/after pattern
        before = images
        after = locals()['after']
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
    
    # New unified approach - convert all inputs to a list of PIL Images
    pil_images = _ensure_image_list(images)
    
    # If only one image, just return it
    if len(pil_images) == 1:
        return pil_images[0]
    
    # If exactly two images and orientation is horizontal or vertical, use the simple comparison
    if len(pil_images) == 2 and orientation.lower() in ["horizontal", "vertical"]:
        return _create_single_comparison(
            pil_images[0], pil_images[1], orientation, spacing, background_color
        )
    
    # For more than two images or grid orientation, create a grid
    if orientation.lower() == "grid" or grid_size is not None:
        # Use grid layout
        return _create_grid(
            pil_images,
            labels,
            grid_size,
            spacing,
            label_height,
            background_color,
            text_color,
            resize_mode,
            target_size,
        )
    
    # For horizontal or vertical layouts with more than 2 images
    return _create_row_or_column(
        pil_images,
        labels,
        orientation,
        spacing,
        label_height,
        background_color,
        text_color,
        resize_mode,
        target_size,
    )


def _create_row_or_column(
    images: List[PIL.Image.Image],
    labels: Optional[List[str]] = None,
    orientation: str = "horizontal",
    spacing: int = 10,
    label_height: int = 30,
    background_color: Union[str, Tuple[int, int, int]] = "white",
    text_color: Union[str, Tuple[int, int, int]] = "black",
    resize_mode: str = "fit",
    target_size: Optional[Tuple[int, int]] = None,
) -> PIL.Image.Image:
    """Create a row or column of images with optional labels."""
    # Handle labels
    if labels is not None:
        if len(labels) < len(images):
            # Pad with empty strings if needed
            labels = labels + [""] * (len(images) - len(labels))
        elif len(labels) > len(images):
            # Truncate if too many labels
            labels = labels[: len(images)]
    else:
        # No labels provided
        labels = [""] * len(images)
        label_height = 0
    
    # Determine target size for images
    if target_size is not None:
        # Use provided target size
        cell_width, cell_height = target_size
    elif resize_mode != "none":
        # Calculate target size based on resize mode
        if resize_mode == "fit":
            # Find the smallest image dimensions
            min_width = min(img.width for img in images)
            min_height = min(img.height for img in images)
            cell_width, cell_height = min_width, min_height
        elif resize_mode == "stretch":
            # Use the average dimensions
            avg_width = sum(img.width for img in images) // len(images)
            avg_height = sum(img.height for img in images) // len(images)
            cell_width, cell_height = avg_width, avg_height
        else:
            raise ValueError(
                f"Invalid resize_mode: {resize_mode}. "
                f"Must be 'fit', 'stretch', or 'none'."
            )
        
        # Resize all images to the target size
        for i, img in enumerate(images):
            if img.width != cell_width or img.height != cell_height:
                images[i] = img.resize((cell_width, cell_height), PIL.Image.Resampling.LANCZOS)
    else:
        # Use the maximum dimensions for the cells
        cell_width = max(img.width for img in images)
        cell_height = max(img.height for img in images)
    
    # Calculate the total dimensions
    if orientation.lower() == "horizontal":
        total_width = len(images) * cell_width + (len(images) + 1) * spacing
        total_height = cell_height + 2 * spacing + label_height
    else:  # vertical
        total_width = cell_width + 2 * spacing
        total_height = len(images) * (cell_height + label_height) + (len(images) + 1) * spacing
    
    # Create the image
    result_img = PIL.Image.new("RGB", (total_width, total_height), background_color)
    draw = ImageDraw.Draw(result_img)
    
    # Try to get a font for the labels
    try:
        font = ImageFont.truetype("Arial", 12)
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Place images and labels
    for idx, (img, label) in enumerate(zip(images, labels)):
        if orientation.lower() == "horizontal":
            # Calculate position for this cell
            x = spacing + idx * (cell_width + spacing)
            y = spacing
            
            # Center the image in its cell if it's smaller than the cell
            img_x = x + (cell_width - img.width) // 2
            img_y = y + (cell_height - img.height) // 2
            
            # Paste the image
            result_img.paste(img, (img_x, img_y))
            
            # Add label if provided
            if label and label_height > 0:
                # Calculate text position (centered)
                text_width = draw.textlength(label, font=font)
                text_x = x + (cell_width - text_width) // 2
                text_y = y + cell_height + (label_height - 12) // 2  # Approximate font height
                
                # Draw the label
                draw.text((text_x, text_y), label, fill=text_color, font=font)
        else:  # vertical
            # Calculate position for this cell
            x = spacing
            y = spacing + idx * (cell_height + label_height + spacing)
            
            # Center the image in its cell if it's smaller than the cell
            img_x = x + (cell_width - img.width) // 2
            img_y = y + (cell_height - img.height) // 2
            
            # Paste the image
            result_img.paste(img, (img_x, img_y))
            
            # Add label if provided
            if label and label_height > 0:
                # Calculate text position (centered)
                text_width = draw.textlength(label, font=font)
                text_x = x + (cell_width - text_width) // 2
                text_y = y + cell_height + (label_height - 12) // 2  # Approximate font height
                
                # Draw the label
                draw.text((text_x, text_y), label, fill=text_color, font=font)
    
    return result_img


def _create_grid(
    images: List[PIL.Image.Image],
    labels: Optional[List[str]] = None,
    grid_size: Optional[Tuple[int, int]] = None,
    spacing: int = 10,
    label_height: int = 30,
    background_color: Union[str, Tuple[int, int, int]] = "white",
    text_color: Union[str, Tuple[int, int, int]] = "black",
    resize_mode: str = "fit",
    target_size: Optional[Tuple[int, int]] = None,
) -> PIL.Image.Image:
    """Create a grid of images with optional labels."""
    # Determine grid size if not provided
    if grid_size is None:
        cols = math.ceil(math.sqrt(len(images)))
        rows = math.ceil(len(images) / cols)
        grid_size = (rows, cols)
    else:
        rows, cols = grid_size
        if rows * cols < len(images):
            raise ValueError(
                f"Grid size {grid_size} is too small for {len(images)} images"
            )
    
    # Handle labels
    if labels is not None:
        if len(labels) < len(images):
            # Pad with empty strings if needed
            labels = labels + [""] * (len(images) - len(labels))
        elif len(labels) > len(images):
            # Truncate if too many labels
            labels = labels[: len(images)]
    else:
        # No labels provided
        labels = [""] * len(images)
        label_height = 0
    
    # Determine target size for images
    if target_size is not None:
        # Use provided target size
        cell_width, cell_height = target_size
    elif resize_mode != "none":
        # Calculate target size based on resize mode
        if resize_mode == "fit":
            # Find the smallest image dimensions
            min_width = min(img.width for img in images)
            min_height = min(img.height for img in images)
            cell_width, cell_height = min_width, min_height
        elif resize_mode == "stretch":
            # Use the average dimensions
            avg_width = sum(img.width for img in images) // len(images)
            avg_height = sum(img.height for img in images) // len(images)
            cell_width, cell_height = avg_width, avg_height
        else:
            raise ValueError(
                f"Invalid resize_mode: {resize_mode}. "
                f"Must be 'fit', 'stretch', or 'none'."
            )
        
        # Resize all images to the target size
        for i, img in enumerate(images):
            if img.width != cell_width or img.height != cell_height:
                images[i] = img.resize((cell_width, cell_height), PIL.Image.Resampling.LANCZOS)
    else:
        # Use the maximum dimensions for the grid cells
        cell_width = max(img.width for img in images)
        cell_height = max(img.height for img in images)
    
    # Calculate the total grid dimensions
    total_width = cols * cell_width + (cols + 1) * spacing
    total_height = rows * (cell_height + label_height) + (rows + 1) * spacing
    
    # Create the grid image
    grid_img = PIL.Image.new("RGB", (total_width, total_height), background_color)
    draw = ImageDraw.Draw(grid_img)
    
    # Try to get a font for the labels
    try:
        font = ImageFont.truetype("Arial", 12)
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Place images and labels in the grid
    for idx, (img, label) in enumerate(zip(images, labels)):
        if idx >= rows * cols:
            break  # Don't try to place more images than the grid can hold
        
        row = idx // cols
        col = idx % cols
        
        # Calculate position for this cell
        x = spacing + col * (cell_width + spacing)
        y = spacing + row * (cell_height + label_height + spacing)
        
        # Center the image in its cell if it's smaller than the cell
        img_x = x + (cell_width - img.width) // 2
        img_y = y + (cell_height - img.height) // 2
        
        # Paste the image
        grid_img.paste(img, (img_x, img_y))
        
        # Add label if provided
        if label and label_height > 0:
            # Calculate text position (centered)
            text_width = draw.textlength(label, font=font)
            text_x = x + (cell_width - text_width) // 2
            text_y = y + cell_height + (label_height - 12) // 2  # Approximate font height
            
            # Draw the label
            draw.text((text_x, text_y), label, fill=text_color, font=font)
    
    return grid_img


def _ensure_image_list(
    images: Union[PIL.Image.Image, List[PIL.Image.Image], str, Path, List[Union[str, Path]]]
) -> List[PIL.Image.Image]:
    """Convert various input types to a list of PIL Images."""
    if isinstance(images, (str, Path)):
        # Load image from file
        return [PIL.Image.open(images)]
    elif isinstance(images, PIL.Image.Image):
        # Single PIL Image
        return [images]
    elif isinstance(images, list):
        # List of images or paths
        result = []
        for img in images:
            if isinstance(img, PIL.Image.Image):
                result.append(img)
            elif isinstance(img, (str, Path)):
                result.append(PIL.Image.open(img))
            else:
                raise TypeError(f"Expected PIL.Image.Image or path, got {type(img)}")
        return result
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
