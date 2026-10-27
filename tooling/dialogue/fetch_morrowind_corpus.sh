#!/usr/bin/env bash
# Copy the tagged Morrowind dialogue corpus (UESP pull, 7,952 verbatim lines) from the old repo into
# $ARGONIA_PRIVATE/dialogue/. Morrowind text is never committed here (decision 0003, docs/legal-and-sourcing.md).
#   tooling/dialogue/fetch_morrowind_corpus.sh [path-to-elder-souls-argonia checkout]
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
src="${1:-$repo_root/../elder-souls-argonia}"
dest="${ARGONIA_PRIVATE:-$repo_root/private}/dialogue"
mkdir -p "$dest"
cp "$src/world/sources/dialogue/exemplars/morrowind-full.json" \
   "$src/world/sources/dialogue/exemplars/morrowind.json" \
   "$src/world/sources/lore/morrowind-dialogue-corpus-full.md" "$dest/"
echo "corpus in $dest"
