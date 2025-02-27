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

### Create Before/After Comparisons

```python
from py_reform.utils import create_comparison

straight_image = straighten("curved_page.jpg")

# Create a side-by-side comparison
comparison = create_comparison(
    before="curved_page.jpg",
    after=straight_image,
    spacing=10  # Add 10px spacing between images
)
comparison.save("comparison.jpg")
```

### Error Handling

```python
# Different error handling options
result = straighten("document.pdf", errors="raise")  # Default: stop on error
result = straighten("document.pdf", errors="ignore") # Skip errors, log warning
result = straighten("document.pdf", errors="warn")   # Use original on error with warning
```

## TODO

- Alternative dewarping algorithms/models

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