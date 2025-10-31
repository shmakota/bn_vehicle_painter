#!/bin/bash

# Vehicle Painter Launcher Script
# Creates a virtual environment, installs dependencies, and runs the application

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "Vehicle Painter for Cataclysm: Bright Nights"
echo "=============================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install requirements
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r "$SCRIPT_DIR/requirements.txt" --quiet
else
    echo "Warning: requirements.txt not found, skipping dependency installation."
fi

echo ""
echo "Starting Vehicle Painter..."
echo ""

# Run the application
python3 "$SCRIPT_DIR/main.py"

# Deactivate virtual environment when done
deactivate

