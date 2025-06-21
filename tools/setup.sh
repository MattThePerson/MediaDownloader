#!/bin/bash

# TOOLS_DIR="$(dirname "$0")"
TOOLS_DIR="$(dirname "$(readlink -f "$0")")"
cd "$TOOLS_DIR/.."

if [ ! -d ".venv" ]; then
    echo "[VENV] Creating virtual env ..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    echo "[VENV] Already exists!"
fi

echo "[PERMISSIONS] Adding execute permissions to run.sh"
chmod +x tools/run.sh

echo
echo "Done. Add symbolic link to run.sh with: ln -sf "$TOOLS_DIR/run.sh" PATH_TO_SYMLINK"
echo

