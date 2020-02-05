rm -rf dist build
python setup.py sdist
twine upload dist/* -r pypitest
rm -rf dist build
