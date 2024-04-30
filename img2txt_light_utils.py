# import os
from datetime import date, datetime
import subprocess
import sys
import logging
# import venv
# import virtualenv
import glob
import timeit
import platform
from multiprocessing import *
from multiprocessing.pool import ThreadPool
from tqdm.auto import tqdm
from pathlib import Path
# from typing import Final, Dict, List, Union
from shutil import copy, rmtree
import pdf2image
from PIL import Image
import requests
import zipfile
from git import Repo
import configparser
from io import BytesIO
from constants import *


def create_output_dir_path(input_dir_path: str) -> str:
    return os.path.join(os.path.dirname(
        input_dir_path), f"{Path(input_dir_path).stem}_ocr")


def os_is_compatible(engine: str) -> bool:
    return not (sys.platform.startswith("win") and engine == "k")


def glob_path_dir(dir_path: str):
    return glob.glob(os.path.join(dir_path, "**", "*"), recursive=True)


def download_unzip_binary(binary_name: str, bin_link: str, venv_path: str = venv_tesseract_path, github_api: bool = True, force: bool = False) -> str:
    """Fetches compressed binaries and downloads them to <venv_path>/<other_bin>
    Args:
        binary_name (str): the name under which the binary will be downloaded. Can end up being either a file or a directory depending on what the specific binary is like.
        bin_link (str, optional): the link to the binary to download.
        venv_path (str, optional): [description]. Defaults to venv_tesseract_path. Path to the virtual environment currently used. 
    """
    bin_path: str = os.path.join(venv_path, "other_bin", binary_name)
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
    # print(glob.glob(os.path.join(bin_path, "**", "bin"), recursive=True))
    return bin_path


def display_progress(op_code, cur_count, max_count=None, message=''):
    if max_count is not None:
        percent = int((cur_count / max_count) * 100)
        print(f'{op_code}: {percent}% - {message}', end='\r')
    else:
        print(f'{op_code}: {cur_count} - {message}', end='\r')
    return
