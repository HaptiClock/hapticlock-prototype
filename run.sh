#!/usr/bin/env bash

# Minify Hapticlock.py, compile it to mpy, and copy it to Pico W.
# Also copy over other relevant files.
# Then soft-reset Pico to run main.py.

./minify.sh

mpy-cross Hapticlock_min.py

sudo mpremote cp Hapticlock_min.mpy :lib/Hapticlock_min.mpy
sudo mpremote cp index.html :index.html
sudo mpremote cp settings.html :settings.html
sudo mpremote cp settings.json :settings.json

sudo mpremote soft-reset

# Run HaptiClock
sudo mpremote exec 'import main'
