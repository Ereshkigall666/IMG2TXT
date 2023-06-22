# IMG2TXT

A simple command line utility to OCRise 17th century French corpora using the Kraken or Tesseract OCR engine. It works on MacOS, Linux, and Windows (it *probably* works on BSD too but was not tested on any BSD system except of course MacOS as previously mentioned).

## Model   

We use the OCR model published by: Simon Gabay, Thibault Clérice, Christian Reul. OCR17: Ground Truth and Models for 17th c. French Prints (and hopefully more). 2020. ⟨hal-02577236⟩
It is available at: https://github.com/e-ditiones/OCR17

## Requirements

- Python >= 3.8 and < 3.11 (if you want to use the Kraken engine: Python3.11 is supported with Tesseract)

- pdf2image==1.16.3
- PyPDF2==3.0.1
- requests==2.28.2
- tqdm==4.64.1
- virtualenv==20.23.0

You can install them all at once (provided you already have a compatible python version installed!) by copy-pasting the following command in a terminal (assuming you cloned the repo to ~/IMG2TXT):

```bash
cd IMG2TXT
pip install -r requirements.txt
```

## How to use it

### Short description  

usage: img2txt_light.py [-h] [-o_fmt {txt,html,alto}] [-o OUTPUT_DIR]
                        [-e {('k', 'kraken'),('t', 'tesseract')}] [-dpi DPI]
                        [-m MULTIPROCESS] [-nc NB_CORE]
                        corpus_path

### Positional arguments

- corpus_path           path to the corpus you want to OCRise.

### options  

- \-h, \-\-help: show this help message and exit    
- \-o_fmt {txt,html,alto}, \-\-output_format {txt,html,alto}: the output format of the OCRised documents. (default:txt)    
-  \-o OUTPUT_DIR, \-\-output_dir OUTPUT_DIR: the directory in which the output files should be put (if you want them to be put in a specific directory).Defaults to a <input_dir>_ocr directory. (default:: None)    
-  \-e {('k', 'kraken'),('t', 'tesseract')}, \-\-engine {('k', 'kraken'),('t', 'tesseract')}:the OCR engine to use. (default: t)    
-  \-dpi DPI: image quality to aim for. (default: 200)   
-  \-m MULTIPROCESS, \-\-multiprocess MULTIPROCESS: whether to multiprocess or not. Multiprocessing is highly recommended as it speeds up the OCRisation process significantly. (default: True)    
-  \-nc NB_CORE, \-\-nb_core NB_CORE: number of cores to use if multiprocessing is used. (default: 3)    
-   \-f, \-\-force, whether to force-OCRise files that are determined to have already been processed. (default: False)

### Examples   

- `python3 img2txt_light.py my_data`: OCRise all the documents in the my_data directory, using default settings (i.e tesseract engine, with multiprocessing, and with txt as the output type)
- `python3 img2txt_light.py my_data -o_fmt html -e kraken`: OCRise all the documents in the my_data directory, using the Kraken engine and outputting the processed files as html files

## Limitations   

Unfortunately, Kraken is not available to Windows users because the Kraken OCR engine itself doesn't support Windows.
