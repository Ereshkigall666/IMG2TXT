#!/usr/bin/env bash

START=1
END=500
INCREMENT=100
INPUT_DIR=$1
ENGINE=$2

# check that input_dir was provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <main_directory> <engine>"
    exit 1
fi

for ((i = $START; i <= $END; i += $INCREMENT)); do
    CURR_SUBDIR="$INPUT_DIR/unzips/$(((i - 1) * 100 + 1))-$((i * 100))"
    OCR_SUBDIR="$INPUT_DIR/ocr_dirs/$(((i - 1) * 100 + 1))-$((i * 100))_ocr"
    if [ -d "$CURR_SUBDIR" ]; then
        echo "$CURR_SUBDIR"
        python img2txt_light.py "$CURR_SUBDIR" -f -e "$ENGINE" -o "$OCR_SUBDIR"
    fi

done
