#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
__version__ = "0.0.13"

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="jsonene",
    packages=find_packages(),
    version=__version__,
    description="Type declaration and validation library for JSON",
    url="https://github.com/nikhil-rupanawar/jsonene",
    author="Nikhil Rupanawar",
    author_email="conikhil@gmail.com",
    license="MIT",
    keywords=["json", "validation", "schema"],
    install_requires=["jsonschema>=3.2.0"],
    python_requires=">=3.6",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
