#!/bin/bash

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "[VENV] Creating virtual env ..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "[VENV] Already exists!"
fi

echo "[PERMISSIONS] Adding execute permissions to run.sh"
chmod +x run.sh
