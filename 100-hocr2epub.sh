#!/usr/bin/env bash

set -eu
# set -x # debug

# src=030-ocr-white
src=074-ocr
dst=$(basename "$0" .sh).epub

doc_title="$(head -n1 readme.md | sed 's/^#\s*//')"

if [ -e "$dst" ]; then
  echo "error: output exists: $dst"
  exit 1
fi

args=(
  # hocr-to-epub-fxl
  /home/user/src/archive-hocr-tools/bin/hocr-to-epub-fxl
  --output "$dst"
  # --scale 0.5
  # --image-format avif
  # --text-format svg
  --doc-title "$doc_title"
  # --doc-modified "$(date -Is)"
  --doc-modified "$(git show -s --format=%cI HEAD)"
  --doc-isbn 9798306310756 # print version
  --color-image-pages 258
  $src/*.hocr
)

"${args[@]}" "$@"
echo "done $dst"

rm -rf $dst.unzip
mkdir $dst.unzip
cd $dst.unzip
unzip -q ../$dst
cd ..

echo "done ./$dst.unzip/index.xhtml"
