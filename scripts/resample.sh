#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT/Assets/IconSet/Source" || exit 1
for f in *.png; do
    name="${f##*/}"
    xattr -c "$f"
    sips -z 144 144 "$f" --out "$PROJECT_ROOT/Assets/IconSet/Color/$name"
    echo "$f ... done"
done
