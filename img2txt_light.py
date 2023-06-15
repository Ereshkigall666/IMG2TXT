from argparse import *
from img2txt_light_functions import *

description:str = "a command line utility to OCRise corpora using kraken or tesseract."
epilog:str = ""

if __name__ == "__main__":
    parser = ArgumentParser(description=description, epilog=epilog, formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("corpus_path", help="path to the corpus you want to OCRise.")
    parser.add_argument("-o_fmt", "--output_format", default="txt", help="the output format of the OCRised documents.", choices=OUTPUT_TYPE_LIST)
    parser.add_argument("-o", "--output_dir", help="the directory in which the output files should be put (if you want them to be put in a specific directory). Defaults to a <input_dir>_ocr directory.")
    parser.add_argument("-e", "--engine", default="t", help="the OCR engine to use.", choices=ENGINE_DICT.items())
    args = parser.parse_args()
    img_to_txt(input_dir_path=args.corpus_path,output_type=args.output_format, engine=args.engine, output_dir_path=args.output_dir)
    #print(args)
    