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


def get_repo_url(lang: str, repo: str, doi: str, download_token: str | None = None) -> str | None:
    repo_url: str | None = None
    if repo == "zenodo":
        repo_url = f"https://zenodo.org/api/records/{doi}"
    elif repo == "nakala":
        repo_url = f"https://api.nakala.fr/data/{doi}/{download_token}"
    return repo_url


def download_kraken_models(lang: str, model_dir: str = model_dir, venv_path: str = venv_kraken_path, is_seg: bool = False, force: bool = False):
    model_dict: dict[str, dict[str, str]
                     ] = KRAKEN_MODELS if not is_seg else KRAKEN_SEG_MODELS
    kraken_key, doi, download_token, name, repo = model_dict[lang].values()
    output_file: str = os.path.join(
        model_dir, name)
    if force or not os.path.exists(output_file):
        repo_url: str | None = get_repo_url(
            lang=lang, doi=doi, repo=repo, download_token=download_token)
        if repo_url is None:
            print(f"this repository: {repo} could not be found.")
            exit(1)
        print(repo_url)
        # zenodo_url: str = f"https://zenodo.org/api/records/{model_dict[lang]['doi']}"
        # print(zenodo_url)
        if repo == "zenodo":
            response = requests.get(zenodo_url)
            data = response.json()
            # Find the file URL in the response
            file_url = None
            for file in data["files"]:
                if file["key"].endswith("mlmodel"):
                    file_url = file["links"]["self"]
                    print(file_url)
                    break
            if file_url is None:
                print("File not found.")
                return
        else:
            file_url = repo_url
        # Download the file
        response = requests.get(file_url)
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"File downloaded to {output_file}")
    return


if __name__ == "__main__":
    # download_kraken_models(lang="2-column-print",model_dir=model_dir, is_seg=True)
    download_kraken_models(lang="htr-manicule-beta",
                           model_dir=model_dir, is_seg=False, force=True)
