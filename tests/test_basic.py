"""
Basic tests for py-reform.
"""

import sys
import unittest
from pathlib import Path

# Add the parent directory to the path so we can import py_reform
sys.path.insert(0, str(Path(__file__).parent.parent))

import PIL.Image
from py_reform import straighten
from py_reform.models import get_model

class TestBasic(unittest.TestCase):
    """Basic tests for py-reform."""
    
    def test_get_model(self):
        """Test that we can get a model."""
        try:
            model = get_model("uvdoc")
            self.assertIsNotNone(model)
        except ImportError:
            # Skip if torch is not available
            self.skipTest("PyTorch not available")
    
    def test_straighten_image(self):
        """Test straightening an image."""
        # Create a simple test image
        test_image = PIL.Image.new("RGB", (100, 100), color="white")
        
        # Process the image
        try:
            result = straighten(test_image)
            
            # Check that we got an image back
            self.assertIsInstance(result, PIL.Image.Image)
            
            # Check that the dimensions are the same
            self.assertEqual(result.size, test_image.size)
        except ImportError:
            # Skip if torch is not available
            self.skipTest("PyTorch not available")
    
    def test_invalid_model(self):
        """Test that we get an error for an invalid model."""
        with self.assertRaises(ValueError):
            get_model("invalid_model")

if __name__ == "__main__":
    unittest.main() 