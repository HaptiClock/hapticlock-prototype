#!/usr/bin/env bash

# Minify Python with python-minifier, add flags to remove docstrings and rename
# classes to e.g. 'A'
pyminify --output "Hapticlock_min.py" \
    --remove-literal-statements --rename-globals Hapticlock.py

# Minify CSS
yui-compressor style.css >"style_min.css"
