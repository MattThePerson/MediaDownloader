#!/bin/bash

INSTALL_NAME=mdown
INSTALL_BIN_DIR=~/WhisperaHQ/bin # change this to folder on path

set -e

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

echo "[SYMLINK] Add adding symbolic link to run.sh"
mkdir -p "$INSTALL_BIN_DIR"
ln -sf "$TOOLS_DIR/run.sh" "$INSTALL_BIN_DIR/$INSTALL_NAME"

echo
echo "Done! Run utility with \"$INSTALL_NAME\""
echo

