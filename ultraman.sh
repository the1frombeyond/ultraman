#!/bin/bash
# ULTRAMAN CLI Launcher
# Created by install.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/main.py" "$@"