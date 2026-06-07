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

# Collect all variant TTF files matching the provided version
mapfile -t VARIANT_FILES < <(find "$TTF_DIR" -maxdepth 1 -name "MamboFont-*_v${VERSION}.ttf" | sort)

if [ ${#VARIANT_FILES[@]} -eq 0 ]; then
    echo -e "${RED}[!] Error: No variant assets found for version v${VERSION} in $TTF_DIR${NC}" >&2
    exit 1
fi

# Build the zip archive
ZIP_NAME="MamboFont_v${VERSION}.zip"
ZIP_PATH="$TTF_DIR/$ZIP_NAME"

echo -e "${BLUE}------------------------------------------${NC}"
echo -e " Target:   ${GREEN}$TAG_NAME${NC}"
echo -e " Variants found:"
for f in "${VARIANT_FILES[@]}"; do
    echo -e "   ${GREEN}+${NC} $(basename "$f")"
done
echo -e " Archive:  $ZIP_NAME"
echo -e "${BLUE}------------------------------------------${NC}"

# Remove stale zip if it exists, then repack
rm -f "$ZIP_PATH"
zip -j "$ZIP_PATH" "${VARIANT_FILES[@]}"

# Create and push git tag
echo -e "${BLUE}[*] Tagging commit: $TAG_NAME...${NC}"
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

# Deploy GitHub Release — upload each variant TTF and the zip
echo -e "${BLUE}[*] Publishing release to GitHub...${NC}"
gh release create "$TAG_NAME" "${VARIANT_FILES[@]}" "$ZIP_PATH" \
    --title "$RELEASE_TITLE" \
    --notes "$NOTES"

echo -e "${BLUE}------------------------------------------${NC}"
echo -e "${GREEN}[+] Release complete!${NC}"
echo -e "${BLUE}------------------------------------------${NC}"