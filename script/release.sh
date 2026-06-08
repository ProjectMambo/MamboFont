#!/usr/bin/env bash
set -e # Stop when any command fails

# Color codes for clean scannable terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Establish structural paths
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TTF_DIR="$PROJECT_ROOT/ttf"

# Parse full version number
VERSION=$1
if [ -z "$VERSION" ]; then
    echo -e "${RED}Usage: $0 [version]  e.g. $0 1.2.3${NC}" >&2
    exit 1
fi

TAG_NAME="v${VERSION}"
RELEASE_TITLE="Mambo Font $TAG_NAME"

# Exit if GitHub CLI is missing
if ! command -v gh &> /dev/null; then
    echo -e "${RED}[!] Error: GitHub CLI ('gh') is not installed.${NC}" >&2
    exit 1
fi

# Verify authentication status
if ! gh auth status &> /dev/null; then
    echo -e "${RED}[!] Error: Not authenticated with GitHub CLI. Run 'gh auth login'${NC}" >&2
    exit 1
fi

# Collect TTF and WOFF2 files separately
mapfile -t TTF_FILES   < <(find "$TTF_DIR" -maxdepth 1 -name "MamboFont-*_v${VERSION}.ttf"   | sort)
mapfile -t WOFF2_FILES < <(find "$TTF_DIR" -maxdepth 1 -name "MamboFont-*_v${VERSION}.woff2" | sort)

if [ ${#TTF_FILES[@]} -eq 0 ] && [ ${#WOFF2_FILES[@]} -eq 0 ]; then
    echo -e "${RED}[!] Error: No font assets found for version v${VERSION} in $TTF_DIR${NC}" >&2
    exit 1
fi

echo -e "${BLUE}------------------------------------------${NC}"
echo -e " Target:   ${GREEN}$TAG_NAME${NC}"

if [ ${#TTF_FILES[@]} -gt 0 ]; then
    echo -e " TTF Files:"
    for f in "${TTF_FILES[@]}"; do
        echo -e "   ${GREEN}+${NC} $(basename "$f")"
    done
fi

if [ ${#WOFF2_FILES[@]} -gt 0 ]; then
    echo -e " WOFF2 Files:"
    for f in "${WOFF2_FILES[@]}"; do
        echo -e "   ${GREEN}+${NC} $(basename "$f")"
    done
fi

echo -e "${BLUE}------------------------------------------${NC}"

# Build one zip per format
ZIP_FILES=()

if [ ${#TTF_FILES[@]} -gt 0 ]; then
    TTF_ZIP="$TTF_DIR/MamboFont_v${VERSION}_ttf.zip"
    rm -f "$TTF_ZIP"
    zip -j -q "$TTF_ZIP" "${TTF_FILES[@]}"
    ZIP_FILES+=("$TTF_ZIP")
    echo -e " -> Created Archive: $(basename "$TTF_ZIP")"
fi

if [ ${#WOFF2_FILES[@]} -gt 0 ]; then
    WOFF2_ZIP="$TTF_DIR/MamboFont_v${VERSION}_woff2.zip"
    rm -f "$WOFF2_ZIP"
    zip -j -q "$WOFF2_ZIP" "${WOFF2_FILES[@]}"
    ZIP_FILES+=("$WOFF2_ZIP")
    echo -e " -> Created Archive: $(basename "$WOFF2_ZIP")"
fi

# Combine everything into one release payload: raw files + zips
RELEASE_ASSETS=("${TTF_FILES[@]}" "${WOFF2_FILES[@]}" "${ZIP_FILES[@]}")

# Create and push git tag
echo -e "\n${BLUE}[*] Tagging commit: $TAG_NAME...${NC}"
git tag -a "$TAG_NAME" -m "Mambo Font release version $VERSION"
git push origin "$TAG_NAME" >/dev/null 2>&1

# Open nvim for release notes — same flow as git commit
# If saved empty, fall back to an auto-generated message
NOTES_FILE=$(mktemp /tmp/mambo_release_XXXXXX.md)
trap 'rm -f "$NOTES_FILE"' EXIT

# Seed the file with a comment hint (stripped if user leaves it)
cat > "$NOTES_FILE" << EOF
# Write your release notes above. Lines starting with # are ignored.
# Leave empty to auto-generate.
EOF

nvim "$NOTES_FILE"

# Strip comment lines and collapse blank lines
NOTES=$(grep -v '^#' "$NOTES_FILE" | sed '/^[[:space:]]*$/d')

if [ -z "$NOTES" ]; then
    NOTES="Mambo Font $VERSION"
    echo -e "${BLUE}[i] No notes provided — using auto-generated message.${NC}"
fi

# Deploy GitHub Release — raw TTFs, raw WOFF2s, and both zips
echo -e "${BLUE}[*] Publishing release to GitHub (${#RELEASE_ASSETS[@]} files)...${NC}"
gh release create "$TAG_NAME" "${RELEASE_ASSETS[@]}" \
    --title "$RELEASE_TITLE" \
    --notes "$NOTES"

echo -e "${BLUE}------------------------------------------${NC}"
echo -e "${GREEN}[+] Release complete!${NC}"
echo -e "${BLUE}------------------------------------------${NC}"