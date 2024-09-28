#!/usr/bin/env bash

# Minify Hapticlock.py, compile it to mpy, and copy it to Pico W.
./minify.sh

mpy-cross Hapticlock_min.py

sudo mpremote cp Hapticlock_min.mpy :lib/Hapticlock_min.mpy
