#!/usr/bin/env bash

# Color codes for clean scannable terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the absolute path
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Make script executable
chmod +x "$SCRIPT_DIR/mambo_font.py"

# Make a symlink for the main command
sudo ln -sf "$SCRIPT_DIR/mambo_font.py" /usr/local/bin/mbfont

echo -e "${BLUE}------------------------------------------${NC}"
echo -e " Tool:   ${GREEN}MamboFont${NC}"
echo -e " Source: $PROJECT_DIR"
echo -e "${GREEN}[+] Installation successful!${NC}"
echo -e "${BLUE}------------------------------------------${NC}"