import os
import subprocess
import sys
import venv
import glob
from tqdm.auto import tqdm
#import tesseract
#import kraken
from pathlib import Path
import pdf2image

input_type_list:list = ["pdf","jpg", "png" "tif"]
output_type_list:list = ["txt", "html"]
venv_kraken_path:str = os.path.join(os.getcwd(), "venv_kraken")
venv_tesseract_path:str = os.path.join(os.getcwd(), "venv_tesseract")
test_dir_path:str = "dummy_corpus/*.pdf"
output_dir_path:str = os.path.join(os.getcwd(), "dummy_corpus_res")

def venv_command_wrapper(command:str, arguments:str|list[str], venv_path:str=venv_tesseract_path):
    if isinstance(arguments, list):
        arguments.insert(0, os.path.join(venv_path, "bin", command))
        subprocess.run(args=arguments)
        
    else:
        subprocess.run([os.path.join(venv_path, "bin", command), arguments])
    return


def set_up_venv(engine:str="t"):
    if engine == "k":
        if not os.path.exists(venv_kraken_path):
            print("Création de l'environement virtuel kraken.")
            venv.create(env_dir=venv_kraken_path, with_pip=True, symlinks=True)
            #install kraken
            venv_command_wrapper(command="pip3", arguments=["install","kraken"], venv_path=venv_kraken_path)
    else:     
        if not os.path.exists(venv_tesseract_path):
            print("Création de l'environement virtuel tesseract.")
            venv.create(env_dir=venv_tesseract_path, with_pip=True)
            #install tesseract
            venv_command_wrapper(command="pip3", arguments=["install", "pytesseract","opencv-python"], venv_path=venv_tesseract_path)
    return

def ocrisation_text(input_dir_path:str, output_dir_path:str, input_type: str, output_type:str, engine:str):
    for filepath in tqdm(glob.glob(input_dir_path)):
        file_Path = Path(filepath)
        # create one subdirectory for each file
        res_dir_path:str = os.path.join(output_dir_path, file_Path.stem)
        os.makedirs(name=res_dir_path, exist_ok=True)
        #print(res_dir_path)
        # split file into image pages
        if filepath.endswith("pdf"):
            pdf2image.convert_from_path(pdf_path=filepath, output_folder=res_dir_path, fmt="png", output_file=file_Path.stem)

        # Binarisation with kraken if kraken
        if engine == "k":
            venv_command_wrapper(command="kraken", arguments=["-i", output_dir_path, output_dir_path+"_bin.png", "binarize"], venv_path=venv_kraken_path)
        #subprocess.run('timeout 600 kraken -i $dir_path $dir_path"_bin.png" binarize')
    return

def img_to_txt(input_dir_path:str, output_dir_path:str, input_type:str, output_type:str, engine:str="t"):
    set_up_venv(engine=engine)
    ocrisation_text(input_dir_path=input_dir_path, output_dir_path=output_dir_path, input_type=input_type, output_type=output_type, engine=engine)
    return

img_to_txt(input_dir_path=test_dir_path, output_dir_path=output_dir_path, input_type="pdf", output_type="txt", engine="k")
