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
from venv_utils import *

# disable max size limit for images
Image.MAX_IMAGE_PIXELS = None


def kraken_ocrise_image_file(img_path: str, output_type: str = "txt", force: bool = False, lang: Union[str, None] = None, model: Union[None, str] = None, segmentation_mode: str = "bl", binarise: bool = False, seg_model: Union[str, None] = None):
    # select model
    corpus_model_path: str = model if model else select_kraken_model(
        model=lang)
    seg_model_path: str = select_kraken_model(model=seg_model, seg=True)
    print(seg_model_path)
    out_img_path: str = f"{os.path.join(os.path.dirname(img_path), f'{Path(img_path).stem}.{output_type}')}"
    print(img_path)
    print(out_img_path)
    if os.path.exists(out_img_path) and not force:
        print("this file has already been processed before.")
        return
    if binarise or segmentation_mode != "bl":
        print("Binarisation...")
        kraken_binarise_img(img_path=img_path)
    # Segmentation and ocr
    print("Segmentation...")
    res = kraken_segment_ocr(img_path=img_path, out_img_path=out_img_path, model=corpus_model_path,
                             output_type=output_type, segmentation_mode=segmentation_mode, seg_model=seg_model_path)
    log_progress(filepath=out_img_path, engine="k", stderr=res.stderr)
    return


def kraken_ocrise_image_dir(dir_path: str, output_type: str = "txt", multiprocess: bool = True, nb_core: int = 3, force: bool = False, lang: Union[str, None] = None, model: Union[None, str] = None, seg_model: Union[str, None] = "2-column-print"):
    # print(model)
    file_list: list = glob.glob(pathname=os.path.join(
        dir_path, "**", "*.png"), recursive=True)
    for ext in INPUT_TYPE_LIST:
        if ext != "png" and ext != "pdf":
            file_list.extend(glob.glob(pathname=os.path.join(
                dir_path, "**", f"*.{ext}"), recursive=True))
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
                img_path=img_path, output_type=output_type, force=force, lang=lang, model=model, seg_model=seg_model)
    return


def tesseract_ocrise_file(filepath: str, output_type: str, force: bool = False, lang: str = "fra", tesseract_path=None):
    if tesseract_path is None:
        tesseract_path = find_tesseract_path()
    print("OCRisation with Tesseract...")
    res = venv_command_wrapper(command="python", arguments=[
                               TESSERACT_SCRIPT_PATH, filepath, output_type, str(force), lang, tesseract_path])
    print(res.stdout)
    log_progress(filepath=filepath, engine="t", stderr=res.stderr)
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


def ocrise_file(filepath: str, output_dir_path: str, output_type: str = "txt", engine: str = "t", dpi: int = 200, venv_path: str = venv_tesseract_path, multiprocess: bool = True, nb_core: int = 3, force: bool = False, tesseract_path=None, lang: Union[None, str] = None, model: Union[None, str] = None, seg_model: Union[str, None] = None):
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


def ocrise_dir(input_dir_path: str, output_dir_path: str, output_type: str = "alto", engine: str = "t", dpi: int = 200, venv_path: str = venv_tesseract_path, multiprocess: bool = True, nb_core: int = 3, force: bool = False, tesseract_path=None, lang=None, model: Union[None, str] = None, keep_png: bool = False, multiprocess_document: bool = False, seg_model: Union[str, None] = None):
    # print(model)
    file_list: str = glob_path_dir(input_dir_path)
    if multiprocess_document:
        print(
            f"multiprocessing using {nb_core}: multiprocessing over documents.")
        multiprocess = False
        file_list: list = [(filepath, output_dir_path, output_type, engine, dpi, venv_path, multiprocess, nb_core, force, tesseract_path, lang, model, seg_model)
                           for filepath in file_list]
        pool: ThreadPool = ThreadPool(processes=nb_core)
        pool.starmap(func=ocrise_file, iterable=tqdm(file_list))
        pool.close()
        pool.join()
    else:
        for filepath in tqdm(file_list):
            print(filepath)
            ocrise_file(filepath=filepath, output_dir_path=output_dir_path, output_type=output_type, engine=engine, dpi=dpi,
                        venv_path=venv_path, multiprocess=multiprocess, nb_core=nb_core, force=force, tesseract_path=tesseract_path, lang=lang, model=model, seg_model=seg_model)
    # remove pngs
    if keep_png == False:
        img_file_list: list[str] = []
        for img_type in INPUT_TYPE_LIST:
            img_file_list.extend(glob.glob(os.path.join(
                output_dir_path, "**", f"*.{img_type}"), recursive=True))
        for img_file in img_file_list:
            os.remove(img_file)
    return


def img_to_txt(input_dir_path: str, output_type: str = "txt", engine: str = "t", output_dir_path: Union[str, None] = None, dpi: int = 200, multiprocess: bool = True, multiprocess_document: bool = False, nb_core: int = 3, force: bool = False, tesseract_path=None, lang: Union[None, str] = None, keep_png: bool = False, model: Union[None, str] = None, kraken_version: Union[None, str] = None, seg_model: Union[str, None] = None):
    # print(model)
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
               venv_path=venv_path, multiprocess=multiprocess, nb_core=nb_core, force=force, tesseract_path=tesseract_path, lang=lang, keep_png=keep_png, model=model, multiprocess_document=multiprocess_document, seg_model=seg_model)
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
