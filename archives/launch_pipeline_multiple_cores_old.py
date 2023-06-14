import os
import sys
import glob
import re
#TODO: use PdfReader
from PyPDF2 import PdfReader
from datetime import datetime

def get_extension(t, in_out, engine):
    if t == '-p': return 'pdf'
    elif t == '-j': return 'jp*g'
    elif t == '-P': return 'png'
    elif t == '-t': 
        if in_out == 'in': return 'tif'
        else: return 'txt'
    elif t == '-h':
        if engine == '-t': return 'alto'
        else: return 'html'
    else: return 'x'

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

w_log = open("log.txt", "w")
if __name__ == '__main__':
    #TODO: add messages
    if len(sys.argv) > 4:
        inType = sys.argv[1]
        outType = sys.argv[2]
        engine = sys.argv[3]
        paths = sys.argv[4:]
        print(paths)
        if len(paths)==1:
          path = paths[0]
          for file_path in glob.glob(f"{path}*.pdf"):
            newdir = re.sub(".pdf", "_path", file_path)
            os.makedirs(newdir, exist_ok=True)
            os.system(f"mv {file_path} {newdir}/")
          paths = glob.glob(f"{path}/*path")
          print(paths)
        path_status = [[path, has_all_ocr(path, inType, outType, engine)] for path in paths]
        paths  = [path for path, status in path_status if status ==False]
        errors = [path for path, status in path_status if status =="Error"]
        print("NB errors:", len(errors))
        w_log.write("ERROR_pdf:"+"\nERROR_pdf:".join(errors))
        i = 0
        NB_core = 3
        while i < len(paths):
            batch = paths[i:i+NB_core]
            print(batch)
            now = datetime.now()
            for b in batch:
              w_log.write(f"{now}:{b}\n")
            list_cmd = ["./img2txt.sh " + inType + " " + outType + " " + engine + " %s/" % path for path in batch]
            cmd = " & ".join(list_cmd)
            os.system(cmd)
            i += NB_core
    else:
        print("You must give 4 arguments.\n",
            "1: -p (PDF) or -j (JPG) or -P (PNG) or -t (TIF)\n",
            "2: -t (TXT) or -h (HTML or XML-alto)\n",
            "3: -k (Kraken), -t (Tesseract)\n",
            "4: paths to your data (intension paths, with *\n"
            )
w_log.close()
