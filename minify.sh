#!/usr/bin/env bash

# Minify with python-minifier
# Remove docstrings
# Rename classes to e.g. 'A'
pyminify --output "Hapticlock_min.py" \
    --remove-literal-statements --rename-globals Hapticlock.py
