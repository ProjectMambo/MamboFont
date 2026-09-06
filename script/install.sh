#!/usr/bin/env bash
set -euo pipefail

source_path="$(dirname "$(readlink -f "$0")")/mbfont.py"
bin_dir="${MAMBOFONT_BIN_DIR:-$HOME/.local/bin}"
target="$bin_dir/mbfont"

mkdir -p "$bin_dir"
if [[ -e "$target" && ! -L "$target" ]]; then
    printf 'refusing to replace non-symlink: %s\n' "$target" >&2
    exit 1
fi
ln -sfn "$source_path" "$target"
printf 'installed %s -> %s\n' "$target" "$source_path"
