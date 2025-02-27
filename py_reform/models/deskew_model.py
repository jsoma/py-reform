"""
Deskew model for document straightening.

This implementation uses the deskew package to detect and correct skew in document images.
"""

import logging
import numpy as np
import PIL.Image

from py_reform.models.base import DewarpingModel

try:
    from deskew import determine_skew
    DESKEW_AVAILABLE = True
except ImportError:
    DESKEW_AVAILABLE = False

logger = logging.getLogger(__name__)


class DeskewModel(DewarpingModel):
    """
    Deskew model for document straightening.
    
    This model uses the deskew package to detect and correct skew in document images.
    It's a simpler alternative to the UVDoc model for basic document straightening.
    """
    
    def __init__(self, max_angle: float = 45.0, num_peaks: int = 20, **kwargs):
        """
        Initialize the Deskew model.
        
        Args:
            max_angle: Maximum angle to consider for skew detection (in degrees)
            num_peaks: Number of peaks to consider in the Hough transform
            **kwargs: Additional parameters (ignored)
        """
        if not DESKEW_AVAILABLE:
            raise ImportError(
                "The deskew package is required for the Deskew model. "
                "Install it with 'pip install deskew'."
            )
        
        self.max_angle = max_angle
        self.num_peaks = num_peaks
        logger.info(f"Initialized Deskew model with max_angle={max_angle}, num_peaks={num_peaks}")
    
    def process(self, image: PIL.Image.Image) -> PIL.Image.Image:
        """
        Process an image to straighten it using the Deskew algorithm.
        
        Args:
            image: The input image to straighten
            
        Returns:
            The straightened image
        """
        # Convert PIL image to numpy array
        img_np = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_np.shape) == 3 and img_np.shape[2] >= 3:
            # Use simple averaging for grayscale conversion
            grayscale = np.mean(img_np[:, :, :3], axis=2).astype(np.uint8)
        else:
            grayscale = img_np
        
        # Determine skew angle
        angle = determine_skew(grayscale, max_angle=self.max_angle, num_peaks=self.num_peaks)
        
        if angle is None or abs(angle) < 0.1:
            logger.info("No significant skew detected")
            return image
        
        logger.info(f"Detected skew angle: {angle:.2f} degrees")
        
        # Rotate the image to correct the skew
        # We use PIL for rotation to avoid scikit-image dependency
        rotated_image = image.rotate(
            angle, 
            resample=PIL.Image.Resampling.BILINEAR,
            expand=True,
            fillcolor=(255, 255, 255) if image.mode == 'RGB' else 255
        )
        
        return rotated_image 