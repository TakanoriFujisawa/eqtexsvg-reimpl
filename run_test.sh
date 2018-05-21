#!/bin/bash

cd $(dirname $BASH_SOURCE)

# 参考 : http://www.kabipan.com/computer/inkscape/

export PYTHONPATH="/usr/share/inkscape/extensions"
./eqtexsvg.py --debug true blank.svg > temp.svg

xmllint --format temp.svg > output.svg
