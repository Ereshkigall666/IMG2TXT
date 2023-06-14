import os
import sys
import glob
import re
from PyPDF2 import PdfReader
from datetime import datetime
from optparse import OptionParser

def get_parser():
    """Returns a command line parser
    Returns:
        OptionParser. The command line parser
    """
    parser = OptionParser()
    parser.add_option("-c", "--corpus_path", dest="corpus_path",
                      help="""Chemin vers le dossier comprenant les fichiers à océriser [pdf, jpg ..] default : dummy_corpus/""", type="string", default="dummy_corpus/")
    parser.add_option('-o', '--out_html', help='Format sortie html (défaut: txt)', action='store_true', default = False)
    parser.add_option('-k', '--kraken', help='Use Kraken (default : Tesseract)', action='store_true', default = False)
    parser.add_option('-F', '--Force', help='Ré-océriser ce qui est déjà fait', action='store_true', default = False)
    #TODO: ajouter filtrage de l'input (pdf et pas jpg ...)
    return parser

def check_exists(path, outType):
  return os.path.exists(f"{path}.{outType}")

def has_all_ocr(path, inType, outType, engine):
    ext_in = get_extension(inType, in_out='in', engine=engine)
    ext_out = get_extension(outType, in_out='out', engine=engine)
    has_all = False
    #try:
    if 'pdf' in ext_in:
      path_pdfs = glob.glob(f"{path}/*.pdf")
      img = sum([len(PdfReader(open(p,'rb')).pages) for p in path_pdfs])
    else:
      liste_in = glob.glob(f"{path}/*." + ext_in)
      img = len(liste_in)
    #except:
    liste_out = glob.glob(f"{path}/*." + ext_out)
    ocr = len(liste_out)
    if ocr == img:
        has_all = True
    return has_all

def get_extension(docs_a_oceriser):
  out = {"pdf":[], "jpg":[], "jpeg":[], "png":[], "tiff":[], "autres":[]}
  for path in docs_a_oceriser:
    extension = re.split("\.", path)[-1]
    if extension in out.keys():
      out[extension].append(path)
    else:
      out["autres"].append(path)
  print("-"*20)
  for extension, elems in out.items():
    if len(elems)>0:
      print(f"{extension} \t: {len(elems)} files, {elems[0]}...")
  print("-"*20)
  out["Png"]=out["png"]#dfférencier avec pdf
  del out ["png"]
  del out ["autres"]
  for path in out["pdf"]:
    if "_path" not in path:
      #toutes les pages au même endroit
      png_paths = segment_and_move_pdf(path)
      out["Png"]+=png_paths
  return {x:elems for x, elems in out.items() if len(elems)>0}

def segment_and_move_pdf(path):
  print(f"Segmenting {path}")
  new_dir = re.split("/|\.", path)[-2]+"_path"
  new_path = f"{options.corpus_path}/{new_dir}"
  os.makedirs(new_path, exist_ok = True)
  os.system(f"mv {path} {new_path}/")
  pdf_path = glob.glob(f"{new_path}/*.pdf")[0]
  os.system(f"pdftoppm -png {pdf_path} {pdf_path}")
  return glob.glob(f"{new_path}/*.png")

import tqdm
w_log = open("log.txt", "w")
if __name__ == '__main__':
  options, _ = get_parser().parse_args()
  print(options.corpus_path)
  engine  = "kraken" if options.kraken  ==True else "tesseract"
  outType = "html"   if options.out_html==True else "txt"

  engine_corpus_path = f"OCR={engine}_{options.corpus_path}/"
  os.makedirs(engine_corpus_path, exist_ok = True)
  os.system(f"cp -r {options.corpus_path}/* {engine_corpus_path}/") 
  docs_a_oceriser  = glob.glob(f"{engine_corpus_path}/*")
  docs_a_oceriser += glob.glob(f"{engine_corpus_path}/*_path/*.png")
  filtrage_input = get_extension(docs_a_oceriser)
  jobs = []
  for inType, liste_path in filtrage_input.items():
    for path in liste_path:
      if check_exists(path, outType)==False:
        if engine=="kraken":
          if "_bin.png" not in path:
            path_bin = path +"_bin.png"
            if os.path.exists(path_bin)==False:
              print(f"Does not exist: {path_bin}")
              continue
            path = path_bin
        jobs.append(f"./img2txt_light.sh -{inType[0]} -{outType[0]} -{engine[0]} {path}")
      else:
        print(path, "done")
  print(f"{len(jobs)} left to process")
  for job in tqdm.tqdm(jobs):
    os.system(job)
w_log.close()
