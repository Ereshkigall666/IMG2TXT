import os
import subprocess
import sys
#import runpy

input_type_list:list = ["pdf","jpg", "png" "tif"]
output_type_list:list = ["txt", "html"]
venv_kraken_path:str = os.path.join(os.getcwd(), "venv_kraken")
venv_tesseract_path:str = os.path.join(os.getcwd(), "venv_tesseract")
kraken_activation_path:str = "./venv_kraken/bin/activate"
tesseract_activation_path:str = "./venv_tesseract/bin/activate"
test_dir_path:str = "dummy_corpus/*.pdf"


def pip_wrap(command:str, package:str, options:list = ["-m"]):
    subprocess.check_call([sys.executable, "-m", "pip", command, package])
    return

def install_venv(venv_path:str):
    subprocess.check_call(["python3", "-m", "venv", venv_path])
    return


def set_up_venv(engine:str="t"):
    if engine == "k":
        # make kraken virtual env (to complete)
        if not os.path.exists(venv_kraken_path):
            print("Création de l'environement virtuel pour accueillir Kraken.")
            os.mkdir(venv_kraken_path)
            install_venv(venv_path=venv_kraken_path)
            subprocess.call(["sh", kraken_activation_path])
            print("Environnement virtuel venv_tesseract créé.\n\nTéléchargement de Tesseract.")
            # install kraken
            install_venv(venv_path=venv_kraken_path)
            print("Environement virtuel créé.")
    else:     
        if not os.path.exists(venv_tesseract_path):
            print("Création de l'environement virtuel pour accueillir Tesseract.")
            os.mkdir(venv_tesseract_path)
            install_venv(venv_path=venv_tesseract_path)
            subprocess.call(["sh", tesseract_activation_path])
            print("Environnement virtuel venv_tesseract créé.\n\nTéléchargement de Tesseract.")
            # install tesseract
            install_venv(venv_path=venv_tesseract_path)
            print("Environement virtuel créé.")
    return

def img_to_txt(dir_path:str, input_type:str, output_type:str, engine:str="t"):
    set_up_venv(engine=engine)
    
    return

img_to_txt(dir_path=test_dir_path, input_type="pdf", output_type="txt", engine="t")