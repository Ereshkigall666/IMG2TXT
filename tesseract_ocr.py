import io
import sys
from pathlib import Path
import os
import pytesseract
import cv2


if __name__ == '__main__':
    if len(sys.argv) == 6:
        img_path: str = sys.argv[1]
        output_type: str = sys.argv[2]
        force: bool = sys.argv[3] == "True"
        lang: str = sys.argv[4]
        tesseract_path: str = sys.argv[5]
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        # print(tesseract_path)
        img_Path = Path(img_path)
        output_path: str = f"{os.path.join(img_Path.parent, img_Path.stem)}.{output_type}"
        # check if file has already been processed
        if os.path.exists(output_path) and not force:
            print("this file has already been processed before.")
            sys.exit()
        img = cv2.imread(img_path)
        # preprocessings
        # Lire un fichier de paramètre pour simplifier les démarches
        # ocr
        # print(output_path)
        if output_type == 'txt':
            (output_file := io.open(file=output_path, mode='w')).write(
                txt := pytesseract.image_to_string(img, lang=lang, config="--psm 1"))
        else:  # alto
            (output_file := io.open(file=output_path, mode='wb')).write(
                alto := pytesseract.image_to_alto_xml(img, lang=lang, config="--psm 1"))
        print("done.")
        output_file.close()
        sys.exit()
