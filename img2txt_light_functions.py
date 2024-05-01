# import os
# import platform
from datetime import date, datetime
import subprocess
import sys
import logging
import glob
import timeit
from multiprocessing import *
from multiprocessing.pool import ThreadPool
from tqdm.auto import tqdm
from pathlib import Path
from typing import Final, Dict, List, Union
from shutil import copy, rmtree
import pdf2image
from PIL import Image
import requests
import zipfile
from git import Repo
import configparser
from io import BytesIO
from img2txt_light_utils import *
from tesseract_utils import *
from kraken_utils import *
from constants import *

# disable max size limit for images
Image.MAX_IMAGE_PIXELS = None


def venv_command_wrapper(command: str, arguments: Union[str, list[str]], venv_path: str = venv_tesseract_path, stream_output: bool = False, log_name: str = f"{date.today()}-log.txt", log_mode: str = "w"):
    """_wrapper to run python subprocesses using the virtual environment.
    Example: "pip3 install pytesseract opencv-python" -----> venv_command_wrapper(command="pip3", arguments=["install", "pytesseract","opencv-python"], venv_path=venv_tesseract_path)
    Args:
        command (str): _description_
        arguments (Union[str, list[str]]): _description_
        venv_path (str, optional): _description_. Defaults to venv_tesseract_path.
        stream_output (bool, optional): whether to stream output to terminal or not. If set, also writes to log file. Defaults to False.
        log_name (str, optional): _description_. Defaults to f"{date.today()}-log.txt".
        log_mode (str, optional): _description_. Defaults to "w".

    Returns:
        _type_: _description_
    """
    # setting up log files
    logger = logging.getLogger(__name__)
    logger.addHandler(fh := logging.FileHandler(
        filename=log_name, mode=log_mode, encoding="utf-8", delay=True))
    # MUST BE SET /!\ or the FileHandler won't be created at all
    logger.setLevel(logging.DEBUG)
    bin_dir_name: str = "bin" if not sys.platform.startswith(
        "win") else "Scripts"
    if stream_output:
        print("streaming output")
        if isinstance(arguments, list):
            logger.info(f"**********{command} {' '.join(arguments)}**********")
            arguments.insert(0, os.path.join(venv_path, bin_dir_name, command))
            process = subprocess.Popen(arguments, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8")
        else:
            logger.info(f"**********{command} {arguments}**********")
            process = subprocess.Popen([os.path.join(venv_path, bin_dir_name, command), arguments],
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8")
        while process.poll() is None:
            stdout_line = process.stdout.readline()  # type: ignore
            logger.debug(stdout_line)
            fh.flush()
            print(stdout_line, flush=True)
        return process
    else:
        if isinstance(arguments, list):
            arguments.insert(0, os.path.join(venv_path, bin_dir_name, command))
            res = subprocess.run(
                args=arguments, capture_output=True, text=True)
        else:
            res = subprocess.run(args=[os.path.join(
                venv_path, bin_dir_name, command), arguments], capture_output=True, text=True)
        return res


def venv_get_version_package(package: str, venv_path: str = venv_tesseract_path):
    res = venv_command_wrapper(command="pip", arguments=[
                               "show", package], venv_path=venv_path)
    # parse output
    package_config = configparser.ConfigParser()
    # add header to avoid MissingSectionHeaderError exception
    package_cfg_str: str = "[default]\n" + res.stdout
    package_config.read_string(package_cfg_str)
    cfg = package_config["default"]
    if "Version" in cfg:
        return cfg["Version"]
    return None


def set_up_venv(engine: str = "t", kraken_version: Union[None, str] = None, force: bool = False) -> None:
    cache_dir_path: str = ""
    python_path: str = sys.executable
    kraken_git_path: str = KRAKEN_GIT_PATH
    if engine == "k":
        if ((not os.path.exists(venv_kraken_path)) or force):
            print("Création de l'environement virtuel kraken.")
            if kraken_version is not None:
                kraken_commit = KRAKEN_VERSIONS[kraken_version]
                kraken_git_path = f"https://github.com/mittagessen/kraken.git@{kraken_commit}"
            print(kraken_git_path)
            cache_dir_path = os.path.join(venv_kraken_path, "tmp")
            log_name: str = os.path.join(SCRIPT_DIR,
                                         "logs", f"kraken_install_log_{date.today()}.txt")
            # try to create venv with any of the supported python versions if they're present on the system
            for version_num in PY_VERSION_LIST:
                sub_process = subprocess.run(
                    args=[python_path, "-m", "virtualenv", f"--python=python3.{version_num}", venv_kraken_path])
                if sub_process.returncode == 0:
                    break
            else:
                print(
                    "it seems that there is no supported version of python installed on this computer. Please install python3.10.")
                return
            # install kraken
            print("installing kraken...")
            print("kraken...")
            res_args: list = [
                "install", f"--cache-dir={cache_dir_path}", "-vvv", "--debug", f"git+{kraken_git_path}"]
            if platform.machine().endswith("armv7l"):
                res_args.append("--extra-index-url")
                res_args.extend(PIP_EXTRA_REPOS)
            res = venv_command_wrapper(command="pip", arguments=res_args,
                                       venv_path=venv_kraken_path, stream_output=True, log_mode="w", log_name=log_name)
            if KRAKEN_SENSITIVE_PACKAGES != []:
                print("installing version sensitive packages...")
                package_arguments: list = [
                    "install", f"--cache-dir={cache_dir_path}", "--force-reinstall", "-v"]
                package_arguments.extend(KRAKEN_SENSITIVE_PACKAGES)
                if platform.machine().endswith("armv7l"):
                    res_args.append("--extra-index-url")
                    res_args.extend(PIP_EXTRA_REPOS)
                package_res = venv_command_wrapper(command="pip", arguments=package_arguments,
                                                   venv_path=venv_kraken_path, stream_output=True, log_mode="a", log_name=log_name)
            if res.returncode != 0:
                print(
                    "it seems like the installation failed; trying an alternative method.")
                kraken_tmpdir_path: str = os.path.join(
                    cache_dir_path, "kraken")
                kraken_repo = Repo.clone_from(
                    url=KRAKEN_GIT_PATH_GENERIC, to_path=kraken_tmpdir_path, progress=display_progress)
                kraken_repo.head.reset(
                    commit=KRAKEN_COMMIT, index=True, working_tree=True)
                res = venv_command_wrapper(command="pip", arguments=[
                                           "install", "-v", f"--cache-dir={cache_dir_path}", kraken_tmpdir_path], venv_path=venv_kraken_path, stream_output=True, log_mode="a", log_name=log_name)
                if KRAKEN_SENSITIVE_PACKAGES != []:
                    print("installing version sensitive packages...")
                    package_arguments = [
                        "install", f"--cache-dir={cache_dir_path}", "--force-reinstall", "-v"]
                    package_arguments.extend(KRAKEN_SENSITIVE_PACKAGES)
                    package_res = venv_command_wrapper(command="pip", arguments=package_arguments,
                                                       venv_path=venv_kraken_path, stream_output=True, log_mode="a", log_name=log_name)
                print("removing temporary kraken clone...")
                rmtree(kraken_tmpdir_path)
                print("kraken clone successfully removed.")
                if res.returncode != 0:
                    print("it seems the installation failed.")
                    # print(res.stdout)
                    # print(res.stderr)
                    exit()
            print("done.")
    else:
        if ((not os.path.exists(venv_tesseract_path) or force)):
            print("Création de l'environement virtuel tesseract.")
            cache_dir_path = os.path.join(venv_tesseract_path, "tmp")
            log_name = os.path.join(
                SCRIPT_DIR, "logs", "tesseract_install_log.txt")
            subprocess.run(
                args=[python_path, "-m", "virtualenv", venv_tesseract_path])
            # install tesseract
            print("installing pytesseract...")
            res = venv_command_wrapper(command="pip", arguments=[
                                       "install", f"--cache-dir={cache_dir_path}", "pytesseract", "opencv-python"], venv_path=venv_tesseract_path, stream_output=True, log_mode="w", log_name=log_name)
            print("done.")
    return


def kraken_ocrise_image_file(img_path: str, output_type: str = "txt", force: bool = False, lang: Union[str, None] = None, model: Union[None, str] = None, segmentation_mode: str = "bl", binarise: bool = False):
    output_type_opt: str = f"--{output_type}" if output_type != "txt" else "-o txt"
    if model is not None:
        corpus_model_path: str = model
    elif lang is not None and lang in KRAKEN_MODELS:
        corpus_model_path: str = os.path.join(
            model_dir, KRAKEN_MODELS[lang]["name"])
    else:
        corpus_model_path: str = corpus_model_path_fra_17
    error_log_path: str = os.path.join(SCRIPT_DIR,
                                       "logs", f"{date.today()}-kraken-error-log.txt")
    success_log_path: str = os.path.join(SCRIPT_DIR,
                                         "logs", f"{date.today()}-kraken-log.txt")
    current_date: datetime = datetime.now()
    print(img_path)
    out_img_path: str = f"{os.path.join(os.path.dirname(img_path), f'{Path(img_path).stem}.{output_type}')}"
    print(out_img_path)
    if os.path.exists(out_img_path) and not force:
        print("this file has already been processed before.")
        return
    if binarise or segmentation_mode != "bl":
        print("Binarisation...")
        venv_command_wrapper(command="kraken", arguments=[
            "-i", img_path, img_path, "binarize"], venv_path=venv_kraken_path)
    # Segmentation and ocr
    print("Segmentation...")
    res = venv_command_wrapper(command="kraken", arguments=[
                               "-i", img_path, out_img_path, output_type_opt, "segment", "-bl", "ocr", "-m", corpus_model_path], venv_path=venv_kraken_path)
    if res.stderr != "":
        error_message: str = f"-------------ERROR-------------\n{res.stderr}"
        print(error_message)
        with open(error_log_path, "a") as error_log_file:
            error_log_file.write(
                f"date: {current_date.date()}, {current_date.hour}\n")
            error_log_file.write(f"file: {out_img_path}\n")
            error_log_file.write(f"error message:\n")
            error_log_file.write(f"{error_message}\n")
    else:
        with open(success_log_path, "a") as success_log_file:
            success_log_file.write(
                f"date: {current_date.date()}, {current_date.hour}\n")
            try:
                success_log_file.write(f"{out_img_path}\n")
            except Exception as e:
                print(e)
    return


def kraken_ocrise_image_dir(dir_path: str, output_type: str = "txt", multiprocess: bool = True, nb_core: int = 3, force: bool = False, lang: Union[str, None] = None, model: Union[None, str] = None):
    file_list: list = glob.glob(pathname=os.path.join(
        dir_path, "**", "*.png"), recursive=True)
    for ext in INPUT_TYPE_LIST:
        if ext != "png" and ext != "pdf":
            print(ext)
            file_list.extend(glob.glob(pathname=os.path.join(
                dir_path, "**", f"*.{ext}"), recursive=True))
    print("***********************")
    print(file_list)
    if multiprocess:
        print(f"multiprocessing using {nb_core}...")
        file_list = [(filepath, output_type, force, lang)
                     for filepath in file_list]
        pool: ThreadPool = ThreadPool(processes=nb_core)
        pool.starmap(func=kraken_ocrise_image_file, iterable=tqdm(file_list))
        pool.close()
        pool.join()
    else:
        print("multiprocessing disabled.")
        for img_path in tqdm(file_list):
            kraken_ocrise_image_file(
                img_path=img_path, output_type=output_type, force=force, lang=lang)
    return


def tesseract_ocrise_file(filepath: str, output_type: str, force: bool = False, lang: str = "fra", tesseract_path=None):
    os.makedirs(os.path.join(SCRIPT_DIR, "logs"), exist_ok=True)
    error_log_path: str = os.path.join(SCRIPT_DIR,
                                       "logs", f"{date.today()}-tesseract-error-log.txt")
    success_log_path: str = os.path.join(SCRIPT_DIR,
                                         "logs", f"{date.today()}-tesseract-log.txt")
    current_date: datetime = datetime.now()
    if tesseract_path is None:
        tesseract_path = find_tesseract_path()
    print("OCRisation with Tesseract...")
    res = venv_command_wrapper(command="python", arguments=[
                               os.path.join(SCRIPT_DIR, "tesseract_ocr.py"), filepath, output_type, str(force), lang, tesseract_path])
    print(res.stdout)
    if res.stderr != "":
        error_message: str = f"-------------ERROR-------------\n{res.stderr}"
        print(error_message)
        with open(error_log_path, "a") as error_log_file:
            error_log_file.write(
                f"date: {current_date.date()}, {current_date.hour}\n")
            error_log_file.write(f"{filepath}\n")
            error_log_file.write(f"error message:\n")
            error_log_file.write(f"{error_message}\n")

    else:
        with open(success_log_path, "a") as success_log_file:
            try:
                success_log_file.write(
                    f"date: {current_date.date()}, {current_date.hour}\n")
                success_log_file.write(f"{filepath}\n")
            except Exception as e:
                print(e)
    return


def tesseract_ocrise_dir(dir_path: str, output_type: str, multiprocess: bool = True, nb_core: int = 3, force: bool = False, lang: Union[str, None] = "fra", tesseract_path=None):
    print(f"multiprocessing={multiprocess}")
    if tesseract_path is None:
        tesseract_path = find_tesseract_path()
        print(tesseract_path)
    file_list: list = glob.glob(pathname=f"{dir_path}/*.png")
    for ext in INPUT_TYPE_LIST:
        if ext != "png" and ext != "pdf":
            file_list.extend(glob.glob(pathname=f"{dir_path}/*.{ext}"))
    if multiprocess:
        print(f"multiprocessing using {nb_core}...")
        file_list = [(filepath, output_type, force, lang, tesseract_path)
                     for filepath in file_list]
        pool: ThreadPool = ThreadPool(processes=nb_core)
        pool.starmap(tesseract_ocrise_file, file_list)
        pool.close()
        pool.join()
    else:
        print("multiprocessing disabled.")
        for img_path in file_list:
            tesseract_ocrise_file(filepath=img_path, output_type=output_type,
                                  force=force, tesseract_path=tesseract_path, lang=lang)
    return


def ocrise_file(filepath: str, output_dir_path: str, output_type: str = "txt", engine: str = "t", dpi: int = 200, venv_path: str = venv_tesseract_path, multiprocess: bool = True, nb_core: int = 3, force: bool = False, tesseract_path=None, lang: Union[None, str] = None, model: Union[None, str] = None):
    """OCRise the file found at <filepath>.

    Args:
        filepath (str): The path to the file to ocrise. Can be a pdf or an image.
        output_dir_path (str): WIP
        output_type (str, optional): The format used for the output. Options are: txt, alto. Defaults to "txt".
        engine (str, optional): The engine to use for OCRisation. Options are: "t" (tesseract), "k" (kraken). Defaults to "t".
        dpi (int, optional): WIP. Defaults to 200.
        venv_path (str, optional): WIP. Defaults to venv_tesseract_path.
        multiprocess (bool, optional): WIP. Defaults to True.
        nb_core (int, optional): WIP Defaults to 3.
        force (bool, optional): WIP. Defaults to False.
        tesseract_path (_type_, optional): WIP. Defaults to None.
        lang (Union[None, str], optional): WIP. Defaults to None.
        model (Union[None, str], optional): WIP. Defaults to None.
    """
    file_Path: Path = Path(filepath)
    # create one subdirectory for each file
    if lang is None and model is not None:
        res_dir_path: str = os.path.join(
            output_dir_path, f"{ENGINE_DICT[engine]}{venv_get_version_package(package=ENGINE_PACKAGES[engine], venv_path=venv_path)}", Path(model).stem, file_Path.stem)
    else:
        res_dir_path: str = os.path.join(
            output_dir_path, f"{ENGINE_DICT[engine]}{venv_get_version_package(package=ENGINE_PACKAGES[engine], venv_path=venv_path)}", lang, file_Path.stem)
    os.makedirs(name=res_dir_path, exist_ok=True)
    # print(res_dir_path)
    # split file into image pages
    if filepath.endswith("pdf"):
        poppler_bin_path = None
        # install poppler in the virtual environment on windows
        if sys.platform.startswith("win"):
            poppler_path = download_unzip_binary(
                binary_name="poppler", bin_link=WIN_POPPLER_LINK, venv_path=venv_path)
            # retrieve the poppler-xx/bin path
            poppler_bin_path = glob.glob(os.path.join(
                poppler_path, "**", "bin"), recursive=True)[0]
        print("splitting into images")
        pdf2image.convert_from_path(pdf_path=filepath, output_folder=res_dir_path, fmt="png",
                                    output_file=file_Path.stem, dpi=dpi, poppler_path=poppler_bin_path)  # type: ignore
    else:
        # (Image.open(filepath)).save(os.path.join(res_dir_path, f"{os.path.basename(filepath)}"))
        copy(src=filepath, dst=os.path.join(
            res_dir_path, os.path.basename(filepath)))

        # ocrisation
    if engine == "k":
        kraken_ocrise_image_dir(dir_path=res_dir_path, output_type=output_type,
                                multiprocess=multiprocess, nb_core=nb_core, force=force, lang=lang, model=model)
    else:
        tesseract_ocrise_dir(dir_path=res_dir_path, output_type=output_type,
                             multiprocess=multiprocess, nb_core=nb_core, force=force, lang=lang)
    return


def ocrise_dir(input_dir_path: str, output_dir_path: str, output_type: str = "alto", engine: str = "t", dpi: int = 200, venv_path: str = venv_tesseract_path, multiprocess: bool = True, nb_core: int = 3, force: bool = False, tesseract_path=None, lang=None, model: Union[None, str] = None, keep_png: bool = False, multiprocess_document: bool = False):
    file_list: str = glob_path_dir(input_dir_path)
    if multiprocess_document:
        print(
            f"multiprocessing using {nb_core}: multiprocessing over documents.")
        multiprocess = False
        file_list: list = [(filepath, output_dir_path, output_type, engine, dpi, venv_path, multiprocess, nb_core, force, tesseract_path, lang, model)
                           for filepath in file_list]
        pool: ThreadPool = ThreadPool(processes=nb_core)
        pool.starmap(func=ocrise_file, iterable=tqdm(file_list))
        pool.close()
        pool.join()
    else:
        for filepath in tqdm(file_list):
            print(filepath)
            ocrise_file(filepath=filepath, output_dir_path=output_dir_path, output_type=output_type, engine=engine, dpi=dpi,
                        venv_path=venv_path, multiprocess=multiprocess, nb_core=nb_core, force=force, tesseract_path=tesseract_path, lang=lang, model=model)
    # remove pngs
    if keep_png == False:
        png_file_list: list = glob.glob(os.path.join(
            output_dir_path, "**", "*.png"), recursive=True)
        for png_file in png_file_list:
            os.remove(png_file)
    return


def img_to_txt(input_dir_path: str, output_type: str = "txt", engine: str = "t", output_dir_path: Union[str, None] = None, dpi: int = 200, multiprocess: bool = True, multiprocess_document: bool = False, nb_core: int = 3, force: bool = False, tesseract_path=None, lang: Union[None, str] = None, keep_png: bool = False, model: Union[None, str] = None, kraken_version: Union[None, str] = None):
    # preliminary steps
    if engine.lower() in ENGINE_DICT.values():
        for key in ENGINE_DICT:
            if ENGINE_DICT[key] == engine:
                engine = key
                break
    if output_dir_path is None:
        # output_dir_path = os.path.join(os.path.dirname(input_dir_path), f"{Path(input_dir_path).stem}_ocr")
        output_dir_path = create_output_dir_path(input_dir_path=input_dir_path)
    # if sys.platform.startswith("win") and engine == "k":
    if not os_is_compatible(engine=engine):
        print("Unfortunately, Windows is not supported on kraken. Defaulting to tesseract.")
        engine = "t"
   # actual script
    # set up virtual environment
    venv_path: str = venv_kraken_path if engine == "k" else venv_tesseract_path
    set_up_venv(engine=engine, kraken_version=kraken_version)
    # download language models as needed
    if lang is not None and lang in KRAKEN_MODELS and engine == "k":
        print(f"downloading {lang} model...")
        download_kraken_models(lang=lang, venv_path=venv_path)
    # ocrisation
    ocrise_dir(input_dir_path=input_dir_path, output_dir_path=output_dir_path, output_type=output_type, engine=engine, dpi=dpi,
               venv_path=venv_path, multiprocess=multiprocess, nb_core=nb_core, force=force, tesseract_path=tesseract_path, lang=lang, keep_png=keep_png, model=model, multiprocess_document=multiprocess_document)
    return


# TESTS
def run_benchmark(input_dir_path: str, benchmark_dir_path: str = benchmark_dir_path, engine: str = "t", output_type: str = "txt", multiprocess: bool = True, dpi: int = 200, number_it: int = 1, nb_core: int = 3):
    bench_filepath: str = os.path.join(
        benchmark_dir_path, f"{ENGINE_DICT[engine]}-benchmark.csv")
    if not os.path.exists(bench_filepath):
        os.makedirs(name=os.path.dirname(bench_filepath), exist_ok=True)
        bench_file = open(file=bench_filepath, mode="w")
        bench_file.write(
            "time,multiprocess,output_type,dpi,number_of_files,number_iterations,nb_core\n")
    else:
        bench_file = open(file=bench_filepath, mode="a")
    time = timeit.timeit(
        stmt=f"img_to_txt(input_dir_path='{input_dir_path}', output_type='{output_type}', engine='{engine}', dpi={dpi}, multiprocess={multiprocess}, nb_core={nb_core})", setup="from __main__ import img_to_txt", number=number_it)
    if multiprocess:
        bench_file.write(
            f"{time/number_it},{multiprocess},{output_type},{dpi},{len(os.listdir(path=input_dir_path))},{number_it},{nb_core}\n")
    else:
        bench_file.write(
            f"{time/number_it},{multiprocess},{output_type},{dpi},{len(os.listdir(path=input_dir_path))},{number_it},{None}\n")
    bench_file.close()
    return


if __name__ == "__main__":
    img_to_txt(input_dir_path=test_dir_path, output_dir_path=None,
               output_type="txt", engine="k", lang=None, force=True, keep_png=False)
    img_to_txt(input_dir_path=test_dir_path, output_dir_path=None,
               output_type="alto", engine="k", lang=None, force=True, keep_png=False)
    img_to_txt(input_dir_path=test_dir_path, output_dir_path=None,
               output_type="txt", engine="t", lang="fra", force=True, keep_png=False)
    img_to_txt(input_dir_path=test_dir_path, output_dir_path=None,
               output_type="alto", engine="t", lang="fra", force=True, keep_png=False)

    # tesseract
    # run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="txt", multiprocess=True, dpi=200, number_it=5)
    # run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="alto", multiprocess=False, dpi=200, number_it=5)
    # kraken
    # set_up_venv(engine="k")
    # download_kraken_models(lang="en")
    # print("----------------------MULTIPROCESS----------------------")
    # run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="html", multiprocess=True, dpi=200, number_it=1, nb_core=3)
    # print("----------------------NO MULTIPROCESS----------------------")
    # run_benchmark(input_dir_path=test_dir_path,benchmark_dir_path=benchmark_dir_path, engine="t", output_type="html", multiprocess=False, dpi=200, number_it=1, nb_core=3)
    # other tests
    # download_unzip_binary(binary_name="poppler", bin_link=WIN_POPPLER_LINK, venv_path=venv_tesseract_path)
    # print(venv_get_version_package(package="kraken", venv_path=venv_kraken_path))
    # ocrise_file(filepath="../../Antonomaz/Glane5_process/Glane5-sample/BM01481_MAZ.jpg", output_dir_path="../../Antonomaz/Glane5_process/Glane5-sample_ocr/", engine="k", output_type="txt", venv_path=venv_kraken_path, force=True)
