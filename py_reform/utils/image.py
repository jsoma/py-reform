"""
Image utility functions for the py-reform library.
"""

import logging
from typing import Union
from pathlib import Path

import PIL.Image
from PIL import ExifTags

logger = logging.getLogger(__name__)

def auto_rotate_image(image: PIL.Image.Image) -> PIL.Image.Image:
    """
    Automatically rotate an image based on EXIF orientation.
    
    Args:
        image: PIL Image object
        
    Returns:
        PIL.Image.Image: The correctly oriented image
    """
    # Check if the image has EXIF data
    if hasattr(image, '_getexif') and image._getexif() is not None:
        exif = dict(image._getexif().items())
        
        # Find the orientation tag
        orientation_tag = None
        for tag, tag_value in ExifTags.TAGS.items():
            if tag_value == 'Orientation':
                orientation_tag = tag
                break
        
        # Apply the appropriate rotation based on orientation
        if orientation_tag and orientation_tag in exif:
            orientation = exif[orientation_tag]
            
            # Orientation values and their corresponding rotations:
            # 1: No rotation (normal)
            # 2: Mirror horizontal
            # 3: Rotate 180 degrees
            # 4: Mirror vertical
            # 5: Mirror horizontal and rotate 270 degrees
            # 6: Rotate 90 degrees (rotate right)
            # 7: Mirror horizontal and rotate 90 degrees
            # 8: Rotate 270 degrees (rotate left)
            
            if orientation == 2:
                image = image.transpose(PIL.Image.Transpose.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                image = image.transpose(PIL.Image.Transpose.ROTATE_180)
            elif orientation == 4:
                image = image.transpose(PIL.Image.Transpose.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                image = image.transpose(PIL.Image.Transpose.FLIP_LEFT_RIGHT)
                image = image.transpose(PIL.Image.Transpose.ROTATE_90)
            elif orientation == 6:
                image = image.transpose(PIL.Image.Transpose.ROTATE_270)
            elif orientation == 7:
                image = image.transpose(PIL.Image.Transpose.FLIP_LEFT_RIGHT)
                image = image.transpose(PIL.Image.Transpose.ROTATE_270)
            elif orientation == 8:
                image = image.transpose(PIL.Image.Transpose.ROTATE_90)
    
    return image

def open_image(image_path: Union[str, Path]) -> PIL.Image.Image:
    """
    Open an image file and automatically correct its orientation.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        PIL.Image.Image: The opened image with correct orientation
    """
    # Convert to Path if string
    if isinstance(image_path, str):
        image_path = Path(image_path)
        
    # Check if file exists
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Open the image
    image = PIL.Image.open(image_path)
    
    # Auto-rotate based on EXIF data
    return auto_rotate_image(image) 