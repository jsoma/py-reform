# py-reform: PDF & Image Dewarping Library

A Python library for dewarping/straightening/reformatting document images and PDFs.

![An example](examples/comparison.jpg)

## Features

- Dewarp/straighten single images
- Process entire PDFs or selected pages
- Return PIL images for further processing
- Save results as images or PDFs
- Progress tracking with tqdm
- Flexible error handling
- Automatic EXIF orientation handling
- Multiple dewarping models

## Installation

```bash
pip install py-reform
```

## Quick Start

### Process a Single Image

```python
from py_reform import straighten

# Process a single image
straight_image = straighten("curved_page.jpg")
straight_image.save("straight_page.jpg")
```

### Process a PDF

```python
from py_reform import straighten, save_pdf

# Process a PDF (all pages)
straight_pages = straighten("document.pdf")

# Save processed pages as a new PDF
save_pdf(straight_pages, "straight_document.pdf")
```

### Process Specific PDF Pages

```python
# Process specific PDF pages
straight_pages = straighten("document.pdf", pages=[0, 2, 5])
```

### Choose a Different Dewarping Model

By default we use [UVDoc](https://github.com/tanguymagne/UVDoc), which works for all sorts of problematic images. If you just need to rotate the image, though, use [deskew](https://github.com/sbrunner/deskew) instead.

```python
# Use the rotation-based deskew model
straight_image = straighten("document.jpg", model="deskew")

# Use the UVDoc model with custom parameters
straight_image = straighten("document.jpg", model="uvdoc", device="cpu")

# Configure deskew model parameters
straight_image = straighten("document.jpg", model="deskew", max_angle=15.0, num_peaks=30)
```

### Create Before/After Comparisons

```python
from py_reform.utils import create_comparison

straight_image = straighten("curved_page.jpg")

# Create a side-by-side comparison
comparison = create_comparison(["curved_page.jpg", straight_image])
comparison.save("comparison.jpg")
```

### Error Handling

```python
# Default: stop on error
result = straighten("document.pdf", errors="raise") 
# Skip errors, log warning
result = straighten("document.pdf", errors="ignore")
# Use original on error with warning
result = straighten("document.pdf", errors="warn")   
```

### Working with Image Orientation

The library automatically handles EXIF orientation data in JPEG files, ensuring that images are correctly oriented before processing. You can also use these utilities directly:

```python
from py_reform.utils import open_image, auto_rotate_image
import PIL.Image

# Open an image with automatic orientation correction
img = open_image("photo.jpg")

# Or correct orientation of an already opened image
img = PIL.Image.open("photo.jpg")
img = auto_rotate_image(img)
```

## Available Models

- [UVDoc](https://github.com/tanguymagne/UVDoc/)
- [deskew](https://github.com/sbrunner/deskew)

## Examples

See [examples/examples.py](examples/examples.py)

## Citation

The UVDoc model is based on original work by Floor Verhoeven, Tanguy Magne, and Olga Sorkine-Hornung. If you use py-reform with the UVDoc model, please consider citing their work:

```bibtex
@inproceedings{UVDoc,
title={{UVDoc}: Neural Grid-based Document Unwarping},
author={Floor Verhoeven and Tanguy Magne and Olga Sorkine-Hornung},
booktitle = {SIGGRAPH ASIA, Technical Papers},
year = {2023},
url={https://doi.org/10.1145/3610548.3618174}
}
```

Original UVDoc repository: [https://github.com/tanguymagne/UVDoc/](https://github.com/tanguymagne/UVDoc/)

## Anything else??

I'm pretty sure I wrote about *two lines of code for this*, the rest was all [Cursor](https://www.cursor.com/en) and [Claude 3.7 Sonnet](https://claude.ai/). My job was mostly making demands around pathlib and ditching OpenCV.