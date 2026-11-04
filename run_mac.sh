#!/usr/bin/env bash
# Stable ASCII Video Generator - macOS / Linux Runner
set -e

echo "========================================================"
echo "  Stable ASCII Video Generator (macOS / Linux)"
echo "========================================================"
echo

# 1. Check Python installation
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 could not be found."
    echo "Please install Python 3.10+ from https://www.python.org/ or via brew: 'brew install python'"
    exit 1
fi

# 2. Setup virtual environment if not present
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv ..."
    python3 -m venv .venv
fi

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Check and install dependencies
echo "Checking dependencies..."
pip install -r requirements.txt --quiet

# 5. Run the generator
echo
echo "Starting video conversion..."
echo

if [ $# -eq 0 ]; then
    python main.py
else
    python main.py "$@"
fi

echo
