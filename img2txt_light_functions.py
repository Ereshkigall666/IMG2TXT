import os
import subprocess
import sys
#import venv
#import virtualenv
import glob
import tempfile
import timeit
from multiprocessing import *
from tqdm.auto import tqdm
from pathlib import Path
from typing import Final, Dict, List, Union
from shutil import copy
import pdf2image
from PIL import Image
import requests
import zipfile
from git import Repo
import configparser
from io import BytesIO

# disable max size limit for images
Image.MAX_IMAGE_PIXELS = None

# global constants
INPUT_TYPE_LIST:Final[List] = ["pdf","jpg", "jpeg", "png" "tif"]
OUTPUT_TYPE_LIST:Final[List] = ["txt", "html", "alto"]
ENGINE_DICT:Final[Dict]={"k": "kraken", "t": "tesseract"}
ENGINE_PACKAGES:Final[Dict] = {"k": "kraken", "t": "pytesseract"}
WIN_POPPLER_LINK:Final[str] = "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest"
#PY_VERSION_LIST:Final[List] = [10, 9, 8]
PY_VERSION_LIST:list = [10, 9, 8]
WIN_TESSERACT_LINK:Final[str] = "https://api.github.com/repos/UB-Mannheim/tesseract/releases/latest"
TESSERACT_INSTALL_LINK:Final[str] = "https://tesseract-ocr.github.io/tessdoc/Installation.html"
WIN_TESSERACT_EXE_PATH:Final[str] = "C:\Program Files\Tesseract-OCR\\tesseract.exe"
KRAKEN_GIT_PATH:Final[str] = "https://github.com/mittagessen/kraken.git"
# convenience variables
venv_kraken_path:str = os.path.join(os.getcwd(), "venv_kraken")
venv_tesseract_path:str = os.path.join(os.getcwd(), "venv_tesseract")
test_dir_path:str = "dummy_corpus"
output_dir_path:str = os.path.join(os.getcwd(), "dummy_corpus_res")
corpus_model_path:str = "./CORPUS17.mlmodel"
benchmark_dir_path:str = os.path.join(os.getcwd(), "benchmarks")




def glob_path_dir(dir_path:str):
    return glob.glob(os.path.join(dir_path, "**", "*"), recursive=True)

def venv_command_wrapper(command:str, arguments:Union[str, list[str]], venv_path:str=venv_tesseract_path):
    """_wrapper to run python subprocesses using the virtual environment.
    Example: "pip3 install pytesseract opencv-python" -----> venv_command_wrapper(command="pip3", arguments=["install", "pytesseract","opencv-python"], venv_path=venv_tesseract_path)
    Args:
        command (str):command name
        arguments (str | list[str]): the arguments for the command
        venv_path (str, optional): the path to the /bin folder of the current venv. Defaults to venv_tesseract_path.
    Returns:
        _CompletedProcess_: _the CompletedProcess object created_
    """
    bin_dir_name:str = "bin" if not sys.platform.startswith("win") else "Scripts"
    if isinstance(arguments, list):
        arguments.insert(0, os.path.join(venv_path, bin_dir_name, command))
        res = subprocess.run(args=arguments, capture_output=True, text=True)
        
    else:
        res = subprocess.run(args=[os.path.join(venv_path, bin_dir_name, command), arguments], capture_output=True, text=True)
    return res


def venv_get_version_package(package:str, venv_path:str=venv_tesseract_path):
    res = venv_command_wrapper(command="pip", arguments=["show", package], venv_path=venv_path)
    # parse output
    package_config = configparser.ConfigParser()
    # add header to avoid MissingSectionHeaderError exception
    package_cfg_str:str = "[default]\n" + res.stdout
    package_config.read_string(package_cfg_str)
    cfg = package_config["default"]
    if "Version" in cfg:
        return cfg["Version"]
    return None

def download_unzip_binary(binary_name:str, bin_link:str, venv_path:str = venv_tesseract_path, github_api:bool = True, force:bool = False)->str:
    """Fetches compressed binaries and downloads them to <venv_path>/<other_bin>
    Args:
        binary_name (str): the name under which the binary will be downloaded. Can end up being either a file or a directory depending on what the specific binary is like.
        bin_link (str, optional): the link to the binary to download.
        venv_path (str, optional): [description]. Defaults to venv_tesseract_path. Path to the virtual environment currently used. 
    """
    bin_path:str =  os.path.join(venv_path, "other_bin", binary_name)
    if os.path.exists(bin_path):
        print("already installed")
    else:
        if github_api:
            release_data = requests.get(bin_link).json()
            if bin_link == WIN_POPPLER_LINK:
                bin_link = release_data["assets"][0]["browser_download_url"]
                print(bin_link)
            elif bin_link == WIN_TESSERACT_LINK:
                bin_link = release_data["zipball_url"]
                
        r = requests.get(bin_link)
        with zipfile.ZipFile(file=BytesIO(r.content), mode="r") as zip_ref:
            zip_ref.extractall(path=bin_path)
    #print(glob.glob(os.path.join(bin_path, "**", "bin"), recursive=True))
    return bin_path


def set_up_venv(engine:str="t")->None:
    cache_dir_path:str = ""
    if engine == "k":
        if not os.path.exists(venv_kraken_path):
            print("Création de l'environement virtuel kraken.")
            cache_dir_path = os.path.join(venv_kraken_path, "tmp")
            #venv.create(env_dir=venv_kraken_path, with_pip=True, symlinks=True, upgrade_deps=True)
            # try to create venv with any of the supported python versions if they're present on the system
            for version_num in PY_VERSION_LIST:
                sub_process=subprocess.run(args=["python", "-m", "virtualenv", f"--python=python3.{version_num}", venv_kraken_path])
                if sub_process.returncode == 0:
                    break
            else:
                print("it seems that there is no supported version of python installed on this computer. Please install python3.10.")
                return
            #install kraken
            print("installing kraken...")
            res = venv_command_wrapper(command="pip", arguments=["install", f"--cache-dir={cache_dir_path}", "v", f"git+{KRAKEN_GIT_PATH}"], venv_path=venv_kraken_path)
            print(res.stdout)
            print(res.stderr)
            if res.returncode != 0:
                print("it seems like the installation failed; trying an alternative method.")
                Repo.clone_from(KRAKEN_GIT_PATH, cache_dir_path)
                res = venv_command_wrapper(command="pip", arguments=["install", cache_dir_path] )
                if res.returncode != 0:
                    print("it seems the installation failed.")
                    print(res.stderr)
                    exit()
            print("done.")
    else:     
        if not os.path.exists(venv_tesseract_path):
            print("Création de l'environement virtuel tesseract.")
            cache_dir_path = os.path.join(venv_tesseract_path, "tmp")
            #venv.create(env_dir=venv_tesseract_path, with_pip=True, symlinks=True, upgrade_deps=True)
            subprocess.run(args=["python", "-m", "virtualenv", venv_tesseract_path])
            #install tesseract
            print("installing pytesseract...")
            res = venv_command_wrapper(command="pip", arguments=["install", f"--cache-dir={cache_dir_path}", "pytesseract","opencv-python"], venv_path=venv_tesseract_path)
            print(res.stdout)
            print("done.")
    return

def find_tesseract_path()->str:
    tesseract_path:str = ""
    if not sys.platform.startswith("win"):
        res = subprocess.run(args=["which", "tesseract"], capture_output=True, text=True)
        which_out:str = res.stdout.strip()
        if not os.path.exists(os.path.realpath(which_out)) or res.returncode != 0:
            print(f"it looks like tesseract is not installed on this system.Please install it at: {TESSERACT_INSTALL_LINK}. If it is installed, it may simply not be in your PATH.")
            sys.exit()
        else:
            tesseract_path = os.path.realpath(which_out)

    else:
        tesseract_path = WIN_TESSERACT_EXE_PATH
        if not os.path.exists(tesseract_path):
            print(f"it looks like tesseract is not installed on this system. Please install it at: {TESSERACT_INSTALL_LINK}.  If it is installed, it may simply not be in your PATH.")
            sys.exit()
    return tesseract_path


def kraken_binarise_image_file(img_path:str, output_type:str="txt", force:bool = False):
        print(img_path)
        out_img_path:str = f"{os.path.join(os.path.dirname(img_path), f'{Path(img_path).stem}.{output_type}')}"
        if os.path.exists(out_img_path) and not force:
            print("this file has already been processed before.")
            return
        print("Binarisation...")
        venv_command_wrapper(command="kraken", arguments=["-i", img_path, img_path, "binarize"],venv_path=venv_kraken_path)
        # Segmentation and ocr
        print(img_path)
        print("Segmentation...")
        venv_command_wrapper(command="kraken", arguments=["-i", img_path, out_img_path, "-o", output_type,  "segment", "ocr", "-m", corpus_model_path], venv_path=venv_kraken_path)
        return

def kraken_binarise_image_dir(dir_path:str, output_type:str="txt", multiprocess:bool = True, nb_core:int = 3, force:bool = False):
    file_list:list = glob.glob(pathname=os.path.join(dir_path, "**", "*.png"), recursive=True)
    for ext in INPUT_TYPE_LIST:
        if ext != "png" and ext != "pdf":
            file_list.extend(glob.glob(pathname=os.path.join(dir_path, "**", ext), recursive=True))
    if multiprocess:
        file_list = [(filepath, output_type, force) for filepath in file_list]
        pool = Pool(processes=nb_core)
        pool.starmap(func=kraken_binarise_image_file, iterable=tqdm(file_list))
        pool.close()
        
    else:
        for img_path in tqdm(file_list):
                kraken_binarise_image_file(img_path=img_path, output_type=output_type, force=force)
    return

def tessaract_ocrise_file(filepath:str, output_type:str, force:bool = False, lang:str="fra", tesseract_path=None):
    if tesseract_path is None:
        tesseract_path = find_tesseract_path()
    print("OCRisation with Tesseract...")
    res = venv_command_wrapper(command="python", arguments=["tesseract_ocr.py", filepath, output_type, str(force), lang, tesseract_path])
    print(res.stdout)
    if res.stderr != "":
        print(f"-------------ERROR-------------\n{res.stderr}")
    return

def tessaract_ocrise_dir(dir_path:str, output_type:str, multiprocess:bool = True, nb_core:int = 3, force:bool = False, lang:str="fra", tesseract_path=None):
    if tesseract_path is None:
        tesseract_path = find_tesseract_path()
        print(tesseract_path)
    file_list:list = glob.glob(pathname=f"{dir_path}/*.png")
    for ext in INPUT_TYPE_LIST:
        if ext != "png" and ext != "pdf":
            file_list.extend(glob.glob(pathname=f"{dir_path}/*.{ext}"))
    if multiprocess:
        file_list = [(filepath, output_type, force, lang, tesseract_path) for filepath in file_list]
        pool = Pool(processes=nb_core)
        pool.starmap(tessaract_ocrise_file, file_list)
        pool.close()
    else:
        for img_path in file_list:
            tessaract_ocrise_file(filepath=img_path, output_type=output_type, force=force, tesseract_path=tesseract_path)
    return


def ocrise_file(filepath:str, output_dir_path:str, output_type:str="alto", engine:str="t", dpi:int=200, venv_path:str=venv_tesseract_path, multiprocess: bool = True, nb_core:int = 3, force: bool=False, tesseract_path=None):
    file_Path = Path(filepath)
    # create one subdirectory for each file
    res_dir_path:str = os.path.join(output_dir_path, f"{ENGINE_DICT[engine]}{venv_get_version_package(package=ENGINE_PACKAGES[engine], venv_path=venv_path)}", file_Path.stem)
    os.makedirs(name=res_dir_path, exist_ok=True)
    #print(res_dir_path)
    # split file into image pages
    if filepath.endswith("pdf"):
        poppler_bin_path = None
        # install poppler in the virtual environment on windows
        if sys.platform.startswith("win"):
            poppler_path = download_unzip_binary(binary_name="poppler", bin_link=WIN_POPPLER_LINK, venv_path=venv_path)
            # retrieve the poppler-xx/bin path
            poppler_bin_path = glob.glob(os.path.join(poppler_path, "**", "bin"), recursive=True)[0]
        print("splitting into images")
        pdf2image.convert_from_path(pdf_path=filepath, output_folder=res_dir_path, fmt="png", output_file=file_Path.stem, dpi=dpi, poppler_path=poppler_bin_path) #type: ignore
    else:
        (Image.open(filepath)).save(os.path.join(res_dir_path, f"{file_Path.stem}.png"))
        #copy(src=filepath, dst=os.path.join(res_dir_path, os.path.basename(filepath)))
        
    # Binarisation with kraken if kraken
    if engine == "k":
        kraken_binarise_image_dir(dir_path=res_dir_path, output_type=output_type, multiprocess=multiprocess, nb_core=nb_core, force=force)
    else:
        tessaract_ocrise_dir(dir_path=res_dir_path, output_type=output_type, multiprocess=multiprocess, nb_core=nb_core, force=force)
    return

def ocrise_dir(input_dir_path:str, output_dir_path:str, output_type:str="alto", engine:str="t", dpi:int=200, venv_path:str=venv_tesseract_path, multiprocess:bool = True, nb_core:int = 3, force:bool = False, tesseract_path=None):
    for filepath in tqdm(glob_path_dir(input_dir_path)):
        print(filepath)
        ocrise_file(filepath=filepath, output_dir_path=output_dir_path, output_type=output_type, engine=engine, dpi=dpi, venv_path=venv_path, multiprocess=multiprocess, nb_core=3, force=force, tesseract_path=tesseract_path)
        # remove pngs
        png_file_list:list = glob.glob(os.path.join(output_dir_path, "**", "*.png"), recursive=True)
        for png_file in png_file_list:
            os.remove(png_file)
    return

def img_to_txt(input_dir_path:str, output_type:str="txt", engine:str="t", output_dir_path:Union[str, None]=None, dpi:int =200, multiprocess:bool = True, nb_core:int = 3, force: bool = False, tesseract_path=None):
    # preliminary steps
    if engine.lower() in ENGINE_DICT.values():
        for key in ENGINE_DICT:
            if ENGINE_DICT[key] == engine:
                engine = key
                break
    if output_dir_path is None:
        output_dir_path = os.path.join(os.path.dirname(input_dir_path), f"{Path(input_dir_path).stem}_ocr")
    if sys.platform.startswith("win") and engine == "k":
        print("Unfortunately, Windows is not supported on kraken. Defaulting to tesseract.")
        engine = "t"
    # actual script
    #set up virtual environment
    venv_path:str = venv_kraken_path if engine == "k" else venv_tesseract_path 
    set_up_venv(engine=engine)
    ocrise_dir(input_dir_path=input_dir_path, output_dir_path=output_dir_path, output_type=output_type, engine=engine, dpi=dpi, venv_path=venv_path, multiprocess=multiprocess, nb_core=nb_core, force=force, tesseract_path=tesseract_path)
    return


# TESTS

def run_benchmark(input_dir_path:str, benchmark_dir_path:str = benchmark_dir_path, engine:str = "t", output_type:str="txt", multiprocess:bool=True, dpi:int=200, number_it:int=1, nb_core:int = 3):
    bench_filepath:str = os.path.join(benchmark_dir_path, f"{ENGINE_DICT[engine]}-benchmark.csv")
    if not os.path.exists(bench_filepath):
        os.makedirs(name=os.path.dirname(bench_filepath), exist_ok=True)
        bench_file = open(file=bench_filepath, mode="w")
        bench_file.write("time,multiprocess,output_type,dpi,number_of_files,number_iterations,nb_core\n")
    else:
        bench_file = open(file=bench_filepath, mode="a")
    time = timeit.timeit(stmt=f"img_to_txt(input_dir_path='{input_dir_path}', output_type='{output_type}', engine='{engine}', dpi={dpi}, multiprocess={multiprocess}, nb_core={nb_core})", setup="from __main__ import img_to_txt", number=number_it)
    if multiprocess:
        bench_file.write(f"{time/number_it},{multiprocess},{output_type},{dpi},{len(os.listdir(path=input_dir_path))},{number_it},{nb_core}\n")
    else:
        bench_file.write(f"{time/number_it},{multiprocess},{output_type},{dpi},{len(os.listdir(path=input_dir_path))},{number_it},{None}\n")
    bench_file.close()
    return

if __name__ == "__main__":
    #img_to_txt(input_dir_path=test_dir_path, output_dir_path=None, output_type="alto", engine="t")
    # tesseract
    #run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="txt", multiprocess=True, dpi=200, number_it=5)
    #run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="alto", multiprocess=False, dpi=200, number_it=5)
    # kraken
    set_up_venv(engine="k")
    #print("----------------------MULTIPROCESS----------------------")
    #run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="html", multiprocess=True, dpi=200, number_it=1, nb_core=3)
    #print("----------------------NO MULTIPROCESS----------------------")
    #run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="html", multiprocess=False, dpi=200, number_it=1, nb_core=3)
    #other tests
    #download_unzip_binary(binary_name="poppler", bin_link=WIN_POPPLER_LINK, venv_path=venv_tesseract_path)
    #print(venv_get_version_package(package="kraken", venv_path=venv_kraken_path))
    #ocrise_file(filepath="../../Antonomaz/Glane5_process/Glane5-sample/BM01481_MAZ.jpg", output_dir_path="../../Antonomaz/Glane5_process/Glane5-sample_ocr/", engine="k", output_type="txt", venv_path=venv_kraken_path, force=True)