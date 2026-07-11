#!/bin/bash

# Snaketboi Game Launcher
# A Snake's Binding

echo "=========================================="
echo "  SNAKETBOI - A Snake's Binding"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python 3 to run this game."
    exit 1
fi

# Check for required Python packages
echo "Checking dependencies..."
python3 -c "import pygame" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: pygame is not installed!"
    echo "Installing pygame..."
    pip3 install pygame
    if [ $? -ne 0 ]; then
        echo "Failed to install pygame. Please install it manually:"
        echo "  pip3 install pygame"
        exit 1
    fi
fi

python3 -c "import PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Pillow (PIL) is not installed!"
    echo "Installing Pillow..."
    pip3 install Pillow
    if [ $? -ne 0 ]; then
        echo "Failed to install Pillow. Please install it manually:"
        echo "  pip3 install Pillow"
        exit 1
    fi
fi

python3 -c "import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: numpy is not installed!"
    echo "Installing numpy..."
    pip3 install numpy
    if [ $? -ne 0 ]; then
        echo "Failed to install numpy. Please install it manually:"
        echo "  pip3 install numpy"
        exit 1
    fi
fi

echo "All dependencies found!"
echo ""
echo "Launching game..."
echo ""

# Get the directory where the launcher is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Launch the game
python3 main.py

# Check if the game exited with an error
if [ $? -ne 0 ]; then
    echo ""
    echo "The game encountered an error. Press Enter to exit..."
    read
fi

