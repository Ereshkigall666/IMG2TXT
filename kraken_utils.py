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
from io import BytesIO
from constants import *


def download_kraken_models(lang: str, model_dir: str = model_dir, venv_path: str = venv_kraken_path):
    output_file: str = os.path.join(model_dir, KRAKEN_MODELS[lang]['name'])
    if not os.path.exists(output_file):
        zenodo_url: str = f"https://zenodo.org/api/records/{KRAKEN_MODELS[lang]['doi']}"
        print(zenodo_url)
        response = requests.get(zenodo_url)
        data = response.json()
        # Find the file URL in the response
        file_url = None
        for file in data["files"]:
            # Change "model.pth" to the actual file name you want
            if file["key"].endswith("mlmodel"):
                file_url = file["links"]["self"]
                print(file_url)
                break

        if file_url is None:
            print("File not found.")
            return

        # Download the file
        response = requests.get(file_url)
        with open(output_file, "wb") as f:
            f.write(response.content)

        print(f"File downloaded to {output_file}")
    return
