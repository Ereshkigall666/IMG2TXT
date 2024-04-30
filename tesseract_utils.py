import os
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
from typing import Final, Dict, List, Union
from shutil import copy, rmtree
import pdf2image
from PIL import Image
import requests
import zipfile
from git import Repo
import configparser
from constants import *


def find_tesseract_path() -> str:
    tesseract_path: str = ""
    if not sys.platform.startswith("win"):
        res = None
        # some distros have 'tesseract-ocr' as the relevant name (e.g void)
        for tesseract_name in ["tesseract-ocr", "tesseract"]:
            res = subprocess.run(
                args=["which", tesseract_name], capture_output=True, text=True)
            which_out: str = res.stdout.strip()
            if os.path.exists(os.path.realpath(which_out)) and res.returncode == 0:
                tesseract_path = os.path.realpath(which_out)
                break
        else:
            print(
                f"it looks like tesseract is not installed on this system.Please install it at: {TESSERACT_INSTALL_LINK}. If it is installed, it may simply not be in your PATH.")
            sys.exit()
    else:
        tesseract_path = WIN_TESSERACT_EXE_PATH
        if not os.path.exists(tesseract_path):
            print(
                f"it looks like tesseract is not installed on this system. Please install it at: {TESSERACT_INSTALL_LINK}.  If it is installed, it may simply not be in your PATH.")
            sys.exit()
    return tesseract_path


def find_tesseract_lang_path() -> str:

    return
