#!/usr/bin/env python3

INPUT_HOCR_DIR = "030-ocr-white"
INPUT_DIR = "020-white"
OUTPUT_DIR = "040-level-images"

# FIXME dont process text in these input files
ignore_input_files = [
    "0003-00200.png",
]

r"""
chatGPT prompt:

create a python script to level image colors from blue/grey to black.
the images are screenshots of text and images.
only the text parts should be leveled, but not the image parts.
the text positions are encoded in HOCR files:

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title></title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
  <meta name='ocr-system' content='tesseract 5.5.1' />
  <meta name='ocr-capabilities' content='ocr_page ocr_carea ocr_par ocr_line ocrx_word ocrp_dir ocrp_lang ocrp_wconf'/>
 </head>
 <body>
  <div class='ocr_page' id='page_1' title='image "../white/0012-00100.png"; bbox 0 0 2047 1141; ppageno 0; scan_res 70 70'>
   <div class='ocr_carea' id='block_1_1' title="bbox 41 16 2007 843">
    <p class='ocr_par' id='par_1_1' lang='deu' title="bbox 41 16 2007 385">
     <span class='ocr_line' id='line_1_1' title="bbox 43 16 2005 55; baseline 0 -9; x_size 37; x_descenders 8; x_ascenders 8">
      <span class='ocrx_word' id='word_1_1' title='bbox 43 17 90 46; x_wconf 95'>Ich</span>
      <span class='ocrx_word' id='word_1_2' title='bbox 117 17 201 47; x_wconf 95'>habe</span>
      <span class='ocrx_word' id='word_1_3' title='bbox 227 18 284 46; x_wconf 95'>mir</span>
      <span class='ocrx_word' id='word_1_4' title='bbox 307 17 416 47; x_wconf 96'>weder</span>
```

the HOCR files are XML files, so just use python's xml parser

every word has a "bbox" value: x1, y1, x2, y2

only the word areas of the input images should be leveled

the blue color is #434376 and the grey color is #757575

when a word has black text color, dont level it

only when a word has blue or grey text color, then level it, so the text color becomes black
"""

import os
import re
import cv2
import numpy as np
import xml.etree.ElementTree as ET
from PIL import Image
import shutil

# Regex to match filenames like 336-00100-ffffffff.png
pattern = re.compile(r"^(\d{3})-\d{5}-[0-9a-f]+\.png$")

import cv2
import numpy as np
import xml.etree.ElementTree as ET
from PIL import Image

def parse_hocr(hocr_file):
    tree = ET.parse(hocr_file)
    root = tree.getroot()
    word_boxes = []
    for elem in root.iter():
        if elem.attrib.get('class') == 'ocrx_word':
            title = elem.attrib.get('title','')
            if 'bbox' in title:
                bbox_str = title.split(';')[0].replace('bbox','').strip()
                x1, y1, x2, y2 = map(int, bbox_str.split())
                word_boxes.append((x1, y1, x2, y2))
    return word_boxes

def recolor_word_regions(image_path, hocr_file, output_path):
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    word_boxes = parse_hocr(hocr_file)
    h, w, _ = img_rgb.shape

    for (x1, y1, x2, y2) in word_boxes:
        # Sample a 1px border outside the bbox
        x1b, y1b = max(x1-1,0), max(y1-1,0)
        x2b, y2b = min(x2+1,w), min(y2+1,h)
        top = img_rgb[y1b:y1, x1b:x2b]
        bottom = img_rgb[y2:y2b, x1b:x2b]
        left = img_rgb[y1b:y2b, x1b:x1]
        right = img_rgb[y1b:y2b, x2:x2b]

        border = np.concatenate([top.reshape(-1,3), bottom.reshape(-1,3),
                                 left.reshape(-1,3), right.reshape(-1,3)], axis=0)
        avg_border = np.median(border, axis=0)

        # Only process word if background is mostly white
        if np.all(avg_border >= 242):
            roi = img_rgb[y1:y2, x1:x2]
            roi_int = roi.astype(np.int16)
            r, g, b = roi_int[:,:,0], roi_int[:,:,1], roi_int[:,:,2]

            # Grey detection: median-based
            pixels = roi_int.reshape(-1,3)
            mask_dark = np.all(pixels < 250, axis=1)
            if np.sum(mask_dark) > 0:
                dark_pixels = pixels[mask_dark]
                median_color = np.median(dark_pixels, axis=0)
                dist = np.linalg.norm(pixels - median_color, axis=1)
                dist_black = np.linalg.norm(pixels, axis=1)
                mask_grey_flat = (dist < 40) & (dist_black > 20)
                mask_grey = mask_grey_flat.reshape(roi.shape[0], roi.shape[1])
            else:
                mask_grey = np.zeros((roi.shape[0], roi.shape[1]), dtype=bool)

            # Blue detection: pixels where B dominates R and G
            mask_blue = (b > 80) & (b > r + 20) & (b > g + 20)

            # Combine masks
            mask = mask_grey | mask_blue

            if np.any(mask):
                gray_vals = (0.299*r[mask] + 0.587*g[mask] + 0.114*b[mask]).astype(np.uint8)
                roi[mask] = np.stack([gray_vals, gray_vals, gray_vals], axis=1)
                roi[mask] = np.minimum(roi[mask],50)  # force dark black
                img_rgb[y1:y2, x1:x2] = roi

    # Convert final image to grayscale
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    result = Image.fromarray(img_gray)
    result.save(output_path)
    print(f"Processed greyscale image saved to {output_path}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for fname in sorted(os.listdir(INPUT_DIR)):
        if not pattern.match(fname): continue
        output_path = OUTPUT_DIR + "/" + fname
        if os.path.exists(output_path): continue
        image_path = INPUT_DIR + "/" + fname
        if fname in ignore_input_files:
            shutil.copy(image_path, output_path)
            continue
        hocr_file = INPUT_HOCR_DIR + "/" + os.path.splitext(fname)[0] + ".hocr"
        recolor_word_regions(image_path, hocr_file, output_path)

if __name__ == "__main__":
    main()
