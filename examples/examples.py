"""
Simple examples for using py-reform to dewarp document images and PDFs.
"""

import sys
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import py_reform
sys.path.insert(0, str(Path(__file__).parent.parent))

from py_reform import straighten, save_pdf
from py_reform.utils import create_comparison, pdf_to_images
import PIL.Image

# Clean up and recreate output directory
output_dir = Path("examples/output")
if output_dir.exists():
    # Remove all files in the output directory
    for file_path in output_dir.glob("*"):
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            shutil.rmtree(file_path)
    print(f"Cleaned up existing output directory: {output_dir}")
else:
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True)
    print(f"Created output directory: {output_dir}")

# =====================================================================
# Process a single image with the default model
# =====================================================================

# Process an image and save the result
image = straighten("examples/data/G38J5.jpg")
image.save("examples/output/straightened.jpg")

# Create a side-by-side comparison
comparison = create_comparison(
    ["examples/data/G38J5.jpg", image],
    spacing=10  # Add 10px spacing between images
)
comparison.save("examples/output/comparison.jpg")

# Process an image with rotated EXIF data
image = straighten("examples/data/sideways.jpg")
image.save("examples/output/sideways_straightened.jpg")

# =====================================================================
# Process an image with the deskew model
# =====================================================================

# Process an image with the Deskew model
deskew_image = straighten("examples/data/G38J5.jpg", model="deskew")
deskew_image.save("examples/output/deskew_straightened.jpg")

# =====================================================================
# Process an entire PDF
# =====================================================================

# Process all pages in a PDF
pages = straighten("examples/data/Adobe Scan 23 Jan 2024.pdf")
save_pdf(pages, "examples/output/straightened.pdf")

# Create comparisons for the first two pages
original_pages = pdf_to_images("examples/data/Adobe Scan 23 Jan 2024.pdf", pages=[0, 1])

# Save the comparison images
for i, (page, original) in enumerate(zip(pages, original_pages)):
    comparison = create_comparison([original, page])
    comparison.save(f"examples/output/pdf_comparison_{i}.jpg")

# =====================================================================
# Process specific PDF pages
# =====================================================================

# Process only pages 0 and 1 (first and second pages)
pages = straighten("examples/data/Adobe Scan 23 Jan 2024.pdf", pages=[0, 1])
save_pdf(pages, "examples/output/pages_0_1.pdf")

# =====================================================================
# Process PDF with the Deskew model
# =====================================================================

# Process a PDF with the Deskew model
deskew_pages = straighten("examples/data/Adobe Scan 23 Jan 2024.pdf", model="deskew")
save_pdf(deskew_pages, "examples/output/deskew_straightened.pdf")

# =====================================================================
# Save PDF pages as individual images
# =====================================================================

# Process a PDF and save each page as an individual image
pages = straighten("examples/data/Adobe Scan 23 Jan 2024.pdf", pages=[0, 1])
for i, page in enumerate(pages):
    page.save(f"examples/output/page_{i}.jpg", "JPEG", quality=95)

# =====================================================================
# NEW: Multi-image comparison examples
# =====================================================================

# Process an image with different models
original = PIL.Image.open("examples/data/G38J5.jpg")
uvdoc_result = straighten("examples/data/G38J5.jpg", model="uvdoc")
deskew_result = straighten("examples/data/G38J5.jpg", model="deskew")

# Create a comparison with multiple images in a row
multi_comparison = create_comparison(
    images=[original, uvdoc_result, deskew_result],
    labels=["Original", "UVDoc Model", "Deskew Model"],
    spacing=15,
)
multi_comparison.save("examples/output/multi_model_comparison.jpg")
print(f"Created multi-model comparison: examples/output/multi_model_comparison.jpg")
