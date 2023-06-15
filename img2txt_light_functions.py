import os
import subprocess
import sys
import venv
#import virtualenv
import glob
from tqdm.auto import tqdm
from pathlib import Path
from typing import Final, Dict, List
import pdf2image

# global constants
INPUT_TYPE_LIST:Final[List] = ["pdf","jpg", "png" "tif"]
OUTPUT_TYPE_LIST:Final[List] = ["txt", "html", "alto"]
ENGINE_DICT:Final[Dict]={"k": "kraken", "t": "tesseract"}

# convenience variables
venv_kraken_path:str = os.path.join(os.getcwd(), "venv_kraken")
venv_tesseract_path:str = os.path.join(os.getcwd(), "venv_tesseract")
test_dir_path:str = "dummy_corpus"
output_dir_path:str = os.path.join(os.getcwd(), "dummy_corpus_res")
corpus_model_path:str = "./CORPUS17.mlmodel"

def glob_path_dir(dir_path:str):
    return glob.glob(os.path.join(dir_path, "**", "*"), recursive=True)

def venv_command_wrapper(command:str, arguments:str|list[str], venv_path:str=venv_tesseract_path)->None:
    """wrapper to run python subprocesses using the virtual environment.
    Example: "pip3 install pytesseract opencv-python" -----> venv_command_wrapper(command="pip3", arguments=["install", "pytesseract","opencv-python"], venv_path=venv_tesseract_path)
    Args:
        command (str):command name
        arguments (str | list[str]): the arguments for the command
        venv_path (str, optional): the path to the /bin folder of the current venv. Defaults to venv_tesseract_path.
    """
    if isinstance(arguments, list):
        arguments.insert(0, os.path.join(venv_path, "bin", command))
        subprocess.run(args=arguments)
        
    else:
        subprocess.run([os.path.join(venv_path, "bin", command), arguments])
    return


def set_up_venv(engine:str="t")->None:
    if engine == "k":
        if not os.path.exists(venv_kraken_path):
            print("Création de l'environement virtuel kraken.")
            #venv.create(env_dir=venv_kraken_path, with_pip=True, symlinks=True, upgrade_deps=True)
            subprocess.run(args=["virtualenv", "--python=python3.10", venv_kraken_path])
            #install kraken
            venv_command_wrapper(command="pip3", arguments=["install","git+https://github.com/mittagessen/kraken.git"], venv_path=venv_kraken_path)
    else:     
        if not os.path.exists(venv_tesseract_path):
            print("Création de l'environement virtuel tesseract.")
            venv.create(env_dir=venv_tesseract_path, with_pip=True, symlinks=True, upgrade_deps=True)
            #install tesseract
            venv_command_wrapper(command="pip3", arguments=["install", "pytesseract","opencv-python"], venv_path=venv_tesseract_path)
    return

def ocrise_text(input_dir_path:str, output_dir_path:str, output_type:str="alto", engine:str="t"):
    for filepath in tqdm(glob_path_dir(input_dir_path)):
        print(filepath)
        file_Path = Path(filepath)
        # create one subdirectory for each file
        res_dir_path:str = os.path.join(output_dir_path, ENGINE_DICT[engine], file_Path.stem)
        os.makedirs(name=res_dir_path, exist_ok=True)
        #print(res_dir_path)
        # split file into image pages
        if filepath.endswith("pdf"):
            pdf2image.convert_from_path(pdf_path=filepath, output_folder=res_dir_path, fmt="png", output_file=file_Path.stem)
        # Binarisation with kraken if kraken
        if engine == "k":
            for img_path in glob.glob(pathname=f"{res_dir_path}/*.png"):
                venv_command_wrapper(command="kraken", arguments=["-i", img_path, img_path, "binarize"], venv_path=venv_kraken_path)
            # Segmentation and ocr
                venv_command_wrapper(command="kraken", arguments=["-i", img_path, img_path+".txt", "segment", "ocr", "-m", corpus_model_path], venv_path=venv_kraken_path)
        else:
            for img_path in glob.glob(pathname=f"{res_dir_path}/*.png"):
                venv_command_wrapper(command="python3", arguments=["tesseract_ocr.py", img_path, output_type])
    return

def img_to_txt(input_dir_path:str, output_type:str="txt", engine:str="t", output_dir_path:str|None=None):
    if engine in ENGINE_DICT.values():
        for key in ENGINE_DICT:
            if ENGINE_DICT[key] == engine:
                engine = key
                break
    if output_dir_path is None:
        output_dir_path = os.path.join(os.path.dirname(input_dir_path), f"{Path(input_dir_path).stem}_ocr")
    set_up_venv(engine=engine)
    ocrise_text(input_dir_path=input_dir_path, output_dir_path=output_dir_path, output_type=output_type, engine=engine)
    return

if __name__ == "__main__":
    img_to_txt(input_dir_path=test_dir_path, output_dir_path=None, output_type="alto", engine="t")