"""
Base class for dewarping models.
"""

from abc import ABC, abstractmethod
from typing import Optional

import PIL.Image


class DewarpingModel(ABC):
    """Base class for all dewarping models."""

    @abstractmethod
    def process(self, image: PIL.Image.Image) -> PIL.Image.Image:
        """
        Process an image to dewarp/straighten it.

        Args:
            image: The input image to process

        Returns:
            The processed (dewarped) image
        """
        pass
