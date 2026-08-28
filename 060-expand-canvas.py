#!/usr/bin/env python3

# this is a workaround for img2pdf
# to get "vertical-align: top" of the images

# Set input and output folders
input_folder = "050-merged-white"
output_folder = "060-expand-canvas"

# Target canvas size
TARGET_WIDTH, TARGET_HEIGHT = 2047, 2282

import os
from PIL import Image, ImageOps
import shutil

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Process all files in the input folder
for filename in os.listdir(input_folder):
    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename)
    if os.path.exists(output_path): continue

    # Only process image files
    try:
        with Image.open(input_path) as img:
            width, height = img.size

            # if width >= TARGET_WIDTH and height >= TARGET_HEIGHT:
            if height >= TARGET_HEIGHT:
                # Image already has target size, just copy
                shutil.copy(input_path, output_path)
            else:
                # Create a new white canvas
                new_img = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), (255, 255, 255))

                # Calculate position to paste the original image (centered)
                paste_x = (TARGET_WIDTH - width) // 2
                # paste_y = (TARGET_HEIGHT - height) // 2
                paste_y = 0 # vertical-align: top
                new_img.paste(img, (paste_x, paste_y))

                # Save the new image
                new_img.save(output_path)

            print(f"Processed: {filename}")

    except Exception as e:
        print(f"Skipping {filename}: {e}")
