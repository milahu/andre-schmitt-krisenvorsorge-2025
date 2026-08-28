#!/usr/bin/env python3

r"""
chatGPT prompt:

create a python script to add a "running footer" to image files.
process all images from an input directory, and write output files to a separate output directory.
the input images have filenames like "0223.png" or "0224_0225.png" which represent the page numbers (223, 224, 225)
parse these page numbers from the filenames, and add them to the bottom of every page.
to make room for the running footer, expand the image size.
the images are screenshots of text.
the line height is 66 px. the font size is 39 px (height between ascender and descender letters).
the running footer should be spaced with one empty line (66 px)
"""

import os
import re
from PIL import Image, ImageDraw, ImageFont
import fontconfig

# --- Configuration ---
input_dir = "060-expand-canvas"
output_dir = "070-page-numbers"
line_height = 66
font_size = 39
font_name = "LiberationSans"
font_variant = "Regular" # LiberationSans-Regular.ttf

font_filename = f"{font_name}-{font_variant}.ttf"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Regex to extract page numbers from filenames like "223.png" or "224_225.png" or "001x2.png"
page_number_pattern = re.compile(r'(\d{3})(?:_(\d{3})|x(\d+))?')

# Use fontconfig to locate the font file
font_files = fontconfig.query(font_name)
print("font_files", font_files)
# font_path = next((f for f in font_files if font_variant in f), None)
font_path = next((f for f in font_files if f.endswith(font_filename)), None)
if not font_path:
    raise RuntimeError(f"Could not find {font_filename} via fontconfig")
font = ImageFont.truetype(font_path, font_size)

def get_page_numbers(filename):
    match = page_number_pattern.match(filename)
    if not match:
        return []
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else start
    return list(range(start, end + 1))

def add_running_footer(image_path, page_numbers):
    img = Image.open(image_path)
    width, height = img.size

    # New canvas: original image + one empty line + footer line
    new_height = height + 2 * line_height
    new_img = Image.new("RGB", (width, new_height), color=(255, 255, 255))
    new_img.paste(img, (0, 0))

    if page_numbers[0] == 1:
        # dont number the first page
        return new_img

    draw = ImageDraw.Draw(new_img)

    # # keep only the first page number
    # footer_text = str(page_numbers[0])

    # Footer text: join page numbers with dash if multiple
    footer_text = "-".join(str(p) for p in page_numbers)

    # Get text size using textbbox
    bbox = draw.textbbox((0, 0), footer_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position: one empty line below original image
    y_position = height + line_height
    x_position = (width - text_width) // 2  # center horizontally

    draw.text((x_position, y_position), footer_text, fill=(0, 0, 0), font=font)

    return new_img

# Process all images in input directory
for filename in os.listdir(input_dir):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        page_numbers = get_page_numbers(filename)
        if not page_numbers:
            print(f"Skipping file {filename}, cannot parse page numbers.")
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        if os.path.exists(output_path): continue

        new_img = add_running_footer(input_path, page_numbers)
        new_img.save(output_path)
        print(f"Processed {filename} -> {output_path}")
