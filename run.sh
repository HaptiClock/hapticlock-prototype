#!/usr/bin/env bash

# Minify code and compile Python to mpy.
# Copy over all relevant files.
# Run 'import main' in Pico to run program.

./minify.sh

mpy-cross Hapticlock_min.py

sudo mpremote cp Hapticlock_min.mpy :lib/Hapticlock_min.mpy
sudo mpremote cp index_min.html :index_min.html
sudo mpremote cp settings_min.html :settings_min.html
sudo mpremote cp lightlevels_min.html :lightlevels_min.html
sudo mpremote cp style_min.css :style_min.css
# Comment this to maintain changes to Settings between ./run.sh
sudo mpremote cp settings.json :settings.json

sudo mpremote soft-reset

# Run HaptiClock
sudo mpremote exec 'import main'
