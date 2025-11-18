#!/bin/bash
# Hardware Control Center Installation Script

set -e

echo "========================================"
echo "Hardware Control Center Installation"
echo "========================================"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This script is designed for Linux systems"
    exit 1
fi

# Check Python version
echo "[1/6] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 7) else 1)'; then
    echo "Error: Python 3.7 or higher required"
    exit 1
fi

# Install system dependencies
echo ""
echo "[2/6] Installing system dependencies..."
echo "This requires sudo privileges"

if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-pyqt5 \
        libusb-1.0-0 \
        i2c-tools \
        libi2c-dev \
        python3-dev \
        libgpiod2 \
        2>/dev/null || echo "Some packages may already be installed"
elif command -v yum &> /dev/null; then
    sudo yum install -y \
        python3-pip \
        python3-qt5 \
        libusb \
        i2c-tools \
        2>/dev/null || echo "Some packages may already be installed"
else
    echo "Warning: Unknown package manager. Please install dependencies manually:"
    echo "  - Python 3.7+"
    echo "  - PyQt5"
    echo "  - libusb"
    echo "  - i2c-tools"
fi

# Install Python dependencies
echo ""
echo "[3/6] Installing Python dependencies..."
pip3 install --user -r requirements.txt

# Add user to required groups
echo ""
echo "[4/6] Adding user to hardware access groups..."
current_user=$(whoami)

for group in dialout i2c spi plugdev gpio; do
    if getent group $group > /dev/null 2>&1; then
        sudo usermod -a -G $group $current_user 2>/dev/null || true
        echo "Added to group: $group"
    fi
done

# Create desktop launcher (optional)
echo ""
echo "[5/6] Creating desktop launcher..."

desktop_file="$HOME/.local/share/applications/hardware-control-center.desktop"
mkdir -p "$(dirname "$desktop_file")"

cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Hardware Control Center
Comment=Unified hardware management interface
Exec=python3 $(pwd)/main.py
Icon=applications-system
Terminal=false
Categories=System;Utility;
EOF

echo "Desktop launcher created"

# Make main.py executable
echo ""
echo "[6/6] Setting permissions..."
chmod +x main.py

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "IMPORTANT: You must logout and login for group changes to take effect!"
echo ""
echo "To run the application:"
echo "  cd $(pwd)"
echo "  python3 main.py"
echo ""
echo "Or find 'Hardware Control Center' in your application menu"
echo ""
echo "Configuration file: configs/default.json"
echo ""
echo "For troubleshooting, see README.md"
echo ""
