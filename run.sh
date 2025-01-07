#!/bin/bash

PROJECT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$PROJECT_DIR"

./venv/bin/python main.py "$@"
