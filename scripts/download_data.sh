#!/usr/bin/env bash
# Download and extract NFL Big Data Bowl 2027 competition data into data/raw/.
# Credentials come from the environment only; nothing is printed or written to disk.
#   KAGGLE_API_TOKEN  (new-style "KGAT_..." token), or
#   KAGGLE_USERNAME + KAGGLE_KEY (if KAGGLE_KEY is a KGAT_ token it is mapped automatically)
set -euo pipefail
COMP="nfl-big-data-bowl-2027"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW="$ROOT/data/raw"

if [[ -z "${KAGGLE_API_TOKEN:-}" && "${KAGGLE_KEY:-}" == KGAT_* ]]; then
  export KAGGLE_API_TOKEN="$KAGGLE_KEY"
fi
command -v kaggle >/dev/null || pip install -q kaggle

mkdir -p "$RAW"
kaggle competitions download -c "$COMP" -p "$RAW"
unzip -tq "$RAW/$COMP.zip"
unzip -o -q "$RAW/$COMP.zip" -d "$RAW"
ls -la "$RAW/$COMP"
