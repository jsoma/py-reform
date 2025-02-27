"""
Setup script for py-reform.
"""

from setuptools import setup, find_namespace_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="py-reform",
    version="0.1.0",
    author="Jonathan Soma",
    author_email="jonathan.soma@gmail.com",
    description="A Python library for dewarping/straightening/reformatting document images and PDFs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jsoma/py-reform",
    packages=find_namespace_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Multimedia :: Graphics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pillow>=9.0.0",
        "numpy>=1.20.0",
        "tqdm>=4.60.0",
        "pypdfium2>=4.0.0",
        "torch>=1.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=0.950",
        ],
    },
    include_package_data=True,
    package_data={
        "py_reform.models": ["weights/*.pkl"],
    },
) 