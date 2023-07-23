#!/usr/bin/env bash

# Tesseract: 1-500, 501-600, 601-700, 701-900, 901-1100, 1101-1300, 1301-1400, 1401-1500, 1501-1600, 1601-1800, 1801-2000
# Kraken: 1-500, 501-700, 701-900, 901-1000

START=501
END=600
INCREMENT=100
INPUT_DIR=$1
ENGINE=$2

# check that input_dir was provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <main_directory> <engine> <start> <end>"
    exit 1
fi

if [ -n "$3" ] ; then
    START="$3"
fi

if [ -n "$4" ] ; then
    END="$4"
fi

for ((i = $START; i <= $END; i+=$INCREMENT)); do
    CURR_SUBDIR="$INPUT_DIR/unzips/$i-$((i + 100 - 1))"
    OCR_SUBDIR="$INPUT_DIR/ocr_dirs/$i-$((i + 100 - 1))_ocr" 
    echo "$OCR_SUBDIR"
    if [ -d "$CURR_SUBDIR" ]; then
        echo "$CURR_SUBDIR"
        python img2txt_light.py "$CURR_SUBDIR" -e "$ENGINE" -o "$OCR_SUBDIR"
    fi

done
