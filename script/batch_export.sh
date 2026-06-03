#!/usr/bin/env bash

# Color codes for clean scannable terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
SVG_DIR="$(dirname "$SCRIPT_DIR")/drawings"
DEST_DIR="$SVG_DIR/exported"
SOURCE="$SVG_DIR/drawing.svg"

# ----------------------------------------------------------------
# Make a temp copy with all display:none stripped so hidden
# layers and paths export with their actual content, not blank
# ----------------------------------------------------------------
WORK=$(mktemp /tmp/export_icons_XXXXXX.svg)
trap 'rm -f "$WORK"' EXIT

# Remove display:none from style attributes (e.g. style="display:none")
# and also bare display="none" attributes — covers both Inkscape variants
xmlstarlet ed \
    -u '//*[contains(@style,"display:none")]/@style' \
    -x 'concat(substring-before(.,"display:none"), substring-after(.,"display:none"))' \
    -d '//*/@display[.="none"]' \
    "$SOURCE" > "$WORK"

# XPath snippets — local-name() avoids namespace registration issues
# across different xmlstarlet builds and SVG namespace declarations
IS_LAYER='@*[local-name()="groupmode"]="layer"'
LABEL='@*[local-name()="label"]'

# ----------------------------------------------------------------
# Find the root "Other" layer (PascalCase in Inkscape)
# ----------------------------------------------------------------
OTHER_ID=$(xmlstarlet sel \
    -t -v "//*[$IS_LAYER][$LABEL='Other']/@id" \
    "$WORK" 2>/dev/null)

if [[ -z "$OTHER_ID" ]]; then
    echo -e "${RED}[!] Error: Root layer 'Other' not found in $SOURCE${NC}" >&2
    exit 1
fi

echo -e "\n${BLUE}[*] Root layer found:${NC} ${GREEN}Other${NC} (id: $OTHER_ID)"
echo -e "${BLUE}------------------------------------------${NC}"

# ----------------------------------------------------------------
# Get all category layers directly under "Other"
# ----------------------------------------------------------------
CATEGORY_LAYERS=$(xmlstarlet sel \
    -t -m "//*[@id='$OTHER_ID']/*[$IS_LAYER]" \
    -v "concat(@id, '|', $LABEL)" -n \
    "$WORK" 2>/dev/null)

if [[ -z "$CATEGORY_LAYERS" ]]; then
    echo -e "${YELLOW}[!] Warning: No category layers found inside 'Other'. Exiting.${NC}" >&2
    exit 1
fi

# ----------------------------------------------------------------
# Loop over each category layer
# ----------------------------------------------------------------
echo "$CATEGORY_LAYERS" | while IFS='|' read -r cat_id cat_name; do
    [[ -z "$cat_id" || -z "$cat_name" ]] && continue

    # Normalise: trim whitespace then lowercase
    cat_folder=$(echo "$cat_name" | xargs | tr '[:upper:]' '[:lower:]')

    echo -e "\n${BLUE}[*] Category:${NC} ${GREEN}$cat_folder${NC}"
    echo -e "${BLUE}------------------------------------------${NC}"

    # Create category folder
    CAT_DEST="$DEST_DIR/$cat_folder"
    mkdir -p "$CAT_DEST"

    # ----------------------------------------------------------------
    # Get all group layers directly under this category
    # ----------------------------------------------------------------
    GROUP_LAYERS=$(xmlstarlet sel \
        -t -m "//*[@id='$cat_id']/*[$IS_LAYER]" \
        -v "concat(@id, '|', $LABEL)" -n \
        "$WORK" 2>/dev/null)

    if [[ -z "$GROUP_LAYERS" ]]; then
        echo -e " -> ${YELLOW}No group layers found inside '$cat_folder'. Skipping.${NC}"
        continue
    fi

    # ----------------------------------------------------------------
    # Loop over each group layer inside the category
    # ----------------------------------------------------------------
    echo "$GROUP_LAYERS" | while IFS='|' read -r grp_id grp_name; do
        [[ -z "$grp_id" || -z "$grp_name" ]] && continue

        grp_folder=$(echo "$grp_name" | xargs | tr '[:upper:]' '[:lower:]')

        echo -e "\n  ${BLUE}[>] Group layer:${NC} ${GREEN}$grp_folder${NC}"

        # ------------------------------------------------------------
        # Get all direct path/shape children of this group layer
        # Paths carry their icon name as inkscape:label
        # ------------------------------------------------------------
        PATH_ENTRIES=$(xmlstarlet sel \
            -t -m "//*[@id='$grp_id']/*[$LABEL]" \
            -v "concat(@id, '|', $LABEL)" -n \
            "$WORK" 2>/dev/null)

        if [[ -z "$PATH_ENTRIES" ]]; then
            echo -e "     -> ${YELLOW}No labelled paths found in '$grp_folder'. Skipping.${NC}"
            continue
        fi

        # Count valid entries
        PATH_COUNT=$(echo "$PATH_ENTRIES" | grep -c '[^[:space:]]')

        # Decide output location:
        # 3+ paths -> category/groupname/  (subfolder named after the group)
        # 1-2 paths -> category/           (flat, no extra nesting)
        if [[ "$PATH_COUNT" -ge 3 ]]; then
            EXPORT_DEST="$CAT_DEST/$grp_folder"
            mkdir -p "$EXPORT_DEST"
            echo -e "     -> $PATH_COUNT paths — exporting into subfolder: ${GREEN}$grp_folder/${NC}"
        else
            EXPORT_DEST="$CAT_DEST"
            echo -e "     -> $PATH_COUNT path(s) — exporting flat into: ${GREEN}$cat_folder/${NC}"
        fi

        # ------------------------------------------------------------
        # Export each path individually by its element ID
        # Filename taken from inkscape:label (PascalCase preserved)
        # Inkscape reads from WORK so hidden elements are visible
        # ------------------------------------------------------------
        echo "$PATH_ENTRIES" | while IFS='|' read -r path_id path_label; do
            [[ -z "$path_id" || -z "$path_label" ]] && continue

            icon_name=$(echo "$path_label" | xargs)

            echo -e "       -> Exporting: ${GREEN}${icon_name}.svg${NC}"

            inkscape "$WORK" \
                --export-id="$path_id" \
                --export-id-only \
                --export-area-page \
                --export-plain-svg \
                --export-type="svg" \
                --export-filename="$EXPORT_DEST/${icon_name}.svg" > /dev/null 2>&1
        done

    done
done

echo -e "\n${BLUE}------------------------------------------${NC}"
echo -e "${GREEN}[+] Export complete! Folders organised inside:${NC}"
echo -e "    $DEST_DIR"
echo -e "${BLUE}------------------------------------------${NC}"