#!/bin/bash
# animkit test suite: pose math, frames/mask calibration, pose render timing, bake->strip->export round trip, loop seam.
set -e
cd "$(dirname "$0")/../../.."
python3 tools/animkit/tests/test_all.py "$@"
