#!/usr/bin/env bash

cd ./Assets/IconSet/Source || exit 1
for f in *.png; do
    name=$(basename "$f")
    xattr -c "$f"
    sips -z 144 144 "$f" --out ../Color/"${name}"
    echo "$f ... done"
done
