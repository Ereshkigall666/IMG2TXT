from argparse import *
from img2txt_light_functions import *
subcommands: list[str] = ["install"]
default_subcommand: str = "ocr"
description: str = "a command line utility to OCRise corpora using kraken or tesseract."
epilog: str = ""

if __name__ == "__main__":
    parser: ArgumentParser = ArgumentParser(description=description, epilog=epilog,
                                            formatter_class=ArgumentDefaultsHelpFormatter)
    # subcommand parsers
    subparsers = parser.add_subparsers(
        dest="command", description="All of the available subcommands.")
    install_parser = subparsers.add_parser(
        "install", help="install the specified venv and quit.")
    install_parser.add_argument(
        "-f", "--force", help="reinstall the specified venv even if it is found to already exist.", action="store_true")
    install_parser.add_argument("engine", default="t", help="the OCR engine to use.", choices=[
        engine for iterable in [ENGINE_DICT.keys(), ENGINE_DICT.values()] for engine in iterable], type=str)
    # default subparser and arguments
    ocr_parser = subparsers.add_parser("ocr", help="OCRise a corpus.")
    ocr_parser.add_argument(
        "corpus_path", help="path to the corpus you want to OCRise.")
    ocr_parser.add_argument("-o_fmt", "--output_format", default="txt",
                            help="the output format of the OCRised documents.", choices=OUTPUT_TYPE_LIST)
    ocr_parser.add_argument(
        "-o", "--output_dir", help="the directory in which the output files should be put (if you want them to be put in a specific directory). Defaults to a <input_dir>_ocr directory.")
    ocr_parser.add_argument("-e", "--engine", default="t", help="the OCR engine to use.", choices=[
        engine for iterable in [ENGINE_DICT.keys(), ENGINE_DICT.values()] for engine in iterable])
    ocr_parser.add_argument(
        "-dpi", type=int, help="image quality to aim for.", default=200)
    ocr_parser.add_argument("-nm", "--no_multiprocess",
                            help="disables multiprocessing. Multiprocessing is highly recommended as it speeds up the OCRisation process significantly", action="store_true")
    ocr_parser.add_argument(
        "-nc", "--nb_core", help="number of cores to use if multiprocessing is used.", default=3, type=int)
    ocr_parser.add_argument(
        "-f", "--force", help="whether to force-OCRise files that are determined to have already been processed.", action="store_true")
    ocr_parser.add_argument("-t_path", "--tesseract_path",
                            help="link to the tesseract binary path (useful if it is installed in an unusual location and not in your PATH).", default=None, type=str)
    ocr_parser.add_argument(
        "-l", "--lang", help=f"specify the language model to use for OCRisation. Possible values: {KRAKEN_MODELS.keys()}", default=None, type=str)
    ocr_parser.add_argument("-k", "--keep_png",
                            help="whether to png artifacts or not.", action="store_true")
    # shared arguments
    parser.add_argument(
        "-kv", "--kraken_version", help=f"specify the version of kraken to install in the venv. Possible values: {KRAKEN_VERSIONS.keys()}", default=None, type=str)
    # running the programme
    if not sys.argv[1] in subcommands:
        sys.argv.insert(default_subcommand, 1)
    args = parser.parse_args()
    # print(args)
    if args.command == "install":
        set_up_venv(engine=args.engine, force=args.force)
    else:
        img_to_txt(input_dir_path=args.corpus_path, output_type=args.output_format, engine=args.engine, output_dir_path=args.output_dir,
                   dpi=args.dpi, multiprocess=(not args.no_multiprocess), nb_core=args.nb_core, force=args.force, tesseract_path=args.tesseract_path, lang=args.lang, keep_png=args.keep_png, kraken_version=args.kraken_version)

# TODO: enable shell completion
