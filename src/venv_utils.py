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
