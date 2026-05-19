#!/usr/bin/env bash

# Color codes for clean scannable terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
SVG_DIR="$(dirname "$SCRIPT_DIR")/svg"
DEST_DIR="$SVG_DIR/exported"
SOURCE="$SVG_DIR/drawing.svg"

# Exit if argument is empty
if [[ "$#" -eq 0 ]]; then
    echo -e "${RED}Usage: $0 LayerName1 LayerName2 ...${NC}" >&2
    exit 1
fi

# Captures every argument
TARGET_PARENTS=("$@")

for parent_name in "${TARGET_PARENTS[@]}"; do
    echo -e "\n${BLUE}[*] Parent Layer:${NC} ${GREEN}$parent_name${NC}"
    echo -e "${BLUE}------------------------------------------${NC}"

    # Find the XML ID of the big parent layer; Skip if not found
    PARENT_ID=$(xmlstarlet sel -t -v "//*[@inkscape:label='$parent_name']/@id" "$SOURCE" 2>/dev/null)
    if [[ -z "$PARENT_ID" ]]; then
        echo -e "${YELLOW}[!] Warning: Layer '$parent_name' not found. Skipping.${NC}" >&2
        continue
    fi

    # Create subfolder for parent
    TARGET_DEST="$DEST_DIR/$parent_name"
    mkdir -p "$TARGET_DEST"

    # Get immediate children layers; Skip if none
    CHILD_LAYERS=$(xmlstarlet sel -N ink="http://www.inkscape.org/namespaces/inkscape" \
        -t -m "//*[@id='$PARENT_ID']/*[@ink:groupmode='layer']" \
        -v "concat(@id, '|', @ink:label)" -n "$SOURCE" 2>/dev/null)
    if [[ -z "$CHILD_LAYERS" ]]; then
        echo -e " -> No sublayers found inside $parent_name."
        continue
    fi

    # Export each child layer into the subfolder
    echo "$CHILD_LAYERS" | while IFS='|' read -r layer_id layer_name; do
        [[ -z "$layer_id" || -z "$layer_name" ]] && continue

        echo -e " -> Exporting sublayer: ${GREEN}$layer_name${NC}"

        # Pipe source to Inkscape
        inkscape "$SOURCE" \
            --export-id="$layer_id" \
            --export-id-only \
            --export-area-page \
            --export-plain-svg \
            --export-type="svg" \
            --export-filename="$TARGET_DEST/${layer_name}.svg" > /dev/null 2>&1
    done
done

echo -e "\n${BLUE}------------------------------------------${NC}"
echo -e "${GREEN}[+] Export complete! Folders organized inside:${NC}"
echo -e " $DEST_DIR"
echo -e "${BLUE}------------------------------------------${NC}"