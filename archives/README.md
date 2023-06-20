# IMG2TXT

A short shell script and Python wrapper to process OCR for XVIIth century french textual data using kraken and compare with Tesseract. 

## Model
We use the OCR model published by: Simon Gabay, Thibault Clérice, Christian Reul. OCR17: Ground Truth and Models for 17th c. French Prints (and hopefully more). 2020. ⟨hal-02577236⟩
It is available at: https://github.com/e-ditiones/OCR17

## Needed 
- python3
- virtualenv
- pdftoppm library
- PyPDF2

You can install all at once using the install.sh script :

chmod +x install.sh

./install.sh

## How to use (new version)?
Usage: launch_pipeline_multiple_cores.py [options]

### Options:
- ```-c```  --corpus_path=    Dossier comprenant les fichiers à océriser [pdf, jpg..] default: dummy_data/
- ```-o``` --out_html        passer le format de sortie en html (default: txt)
- ```-k``` --kraken          Océriser avec Kraken (default : Tesseract)
- ```-F``` --Force           Ré-océriser ce qui a déjà été fait

## How to use (old version)?

Launch the script launch_pipeline_multiple_cores_old.py with the following arguments :

### Argument 1
- ```-p```: PDFs in ```./data/```
- ```-P```: PNGs in ```./data/```
- ```-j```: JPGs in ```./data/```
- ```-t```: TIFFs in ```./data/```

### Argument 2
- ```-t```: TXT format as output
- ```-h```: HTML format as output

### Argument 3
- ```-k```: Kraken
- ```-t```: Tesseract

### Argument 4
Paths to the directories where images are stored.
Ex.: ```./data/*/jpg/``` the ```*``` means all the directories in ./data/ that has got a jpg/ directory in it.



### Examples
- ```python3 launch_pipeline_multiple_cores_old.py -p -t -k ./data/*/pdf/ ```: OCR is processed with Kraken on PDF documents stored in ```./data/*/pdf/``` directories and the output is in TXT format
- ```python3 launch_pipeline_multiple_cores_old.py -j -h -t ./data/*/jpg/```: OCR is processed with Tesseract on JPG documents stored in ```./data/*/jpg/``` directories and the output is in HTML format
