#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from __future__ import with_statement
from __future__ import absolute_import
from io import open
__version__ = u"0.0.13"

from setuptools import find_packages, setup

with open(u"README.md", u"r") as fh:
    long_description = fh.read()

setup(
    name=u"jsonene",
    packages=find_packages(),
    version=__version__,
    description=u"Type declaration and validation library for JSON",
    url=u"https://github.com/nikhil-rupanawar/jsonene",
    author=u"Nikhil Rupanawar",
    author_email=u"conikhil@gmail.com",
    license=u"MIT",
    keywords=[u"json", u"validation", u"schema"],
    install_requires=[u"jsonschema>=3.2.0"],
    python_requires=u">=3.6",
    long_description=long_description,
    long_description_content_type=u"text/markdown",
    classifiers=[
        u"Programming Language :: Python :: 3",
        u"License :: OSI Approved :: MIT License",
        u"Operating System :: OS Independent",
    ],
)
