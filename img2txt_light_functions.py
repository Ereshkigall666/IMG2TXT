import os
import subprocess
import sys
import venv
#import virtualenv
import glob
import timeit
from multiprocessing import *
from tqdm.auto import tqdm
from pathlib import Path
from typing import Final, Dict, List
import pdf2image
import requests
import zipfile
import configparser
from io import BytesIO

# global constants
INPUT_TYPE_LIST:Final[List] = ["pdf","jpg", "png" "tif"]
OUTPUT_TYPE_LIST:Final[List] = ["txt", "html", "alto"]
ENGINE_DICT:Final[Dict]={"k": "kraken", "t": "tesseract"}
ENGINE_PACKAGES:Final[Dict] = {"k": "kraken", "t": "pytesseract"}
WIN_POPPLER_LINK:Final[str] = "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest"
# convenience variables
venv_kraken_path:str = os.path.join(os.getcwd(), "venv_kraken")
venv_tesseract_path:str = os.path.join(os.getcwd(), "venv_tesseract")
test_dir_path:str = "dummy_corpus"
output_dir_path:str = os.path.join(os.getcwd(), "dummy_corpus_res")
corpus_model_path:str = "./CORPUS17.mlmodel"
benchmark_dir_path:str = os.path.join(os.getcwd(), "benchmarks")




def glob_path_dir(dir_path:str):
    return glob.glob(os.path.join(dir_path, "**", "*"), recursive=True)

def venv_command_wrapper(command:str, arguments:str|list[str], venv_path:str=venv_tesseract_path):
    """wrapper to run python subprocesses using the virtual environment.
    Example: "pip3 install pytesseract opencv-python" -----> venv_command_wrapper(command="pip3", arguments=["install", "pytesseract","opencv-python"], venv_path=venv_tesseract_path)
    Args:
        command (str):command name
        arguments (str | list[str]): the arguments for the command
        venv_path (str, optional): the path to the /bin folder of the current venv. Defaults to venv_tesseract_path.
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
            bin_link = release_data["assets"][0]["browser_download_url"]
            print(bin_link)
        r = requests.get(bin_link)
        with zipfile.ZipFile(file=BytesIO(r.content), mode="r") as zip_ref:
            zip_ref.extractall(path=bin_path)
    #print(glob.glob(os.path.join(bin_path, "**", "bin"), recursive=True))
    return bin_path


def set_up_venv(engine:str="t")->None:
    if engine == "k":
        if not os.path.exists(venv_kraken_path):
            print("Création de l'environement virtuel kraken.")
            #venv.create(env_dir=venv_kraken_path, with_pip=True, symlinks=True, upgrade_deps=True)
            subprocess.run(args=["python", "-m", "virtualenv", "--python=python3.10", venv_kraken_path])
            #install kraken
            print("installing kraken...")
            venv_command_wrapper(command="pip", arguments=["install", "v", "git+https://github.com/mittagessen/kraken.git"], venv_path=venv_kraken_path)
            print("done.")
    else:     
        if not os.path.exists(venv_tesseract_path):
            print("Création de l'environement virtuel tesseract.")
            #venv.create(env_dir=venv_tesseract_path, with_pip=True, symlinks=True, upgrade_deps=True)
            subprocess.run(args=["python", "-m", "virtualenv", venv_tesseract_path])
            #install tesseract
            print("installing tesseract...")
            venv_command_wrapper(command="pip", arguments=["install", "pytesseract","opencv-python"], venv_path=venv_tesseract_path)
            print("done.")
    return


def kraken_binarise_image_file(img_path:str):
        print(img_path)
        print("Binarisation...")
        venv_command_wrapper(command="kraken", arguments=["-i", img_path, img_path, "binarize"],venv_path=venv_kraken_path)
        # Segmentation and ocr
        print(img_path)
        print("Segmentation...")
        venv_command_wrapper(command="kraken", arguments=["-i", img_path, img_path+".txt", "segment", "ocr", "-m", corpus_model_path], venv_path=venv_kraken_path)
        return

def kraken_binarise_image_dir(dir_path:str, multiprocess:bool = True):
    file_list:list = glob.glob(pathname=f"{dir_path}/*.png")
    if multiprocess:
        pool = Pool(processes=len(file_list))
        pool.map(func=kraken_binarise_image_file, iterable=tqdm(file_list))
        pool.close()
        
    else:
        for img_path in tqdm(file_list):
                kraken_binarise_image_file(img_path=img_path)
    return

def tessaract_ocrise_file(filepath:str, output_type:str):
    venv_command_wrapper(command="python", arguments=["tesseract_ocr.py", filepath, output_type])
    return

def tessaract_ocrise_dir(dir_path:str, output_type:str, multiprocess:bool = True):
    if multiprocess:
        file_list:list = [(filepath, output_type) for filepath in glob.glob(pathname=f"{dir_path}/*.png")]
        pool = Pool(processes=len(file_list))
        pool.starmap(tessaract_ocrise_file, file_list)
        pool.close()
    else:
        for img_path in glob.glob(pathname=f"{dir_path}/*.png"):
            venv_command_wrapper(command="python", arguments=["tesseract_ocr.py", img_path, output_type])
    return


def ocrise_file(filepath:str, output_dir_path:str, output_type:str="alto", engine:str="t", dpi:int=200, venv_path:str=venv_tesseract_path, multiprocess: bool = True):
    file_Path = Path(filepath)
    # create one subdirectory for each file
    res_dir_path:str = os.path.join(output_dir_path, f"{ENGINE_DICT[engine]}{venv_get_version_package(package=ENGINE_PACKAGES[engine], venv_path=venv_path)}", file_Path.stem)
    os.makedirs(name=res_dir_path, exist_ok=True)
    print(res_dir_path)
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
    # Binarisation with kraken if kraken
    if engine == "k":
        kraken_binarise_image_dir(dir_path=res_dir_path, multiprocess=multiprocess)
    else:
        tessaract_ocrise_dir(dir_path=res_dir_path, output_type=output_type, multiprocess=multiprocess)
    return

def ocrise_dir(input_dir_path:str, output_dir_path:str, output_type:str="alto", engine:str="t", dpi:int=200, venv_path:str=venv_tesseract_path, multiprocess:bool = True):
    for filepath in tqdm(glob_path_dir(input_dir_path)):
        print(filepath)
        ocrise_file(filepath=filepath, output_dir_path=output_dir_path, output_type=output_type, engine=engine, dpi=dpi, venv_path=venv_path, multiprocess=multiprocess)
    return

def img_to_txt(input_dir_path:str, output_type:str="txt", engine:str="t", output_dir_path:str|None=None, dpi:int =200, multiprocess:bool = True):
    # preliminary steps
    if engine in ENGINE_DICT.values():
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
    ocrise_dir(input_dir_path=input_dir_path, output_dir_path=output_dir_path, output_type=output_type, engine=engine, dpi=dpi, venv_path=venv_path, multiprocess=multiprocess)
    return


# TESTS

def run_benchmark(input_dir_path:str, benchmark_dir_path:str = benchmark_dir_path, engine:str = "t", output_type:str="txt", multiprocess:bool=True, dpi:int=200, number_it:int=1):
    bench_filepath:str = os.path.join(benchmark_dir_path, f"{ENGINE_DICT[engine]}-benchmark.csv")
    if not os.path.exists(bench_filepath):
        os.makedirs(name=os.path.dirname(bench_filepath), exist_ok=True)
        bench_file = open(file=bench_filepath, mode="w")
        bench_file.write("time,multiprocess,output_type,dpi,number_of_files,number_iterations\n")
    else:
        bench_file = open(file=bench_filepath, mode="a")
    time = timeit.timeit(stmt=f"img_to_txt(input_dir_path='{input_dir_path}', output_type='{output_type}', engine='{engine}', dpi={dpi}, multiprocess={multiprocess})", setup="from __main__ import img_to_txt", number=number_it)
    bench_file.write(f"{time/number_it},{multiprocess},{output_type},{dpi},{len(os.listdir(path=input_dir_path))},{number_it}\n")  
    bench_file.close()
    return

if __name__ == "__main__":
    #img_to_txt(input_dir_path=test_dir_path, output_dir_path=None, output_type="alto", engine="t")
    # tesseract
    #run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="txt", multiprocess=True, dpi=200, number_it=5)
    #run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="alto", multiprocess=False, dpi=200, number_it=5)
    # kraken
    #set_up_venv(engine="k")
    #print("----------------------MULTIPROCESS----------------------")
    run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="k", output_type="txt", multiprocess=True, dpi=200, number_it=4)
    #print("----------------------NO MULTIPROCESS----------------------")
    run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="k", output_type="txt", multiprocess=False, dpi=200, number_it=4)
    #other tests
    #download_unzip_binary(binary_name="poppler", bin_link=WIN_POPPLER_LINK, venv_path=venv_tesseract_path)
    #print(venv_get_version_package(package="kraken", venv_path=venv_kraken_path))