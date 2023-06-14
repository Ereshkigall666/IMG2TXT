import io
import sys
import pytesseract
import cv2 

if __name__ == '__main__':
	if len(sys.argv) == 3:
		img_path = sys.argv[1]
		outType = sys.argv[2]
		ext = '.txt' if outType == 'txt' else '.alto'
		img = cv2.imread(img_path)
		
		# preprocessings
		# Lire un fichier de paramètre pour simplifier les démarches
		# ocr
		out_name = img_path.split('\.')[0] + ext
		if ext == '.txt':
			outFile = io.open(out_name, 'w')
			txt = pytesseract.image_to_string(img)
			outFile.write(txt)
		else: # alto
			outFile = io.open(out_name, 'wb')
			alto = pytesseract.image_to_alto_xml(img)
			outFile.write(alto)
		outFile.close()
