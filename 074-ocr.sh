#!/usr/bin/env bash

set -eu

cd "$(dirname "$0")"
# src=020-white
src=070-page-numbers
dst=$(basename "$0" .sh)

mkdir -p $dst

scan_format=png
ocr_lang=deu+eng

./tessdata_best.sh $(echo "$ocr_lang" | tr '+' ' ')

# the page image path is relative to the workdir
# <div class='ocr_page' id='page_1' title='image "../070-deskew/005.tiff"; ...'>
# patch paths:
# sed -i -E "s|(<div class='ocr_page' id='page_[0-9]+' title='image \")[^/]+/([0-9]+\.tiff\";)|\1../070-deskew/\2|" 080-ocr/*.hocr
cd "$dst"

t1=$(date --utc +%s)
num_pages=0

for inp in ../"$src"/*."$scan_format"; do

  # FIXME use $num_pages and $scan_format
  # page_number=${inp%.tiff}
  page_number=${inp%.png}
  page_number=${page_number##*/}
  page_number=${page_number#0}
  page_number=${page_number#0}

  out=${inp##*/}
  # out=${out%.tiff}
  out=${out%.png}
  # out=$dst/$out

  out1=$out.hocr
  if ! [ -e $out1 ]; then
    # TODO? use OCRopus https://github.com/ocropus-archive/DUP-ocropy
    echo + \
    tesseract "$inp" - -c tessedit_create_hocr=1 -l "$ocr_lang" --tessdata-dir ../tessdata_best
    tesseract "$inp" - -c tessedit_create_hocr=1 -l "$ocr_lang" --tessdata-dir ../tessdata_best >$out1
    # tesseract "$inp" - -c tessedit_create_hocr=1 -l "$ocr_lang" --oem 1 --psm 6 --tessdata-dir ../tessdata_best >$out1
  fi

  num_pages=$((num_pages + 1))

  # [ "$page_number" = 10 ] && break # debug

done

t2=$(date --utc +%s)
echo "done $num_pages pages in $((t2 - t1)) seconds"
