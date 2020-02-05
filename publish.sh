#!/bin/bash

rm -rf dist build
python setup.py sdist
twine upload dist/* -r $1
rm -rf dist build
