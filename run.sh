#!/bin/bash
# Hardware Control Center Launcher
# This script activates the virtual environment and runs the application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run ./install.sh first to set up the application."
    exit 1
fi

# Activate virtual environment and run the application
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 main.py "$@"
deactivate
