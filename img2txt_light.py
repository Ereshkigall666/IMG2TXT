from argparse import *
from img2txt_light_functions import *

description:str = "a command line utility to OCRise corpora using kraken or tesseract."
epilog:str = "usage: python3 img2txt_light.py <corpus_path> -o <output format> -e <engine>"

if __name__ == "__main__":
    parser = ArgumentParser(description=description, epilog=epilog)
    parser.add_argument("corpus_path")
    parser.add_argument("-i_fmt", "--input_format", default="pdf")
    parser.add_argument("-o_fmt", "--output_format", default="txt")
    parser.add_argument("-o", "--output_dir", default="")
    parser.add_argument("-e", "--engine", default="t")
    args = parser.parse_args()
    img_to_txt(input_dir_path=args.corpus_path, input_type=args.input_format, output_type=args.output_format, engine=args.engine, output_dir_path=args.output_dir)
    #print(args)
    