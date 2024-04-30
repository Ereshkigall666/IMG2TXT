import os
from typing import Final, Dict, List, Union

# global constants
SCRIPT_DIR: Final[str] = os.path.dirname(os.path.realpath(__file__))
INPUT_TYPE_LIST: Final[List] = ["pdf", "jpg", "jpeg", "png" "tif"]
OUTPUT_TYPE_LIST: Final[List] = ["txt", "html", "alto"]
ENGINE_DICT: Final[Dict] = {"k": "kraken", "t": "tesseract"}
ENGINE_PACKAGES: Final[Dict] = {"k": "kraken", "t": "pytesseract"}
WIN_POPPLER_LINK: Final[str] = "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest"
# PY_VERSION_LIST:Final[List] = [9, 8]
PY_VERSION_LIST: list = [10, 9, 8]
WIN_TESSERACT_LINK: Final[str] = "https://api.github.com/repos/UB-Mannheim/tesseract/releases/latest"
TESSERACT_INSTALL_LINK: Final[str] = "https://tesseract-ocr.github.io/tessdoc/Installation.html"
WIN_TESSERACT_EXE_PATH: Final[str] = "C:\Program Files\Tesseract-OCR\\tesseract.exe"
PIP_EXTRA_REPOS: Final[List] = ["https://www.piwheels.org/simple"]
# Kraken venv constants
KRAKEN_GIT_PATH_GENERIC: Final[str] = f"https://github.com/mittagessen/kraken.git"
# specific commits
# currently set at 4.3.13.dev25
KRAKEN_COMMIT: Final[str] = "1306fb2653c1bd5a9baf6d518dc3968e5232ca8e"
# newest: 09/01/2024
# KRAKEN_COMMIT: Final[str] = "e80308be69041517a97feac903c5c7cf2690227b"
# KRAKEN_GIT_PATH: Final[str] = f"https://github.com/mittagessen/kraken.git@{KRAKEN_COMMIT}"
KRAKEN_GIT_PATH: Final[str] = f"https://github.com/mittagessen/kraken.git"
# packages that are version sensitive and seem not to be installed correctly by kraken
KRAKEN_SENSITIVE_PACKAGES: Final[list] = []
KRAKEN_SENSITIVE_PACKAGES: Final[list] = [
    "scipy==1.10.1", "torch==2.0.0", "scikit-learn==1.1.2"]
KRAKEN_MODELS: Final[dict[dict]] = {"eng": {"kraken_key": "10.5281/zenodo.2577813", "doi": "2577813", "name": "en_best.mlmodel"},
                                    "fra-lectaurep": {"kraken_key": "10.5281/zenodo.6542744",
                                                      "doi": "6542744", "name": "lectaurep_base.mlmodel"}, "fra": {"kraken_key": "10.5281/zenodo.6657809", "doi": "6657809", "name": "HTR-United-Manu_McFrench.mlmodel"}}
KRAKEN_VERSIONS: Final[dict[str, str]] = {
    "4.3.13.dev25": "1306fb2653c1bd5a9baf6d518dc3968e5232ca8e"}
# convenience variables
model_dir: str = os.path.join(SCRIPT_DIR, "models")
venv_kraken_path: str = os.path.join(SCRIPT_DIR, "venv_kraken")
venv_tesseract_path: str = os.path.join(SCRIPT_DIR, "venv_tesseract")
test_dir_path: str = "dummy_corpus"
output_dir_path: str = os.path.join(SCRIPT_DIR, "dummy_corpus_res")
corpus_model_path_fra_17: str = os.path.join(model_dir, "CORPUS17.mlmodel")
benchmark_dir_path: str = os.path.join(SCRIPT_DIR, "benchmarks")
