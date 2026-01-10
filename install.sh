#!/bin/bash

# Wave Reborn Installation Script
# This script installs the .desktop file and icon for Wave Reborn

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$SCRIPT_DIR/wave-reborn.desktop"
ICON_FILE="$SCRIPT_DIR/wave_icon.png"

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Wave Reborn - Installer          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Check if .desktop file exists
if [ ! -f "$DESKTOP_FILE" ]; then
    echo -e "${YELLOW}Error: wave-reborn.desktop not found!${NC}"
    exit 1
fi

# Check if icon file exists
if [ ! -f "$ICON_FILE" ]; then
    echo -e "${YELLOW}Warning: wave_icon.png not found!${NC}"
fi

# Create directories if they don't exist
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons

# Create a temporary .desktop file with correct paths
TEMP_DESKTOP=$(mktemp)
cat > "$TEMP_DESKTOP" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Wave Reborn
Comment=Professional Audio Mixer for Linux Streamers
GenericName=Audio Mixer
Exec=$SCRIPT_DIR/run_tray.sh
Icon=$SCRIPT_DIR/wave_icon.png
Terminal=false
StartupNotify=false
Categories=AudioVideo;Audio;Mixer;
Keywords=audio;mixer;streaming;pulseaudio;
EOF

# Copy .desktop file
echo -e "${BLUE}[1/3]${NC} Installing application launcher..."
cp "$TEMP_DESKTOP" ~/.local/share/applications/wave-reborn.desktop
chmod +x ~/.local/share/applications/wave-reborn.desktop
rm "$TEMP_DESKTOP"

# Copy icon if it exists
if [ -f "$ICON_FILE" ]; then
    echo -e "${BLUE}[2/3]${NC} Installing application icon..."
    cp "$ICON_FILE" ~/.local/share/icons/wave-reborn.png
fi

# Update desktop database
echo -e "${BLUE}[3/3]${NC} Updating application menu..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications
    echo -e "${GREEN}✓ Desktop database updated${NC}"
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Installation Complete! 🎉         ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Wave Reborn${NC} is now available in your application menu!"
echo ""
echo -e "To uninstall, run: ${YELLOW}./uninstall.sh${NC}"
echo ""
