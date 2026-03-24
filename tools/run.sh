#!/bin/bash

TOOLS_DIR="$(dirname "$(readlink -f "$0")")"
cd "$TOOLS_DIR/.."

if [ ! -d ".venv" ]; then
    echo "ERROR: No '.venv' found, please run 'tools/setup.sh'"
    exit
fi

./.venv/bin/python main.py "$@"
