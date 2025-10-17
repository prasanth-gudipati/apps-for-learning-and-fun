#!/bin/bash
# Activation script for the virtual environment
# Usage: source activate_venv.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"

if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    echo "Virtual environment activated!"
    echo "Python location: $(which python)"
    echo "Pip location: $(which pip)"
    echo ""
    echo "To deactivate, run: deactivate"
else
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi