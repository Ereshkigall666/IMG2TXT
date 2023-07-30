#!/usr/bin/env bash

# Tesseract: 1-500, 501-600, 601-700, 701-900, 901-1100, 1101-1300, 1301-1400, 1401-1500, 1501-1600, 1601-1800, 1801-2000, 2001-2100, 2101-2300, 2301-2500, 2501-2600, 2601-2800, (human-num: 2801-3000), (squidward: 3001-3200), (huma-num:3201-3400), (huma-num:3401-3600), (squidward: 3601-3700), 3701-3900, (huma-num: 3901-4100)
# Kraken: 1-500, 501-700, 701-900, 901-1000, 1001-1100, 1101-1200, 1201-1300, 1301-1500, 1501-1600, (huma-num: 1601-1700), 1701-1800, 1801-2000, 2001-2100, (huma-num: 2101-2300, 2301-2500), 2501-2700, 2701-2900, 2901-3100, (huma-num: 3101-3200), 3201-3400, 3401-3600, 3601-3800, 3801-4000, 4001-4100

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

if [ -n "$3" ]; then
    START="$3"
fi

if [ -n "$4" ]; then
    END="$4"
fi
# for numbered folders
if [[ $START =~ ^[0-9]+$ ]]; then
    for ((i = $START; i <= $END; i += $INCREMENT)); do
        CURR_SUBDIR="$INPUT_DIR/unzips/$i-$((i + 100 - 1))"
        OCR_SUBDIR="$INPUT_DIR/ocr_dirs/$i-$((i + 100 - 1))_ocr"
        echo "$OCR_SUBDIR"
        if [ -d "$CURR_SUBDIR" ]; then
            echo "$CURR_SUBDIR"
            python img2txt_light.py "$CURR_SUBDIR" -e "$ENGINE" -o "$OCR_SUBDIR"
        fi
    done
# unnumbered folders
else
    for DOC in "${@:3}"; do
        CURR_SUBDIR="$INPUT_DIR/unzips/$DOC"
        OCR_SUBDIR="$INPUT_DIR/ocr_dirs/${DOC}_ocr"
        echo "$OCR_SUBDIR"
        python img2txt_light.py "$CURR_SUBDIR" -e "$ENGINE" -o "$OCR_SUBDIR"
    done
fi
