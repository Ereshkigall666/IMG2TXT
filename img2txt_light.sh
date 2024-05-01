#!/bin/bash

PYTHON=python3.11

SCRIPT_PATH=$(realpath "./src/img2txt_light.py")
#echo "$SCRIPT_PATH"

"$PYTHON" "$SCRIPT_PATH" "$@"
