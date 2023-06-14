#!/bin/sh
# Prérequis :
# pdftoppm
# python3
# virtualenv

inType=$1 # -p (PDF) -j (JPG) -P (PNG) -t (TIF)
outType=$2 # -t (TXT) -h (HTML)
engine=$3 # -k (KRAKEN), -t (TESSERACT)
dir_path=$4


# 1. Environnement virtuel
if [ $engine = "-k" ]; then
	if [ ! -d "./venv_kraken/" ]; then
		echo "Création de l'environnment virtuel pour accueillir Kraken."
		mkdir ./venv_kraken/
		python3 -m venv ./venv_kraken/
		. ./venv_kraken/bin/activate
		echo "Environnement virtuel venv_kraken créé.\n\nTéléchargement de Kraken."
		pip3 install kraken
	else
		. ./venv_kraken/bin/activate
	fi
elif [ $engine = "-t" ]; then
	if [ ! -d "./venv_tesseract/" ]; then
		echo "Création de l'environnment virtuel pour accueillir Tesseract."
		mkdir ./venv_tesseract/
		virtualenv -p python3 venv_tesseract
		. ./venv_tesseract/bin/activate
		echo "Environnement virtuel venv_tesseract créé.\n\nTéléchargement de Tesseract."
		pip3 install pytesseract opencv-python
	else
		. ./venv_tesseract/bin/activate
	fi
fi

# 3. Segmentation des pages
if [ $inType = "-p" ]; then
	for file in `ls $dir_path*.pdf`; do pdftoppm -png $file $file; done
fi

# 4. Binarisation des images pour Kraken
if [ $engine = "-k" ]; then
	if [ $inType = "-p" ]; then
		for file in `ls $dir_path*.png`; do timeout 600 kraken -i $file $file"_bin.png" binarize; done
	elif [ $inType = "-P" ]; then
		for file in `ls $dir_path*.png`; do timeout 600 kraken -i $file $file"_bin.png" binarize; done
	elif [ $inType = "-j" ]; then
		for file in `ls $dir_path*.jpg`; do timeout 600 kraken -i $file $file"_bin.png" binarize; done
	elif [ $inType = "-t" ]; then
		for file in `ls $dir_path*.tif`; do timeout 600 kraken -i $file $file"_bin.png" binarize; done
	fi
fi

# 5. Segmentation et OCR
if [ $engine = "-k" ]; then
	if [ $outType = "-t" ]; then
		for file in `ls $dir_path*_bin.png`; do timeout 600 kraken -i $file $file".txt" segment ocr -m ./CORPUS17.mlmodel; done
	else
		for file in `ls $dir_path*_bin.png`; do timeout 600 kraken -i $file $file".html" segment ocr -m ./CORPUS17.mlmodel -h; done
	fi
elif [ $engine = "-t" ]; then
	# code pour lancer tesseract avec un fichier de config
	# ici html ça sera un fichier alto
	if [ $inType = "-p" ]; then
		for file in `ls $dir_path*.png`; do python3 tesseract_ocr.py $file $outType; done # if $outType -t --> TEXT if $outType -h --> ALTO
	elif [ $inType = "-P" ]; then
		for file in `ls $dir_path*.png`; do python3 tesseract_ocr.py $file $outType; done 
	elif [ $inType = "-j" ]; then
		for file in `ls $dir_path*.jpg`; do python3 tesseract_ocr.py $file $outType; done
	elif [ $inType = "-t" ]; then
		for file in `ls $dir_path*.tif`; do python3 tesseract_ocr.py $file $outType; done
	fi
fi
