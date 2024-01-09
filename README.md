# IMG2TXT

A simple command line utility to OCRise 17th century French corpora using the Kraken or Tesseract OCR engine. It works on MacOS, Linux, and Windows (it *probably* works on BSD too but was not tested on any BSD system except of course MacOS as previously mentioned).

## Model   

We use the OCR model published by: Simon Gabay, Thibault Clérice, Christian Reul. OCR17: Ground Truth and Models for 17th c. French Prints (and hopefully more). 2020. ⟨hal-02577236⟩
It is available at: https://github.com/e-ditiones/OCR17       
Other models can be downloaded and used with the --lang option.    

### Tesseract    

The list of available tesseract models is available here: https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html    


### Kraken    

The list of currently available kraken models is given (here)[https://github.com/Ereshkigall666/IMG2TXT/blob/main/kraken_models.md]; the models in italics are not yet available directly within IMG2TXT.    
## Requirements

### On all systems
- Python >= 3.8 and < 3.11 (if you want to use the Kraken engine: Python3.11 is supported with Tesseract)    
- Tesseract (for the tesseract engine)

### On Ubuntu and Debian-based Linux distributions

- please make sure you have the `distutils` package installed, as it is not packaged in the core python package on these distributions. IMG2TXT will use the latest python version available on your system (i.e, it will look for python3.10 first, if it's not available, for python3.9 etc). Make sure you install the `distutils` package for the appropriate python version that will be used:

#### python3.10

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.10-distutils  
```
#### python3.9

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.9-distutils
```
#### python3.8

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.8-distutils
```

## Hardware support

IMG2TXT should run on most x86-64 computers.

#### Raspberry Pi

#### Pi 4

IMG2TXT can run on a Pi4 and has been tested on one, but it requires some tweaks in the installation process in particular for kraken. The installation may be longer as some packages may need to be installed from source: furthermore, a bug with PyTorch necessitates a specific workaround to get torch to run correctly (see ![issue 97226](https://github.com/pytorch/pytorch/issues/97226)). Built-in support for Pi4s will be added in the coming days.

### Earlier generations

IMG2TXT is currently being tested on older generations. However, please keep in mind that this is a rather CPU-intensive programme; a Pi3 or earlier may not be the best fit for it in terms of power.

## Python dependencies   

- pdf2image==1.16.3
- PyPDF2==3.0.1
- requests==2.28.2
- tqdm==4.64.1
- virtualenv==20.23.0

You can install the latter all at once (provided you already have a compatible python version installed!) by copy-pasting the following command in a terminal (assuming you cloned the repo to ~/IMG2TXT):

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
-  \-nm, \-\-no_multiprocess: disables multiprocessing. Multiprocessing is highly recommended as it speeds up the OCRisation process significantly (default: False)
-  \-nc NB_CORE, \-\-nb_core NB_CORE: number of cores to use if multiprocessing is used. (default: 3)
-  \-f, \-\-force: whether to force-OCRise files that are determined to have already been processed. (default: False)
-  \-t_path TESSERACT_PATH, \-\-tesseract_path TESSERACT_PATH: link to the tesseract binary path (useful if it is installed in an unusual location and not in your PATH). (default: None)
-  \-l LANG, \-\-lang LANG:  specify the language model to use for OCRisation. Possible values: dict_keys(['eng', 'fra-lectaurep', 'fra']) (default: None)
-  \-k, \-\-keep_png: whether to png artifacts or not. (default: False)      

### Examples   

- `python3 img2txt_light.py my_data`: OCRise all the documents in the my_data directory, using default settings (i.e tesseract engine, with multiprocessing, and with txt as the output type)
- `python3 img2txt_light.py my_data -o_fmt html -e kraken`: OCRise all the documents in the my_data directory, using the Kraken engine and outputting the processed files as html files

### Note

The default language model used for Tesseract is the French one at the moment since this was our use case; a command line option to pick the language to use will be added shortly.

## Limitations   

Unfortunately, Kraken is not available to Windows users because the Kraken OCR engine itself doesn't support Windows.
