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
from venv_utils import *


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


def select_kraken_model(model: Union[None, str] = None, seg: bool = False) -> str:
    model_dict: dict[str, dict[str, str]
                     ] = KRAKEN_MODELS if not seg else KRAKEN_SEG_MODELS
    if model is None and not seg:
        return corpus_model_path_fra_17
    if model in model_dict:
        return os.path.join(model_dir, model_dict[model]["name"])
    return model


def kraken_binarise_img(img_path: str):
    venv_command_wrapper(command="kraken", arguments=[
        "-i", img_path, img_path, "binarize"], venv_path=venv_kraken_path)
    return


def kraken_segment_ocr(img_path: str, out_img_path: str, model: str, output_type: str = "txt", segmentation_mode: str = "bl", seg_model: Union[str, None] = None):
    kraken_args: list[str] = ["-i", img_path, out_img_path]
    kraken_args.append(
        f"--{output_type}") if output_type != "txt" else kraken_args.append("-o txt")
    segment_args: list[str] = ["segment", f"-{segmentation_mode}"]
    if seg_model is not None:
        segment_args.extend(["-i", seg_model])
    ocr_args: list[str] = ["ocr", "-m", model]
    all_args: list[str] = kraken_args + segment_args + ocr_args
    print(all_args)
    res = venv_command_wrapper(
        command="kraken", arguments=all_args, venv_path=venv_kraken_path)
    return res


if __name__ == "__main__":
    # download_kraken_models(lang="2-column-print",model_dir=model_dir, is_seg=True)
    download_kraken_models(lang="htr-manicule-beta",
                           model_dir=model_dir, is_seg=False, force=True)
