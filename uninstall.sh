#!/bin/bash

# Wave Reborn Uninstallation Script
# This script removes the .desktop file and autostart entry

set -e

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Wave Reborn - Uninstaller        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Remove .desktop file
if [ -f ~/.local/share/applications/wave-reborn.desktop ]; then
    echo -e "${BLUE}[1/3]${NC} Removing application launcher..."
    rm ~/.local/share/applications/wave-reborn.desktop
    echo -e "${GREEN}✓ Application launcher removed${NC}"
else
    echo -e "${YELLOW}⚠ Application launcher not found${NC}"
fi

# Remove icon
if [ -f ~/.local/share/icons/wave-reborn.png ]; then
    echo -e "${BLUE}[2/3]${NC} Removing application icon..."
    rm ~/.local/share/icons/wave-reborn.png
    echo -e "${GREEN}✓ Application icon removed${NC}"
else
    echo -e "${YELLOW}⚠ Application icon not found${NC}"
fi

# Remove autostart file
if [ -f ~/.config/autostart/wave-reborn.desktop ]; then
    echo -e "${BLUE}[3/3]${NC} Removing autostart entry..."
    rm ~/.config/autostart/wave-reborn.desktop
    echo -e "${GREEN}✓ Autostart entry removed${NC}"
else
    echo -e "${YELLOW}⚠ Autostart entry not found${NC}"
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Uninstallation Complete!         ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo -e "Wave Reborn has been removed from your system."
echo ""
