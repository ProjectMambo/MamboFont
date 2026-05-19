#!/usr/bin/env bash
set -e # Stop when any command fails

# Color codes for clean scannable terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Establish structural paths
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TTF_DIR="$PROJECT_ROOT/ttf"

# Parse base version number
BASE_VERSION=$1
if [ -z "$BASE_VERSION" ]; then
    echo -e "${RED}Usage: $0 [base_version]${NC}" >&2
    exit 1
fi

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

# Ensure compiled font asset exists
EXPECTED_FILE="$TTF_DIR/MamboFont_v${BASE_VERSION}.ttf"
if [ ! -f "$EXPECTED_FILE" ]; then
    echo -e "${RED}[!] Error: Asset not found: MamboFont_v${BASE_VERSION}.ttf${NC}" >&2
    exit 1
fi

# Fetch and calculate auto-increment version tags
LATEST_TAG=$(gh release list --limit 100 | awk '{print $1}' | grep -E "^v${BASE_VERSION}(\.|$)" | sort -V | tail -n 1 || true)

if [ -z "$LATEST_TAG" ]; then
    FINAL_VERSION="${BASE_VERSION}.0"
else
    CURRENT_VERSION="${LATEST_TAG#v}"
    
    IFS='.' read -r -a parts <<< "$CURRENT_VERSION"
    if [ "${#parts[@]}" -le 2 ]; then
        PATCH=0
    else
        PATCH=${parts[2]}
    fi
    
    NEXT_PATCH=$((PATCH + 1))
    FINAL_VERSION="${parts[0]}.${parts[1]}.${NEXT_PATCH}"
fi

TAG_NAME="v${FINAL_VERSION}"
RELEASE_TITLE="Mambo Font $TAG_NAME"

echo -e "${BLUE}------------------------------------------${NC}"
echo -e " Base Ver: $BASE_VERSION"
echo -e " Target:   ${GREEN}$TAG_NAME${NC}"
echo -e " Asset:    MamboFont_v${BASE_VERSION}.ttf"
echo -e "${BLUE}------------------------------------------${NC}"

# Create and push git tag
echo -e "${BLUE}[*] Tagging commit: $TAG_NAME...${NC}"
git tag -a "$TAG_NAME" -m "Mambo Font release version $FINAL_VERSION (Base: $BASE_VERSION)"
git push origin "$TAG_NAME" >/dev/null 2>&1

# Deploy GitHub Release and upload asset
echo -e "${BLUE}[*] Publishing release to GitHub...${NC}"
gh release create "$TAG_NAME" "$EXPECTED_FILE" \
    --title "$RELEASE_TITLE" \
    --notes "Automated patch update tracking deployment for Mambo Font $FINAL_VERSION."

echo -e "${BLUE}------------------------------------------${NC}"
echo -e "${GREEN}[+] Auto-increment release complete!${NC}"
echo -e "${BLUE}------------------------------------------${NC}"