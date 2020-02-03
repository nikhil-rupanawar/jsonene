#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
__version__ = "0.0.2"

from setuptools import find_packages, setup

setup(
    name="jsonene",
    packages=find_packages(),
    version=__version__,
    description="Type declaration and validation library for JSON",
    url="https://github.com/nikhil-rupanawar/jsonene/archive/0.0.1.tar.gz",
    author="Nikhil Rupanawar",
    author_email="conikhil@gmail.com",
    license="MIT",
    keywords = ['json', 'validation', 'jsonschema'],
    install_requires=['jsonschema>=3.2.0'],
)
