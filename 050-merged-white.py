#!/usr/bin/env python3

r"""
chatGPT prompt:

create a python script to merge images.
process all images from an input directory.
write output files to a separate output directory.

some input images have multiple parts:
0336-00100.png
0336-00200.png
0336-00300.png
merge these 3 parts into the output image 0336.png

"merge" means: create a vertical stack from the input images

some input images have only one part
this part's filename always ends with "-00100.png"
in this case, copy the input image
and only remove the filename suffix "-00100.png"



If an input group has multiple parts: merge vertically.

If an input group has a single part: instead of just copying,
pair it with the next available single-part group,
and merge those two single-part images vertically into one output image.
only consecutive single-part images should be merged.

If there’s an odd leftover single-part image (no partner), just copy it as before.
"""

import os
import re
from PIL import Image

INPUT_DIR = "040-level-images"
OUTPUT_DIR = "050-merged-white"

# Regex to match filenames like 336-00100-ffffffff.png
pattern = re.compile(r"^(\d{3})-\d{5}-[0-9a-f]+\.png$")

def merge_images_vertically(images, out_path):
    widths = [img.width for img in images]
    heights = [img.height for img in images]

    max_width = max(widths)
    total_height = sum(heights)

    merged = Image.new("RGB", (max_width, total_height), (255, 255, 255))

    y_offset = 0
    for img in images:
        merged.paste(img, (0, y_offset))
        y_offset += img.height

    merged.save(out_path)


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Group images by base prefix (before the dash)
    groups = {}
    for fname in sorted(os.listdir(INPUT_DIR)):
        if pattern.match(fname):
            base = fname.split("-")[0]
            groups.setdefault(base, []).append(fname)

    single_part_bases = []

    # avoid output file collisions
    used_out_paths = []

    # Iterate over a static list of keys to avoid RuntimeError
    for base in list(groups.keys()):
        files = groups[base]
        files.sort()  # ensure order by suffix number
        n = len(files)

        if n == 1:
            single_part_bases.append(base)

        # elif n == 2:
        #     # Merge 2 parts

        elif True: # n >= 2
            # Merge multiple parts

            images = [Image.open(os.path.join(INPUT_DIR, f)) for f in files]
            out_name = base + ".png"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            assert out_path not in used_out_paths, f"duplicate out_path: {out_path!r}"
            used_out_paths.append(out_path)
            merge_images_vertically(images, out_path)
            print(f"Merged {len(files)} parts {files} -> {out_name}")
        elif n == 3:
            # Merge first 2 parts
            images = [Image.open(os.path.join(INPUT_DIR, files[0])), Image.open(os.path.join(INPUT_DIR, files[1]))]
            out_name = base + ".png"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            assert out_path not in used_out_paths, f"duplicate out_path: {out_path!r}"
            used_out_paths.append(out_path)
            merge_images_vertically(images, out_path)
            print(f"Merged first 2 parts of 3 {files[:2]} -> {out_name}")

            # Treat 3rd part as single-part image
            # FIXME where is 001_part3.png
            # FIXME where is 091_part3.png
            new_base = base + '_part3'
            print(f"Moving part 3 to a new group: {files[2]} -> {new_base}")
            groups[new_base] = [files[2]]
            single_part_bases.append(new_base)
        else: # n >= 3
            raise ValueError(f"too many parts: {len(files)} parts in files {files}")

    # Sort single-part bases numerically (ignore '_part3' suffix for sorting)
    def sort_key(b):
        return int(re.match(r'(\d+)', b).group(1))

    single_part_bases = sorted(single_part_bases, key=sort_key)

    r'''
    # Merge consecutive single-part images
    i = 0
    while i < len(single_part_bases):
        base1 = single_part_bases[i]
        f1 = groups[base1][0]
        img1 = Image.open(os.path.join(INPUT_DIR, f1))

        if i + 1 < len(single_part_bases):
            base2 = single_part_bases[i + 1]
            # Check if consecutive numbers
            num1 = int(re.match(r'(\d+)', base1).group(1))
            if num1 == 1:
                # dont merge page 1 and page 2
                # assume: output file does not exist
                out_name = f"{num1:03d}.png"
                out_path = os.path.join(OUTPUT_DIR, out_name)
                used_out_paths.append(out_path)
                img1.save(out_path)
                print(f"Copied single {f1} -> {out_name}")
                i += 1
                continue
            num2 = int(re.match(r'(\d+)', base2).group(1))
            if num2 == num1 + 1:
                f2 = groups[base2][0]
                img2 = Image.open(os.path.join(INPUT_DIR, f2))
                # out_name = f"{num1}_{num2}.png"
                # out_name = f"{num1:04d}_{num2:04d}.png"
                out_name = f"{num1:03d}_{num2:03d}.png"
                out_path = os.path.join(OUTPUT_DIR, out_name)
                assert out_path not in used_out_paths, f"duplicate out_path: {out_path!r}"
                used_out_paths.append(out_path)
                merge_images_vertically([img1, img2], out_path)
                print(f"Merged consecutive singles {f1} + {f2} -> {out_name}")
                i += 2
                continue

        # No consecutive match → save single
        # retry loop
        subpage = 1
        while True:
            if subpage == 1:
                out_name = re.match(r'(\d+)', base1).group(1) + ".png"
            else:
                # 001x2.png is sorted after 001.png
                out_name = re.match(r'(\d+)', base1).group(1) + f"x{subpage}.png"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            if out_path in used_out_paths:
                # collision = output file exists -> retry
                subpage += 1
                continue
            assert out_path not in used_out_paths, f"duplicate out_path: {out_path!r}"
            # output file does not exist
            used_out_paths.append(out_path)
            img1.save(out_path)
            print(f"Copied single {f1} -> {out_name}")
            i += 1
            break
    '''

    # dont merge single parts
    for base1 in single_part_bases:
        f1 = groups[base1][0]
        # TODO copy f1 from INPUT_DIR to OUTPUT_DIR
        img1 = Image.open(os.path.join(INPUT_DIR, f1))
        num1 = int(re.match(r'(\d+)', base1).group(1))
        out_name = f"{num1:03d}.png"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        used_out_paths.append(out_path)
        img1.save(out_path)
        print(f"Copied single {f1} -> {out_name}")

    # FIXME fill missing pages with empty pages
    # example: page 31 is missing: ... 28 29 30 32 33 34 ...

if __name__ == "__main__":
    main()
