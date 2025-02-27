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
# Process a single image
# =====================================================================

# Process an image and save the result
image = straighten("examples/data/G38J5.jpg", model="uvdoc")
image.save("examples/output/straightened.jpg")

# Create a side-by-side comparison
comparison = create_comparison(
    before="examples/data/G38J5.jpg",
    after=image,
    spacing=10  # Add 10px spacing between images
)
comparison.save("examples/output/comparison.jpg")

# =====================================================================
# Process an entire PDF
# =====================================================================

# Process all pages in a PDF
pages = straighten("examples/data/Adobe Scan 23 Jan 2024.pdf", model="uvdoc")
save_pdf(pages, "examples/output/straightened.pdf")

# Create comparisons for the first two pages
original_pages = pdf_to_images("examples/data/Adobe Scan 23 Jan 2024.pdf", pages=[0, 1])
comparisons = create_comparison(
    before=original_pages,
    after=pages[:2]
)

# Save the comparison images
for i, comp in enumerate(comparisons):
    comp.save(f"examples/output/pdf_comparison_{i}.jpg")

# =====================================================================
# Process specific PDF pages
# =====================================================================

# Process only pages 0 and 1 (first and second pages)
pages = straighten("examples/data/Adobe Scan 23 Jan 2024.pdf", pages=[0, 1], model="uvdoc")
save_pdf(pages, "examples/output/pages_0_1.pdf")

# =====================================================================
# Save PDF pages as individual images
# =====================================================================

# Process a PDF and save each page as an individual image
pages = straighten("examples/data/Adobe Scan 23 Jan 2024.pdf", pages=[0, 1], model="uvdoc")
for i, page in enumerate(pages):
    page.save(f"examples/output/page_{i}.jpg", "JPEG", quality=95)
