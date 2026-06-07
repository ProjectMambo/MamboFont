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
# Root layers to skip entirely (Family is handled separately)
# ----------------------------------------------------------------
SKIP_LAYERS=("Base")

# ----------------------------------------------------------------
# Make a temp copy with all display:none stripped
# ----------------------------------------------------------------
WORK=$(mktemp /tmp/export_icons_XXXXXX.svg)
trap 'rm -f "$WORK"' EXIT

xmlstarlet ed \
    -u '//*[contains(@style,"display:none")]/@style' \
    -x 'concat(substring-before(.,"display:none"), substring-after(.,"display:none"))' \
    -d '//*/@display[.="none"]' \
    "$SOURCE" > "$WORK"

IS_LAYER='@*[local-name()="groupmode"]="layer"'
LABEL='@*[local-name()="label"]'

# ----------------------------------------------------------------
# Get all top-level layers
# ----------------------------------------------------------------
ROOT_LAYERS=$(xmlstarlet sel \
    -t -m "/svg:svg/*[$IS_LAYER]" \
    -v "concat(@id, '|', $LABEL)" -n \
    --ns svg=http://www.w3.org/2000/svg \
    "$WORK" 2>/dev/null)

if [[ -z "$ROOT_LAYERS" ]]; then
    ROOT_LAYERS=$(xmlstarlet sel \
        -t -m "//*[local-name()='svg']/*[$IS_LAYER]" \
        -v "concat(@id, '|', $LABEL)" -n \
        "$WORK" 2>/dev/null)
fi

if [[ -z "$ROOT_LAYERS" ]]; then
    echo -e "${RED}[!] Error: No root layers found in $SOURCE${NC}" >&2
    exit 1
fi

# ----------------------------------------------------------------
# export_paths_from_layer <layer_id> <dest_dir>
#
# Three things can live inside a layer — all handled:
#   A) Direct path with label          -> export by label
#   B) Sublayer containing path(s)     -> export each path by its label
#      (sublayer name ignored; used for W/W nesting style)
#   C) Empty sublayer (no children)    -> export the sublayer itself by its label
#      (used for space, return, .notdef-as-empty, etc.)
#
# A layer can mix A+B+C freely.
# ----------------------------------------------------------------
export_paths_from_layer() {
    local layer_id="$1"
    local dest_dir="$2"

    mkdir -p "$dest_dir"

    local exported_any=false

    # ---- A) Direct labelled non-layer children ----
    local DIRECT
    DIRECT=$(xmlstarlet sel \
        -t -m "//*[@id='$layer_id']/*[$LABEL][not($IS_LAYER)]" \
        -v "concat(@id, '|', $LABEL)" -n \
        "$WORK" 2>/dev/null | grep -v '^[[:space:]]*$')

    if [[ -n "$DIRECT" ]]; then
        local count
        count=$(echo "$DIRECT" | grep -c '[^[:space:]]')
        echo -e "     -> $count direct path(s)"
        while IFS='|' read -r path_id path_label; do
            [[ -z "$path_id" || -z "$path_label" ]] && continue
            local icon_name
            icon_name=$(echo "$path_label" | xargs)
            echo -e "       -> Exporting: ${GREEN}${icon_name}.svg${NC}"
            inkscape "$WORK" \
                --export-id="$path_id" \
                --export-id-only \
                --export-area-page \
                --export-plain-svg \
                --export-type="svg" \
                --export-filename="$dest_dir/${icon_name}.svg" > /dev/null 2>&1
            exported_any=true
        done <<< "$DIRECT"
    fi

    # ---- B+C) Child layers ----
    local CHILD_LAYERS
    CHILD_LAYERS=$(xmlstarlet sel \
        -t -m "//*[@id='$layer_id']/*[$IS_LAYER]" \
        -v "concat(@id, '|', $LABEL)" -n \
        "$WORK" 2>/dev/null | grep -v '^[[:space:]]*$')

    if [[ -n "$CHILD_LAYERS" ]]; then
        while IFS='|' read -r cl_id cl_name; do
            [[ -z "$cl_id" || -z "$cl_name" ]] && continue

            cl_label=$(echo "$cl_name" | xargs | sed 's/^-*//')

            # Check if this child layer has its own labelled path children
            local CL_PATHS
            CL_PATHS=$(xmlstarlet sel \
                -t -m "//*[@id='$cl_id']/*[$LABEL][not($IS_LAYER)]" \
                -v "concat(@id, '|', $LABEL)" -n \
                "$WORK" 2>/dev/null | grep -v '^[[:space:]]*$')

            if [[ -n "$CL_PATHS" ]]; then
                # B) sublayer has paths — export each by its label
                while IFS='|' read -r path_id path_label; do
                    [[ -z "$path_id" || -z "$path_label" ]] && continue
                    local icon_name
                    icon_name=$(echo "$path_label" | xargs)
                    echo -e "       -> Exporting (nested): ${GREEN}${icon_name}.svg${NC}"
                    inkscape "$WORK" \
                        --export-id="$path_id" \
                        --export-id-only \
                        --export-area-page \
                        --export-plain-svg \
                        --export-type="svg" \
                        --export-filename="$dest_dir/${icon_name}.svg" > /dev/null 2>&1
                done <<< "$CL_PATHS"
            else
                # C) empty sublayer — export the layer itself, named by its label
                echo -e "       -> Exporting (empty layer): ${GREEN}${cl_label}.svg${NC}"
                inkscape "$WORK" \
                    --export-id="$cl_id" \
                    --export-id-only \
                    --export-area-page \
                    --export-plain-svg \
                    --export-type="svg" \
                    --export-filename="$dest_dir/${cl_label}.svg" > /dev/null 2>&1
            fi
            exported_any=true
        done <<< "$CHILD_LAYERS"
    fi

    if [[ "$exported_any" == false ]]; then
        # Layer itself is totally empty — export it as a single SVG
        local layer_label
        layer_label=$(xmlstarlet sel \
            -t -v "//*[@id='$layer_id']/@*[local-name()='label']" \
            "$WORK" 2>/dev/null | xargs | sed 's/^-*//')
        echo -e "     -> ${YELLOW}Truly empty — exporting layer as:${NC} ${GREEN}${layer_label}.svg${NC}"
        inkscape "$WORK" \
            --export-id="$layer_id" \
            --export-id-only \
            --export-area-page \
            --export-plain-svg \
            --export-type="svg" \
            --export-filename="$dest_dir/${layer_label}.svg" > /dev/null 2>&1
    fi
}

# ----------------------------------------------------------------
# Pass 1 — collect Family layer categories into FAMILY_CATS
# Use process substitution (not pipe) so the array stays in scope
# ----------------------------------------------------------------
FAMILY_ID=$(xmlstarlet sel \
    -t -v "//*[$IS_LAYER][$LABEL='Family']/@id" \
    "$WORK" 2>/dev/null)

declare -A FAMILY_CATS   # cat_folder -> cat_id

if [[ -n "$FAMILY_ID" ]]; then
    echo -e "\n${BLUE}[*] Found Family layer — collecting shared glyphs${NC}"
    echo -e "${BLUE}------------------------------------------${NC}"

    while IFS='|' read -r cat_id cat_name; do
        [[ -z "$cat_id" || -z "$cat_name" ]] && continue
        cat_key=$(echo "$cat_name" | xargs | tr '[:upper:]' '[:lower:]' | sed 's/^-*//' | tr -d ' ')
        FAMILY_CATS["$cat_key"]="$cat_id"
        echo -e "  -> Shared category: ${GREEN}$cat_key${NC}"
    done < <(xmlstarlet sel \
        -t -m "//*[@id='$FAMILY_ID']/*[$IS_LAYER]" \
        -v "concat(@id, '|', $LABEL)" -n \
        "$WORK" 2>/dev/null)
fi

# ----------------------------------------------------------------
# Pass 2 — process weight layers
# Use process substitution so FAMILY_CATS is visible inside
# ----------------------------------------------------------------
echo -e "\n${BLUE}[*] Processing weight layers${NC}"
echo -e "${BLUE}------------------------------------------${NC}"

while IFS='|' read -r root_id root_name; do
    [[ -z "$root_id" || -z "$root_name" ]] && continue

    root_name_trimmed=$(echo "$root_name" | xargs)

    # Skip Family and anything in SKIP_LAYERS
    if [[ "$root_name_trimmed" == "Family" ]]; then continue; fi
    skip=false
    for s in "${SKIP_LAYERS[@]}"; do
        [[ "$root_name_trimmed" == "$s" ]] && skip=true && break
    done
    $skip && echo -e "\n${YELLOW}[~] Skipping:${NC} $root_name_trimmed" && continue

    root_folder=$(echo "$root_name_trimmed" | tr '[:upper:]' '[:lower:]')
    ROOT_DEST="$DEST_DIR/$root_folder"

    echo -e "\n${BLUE}[*] Weight:${NC} ${GREEN}$root_name_trimmed${NC} -> exported/$root_folder/"
    echo -e "${BLUE}------------------------------------------${NC}"

    # Step A — write Family glyphs first (baseline)
    for cat_key in "${!FAMILY_CATS[@]}"; do
        cat_id="${FAMILY_CATS[$cat_key]}"
        echo -e "\n  ${BLUE}[F] Family->$cat_key${NC} (shared)"
        export_paths_from_layer "$cat_id" "$ROOT_DEST/$cat_key"
    done

    # Step B — write weight-specific layers (overrides Family by overwriting files)
    while IFS='|' read -r child_id child_name; do
        [[ -z "$child_id" || -z "$child_name" ]] && continue
        child_folder=$(echo "$child_name" | xargs | tr '[:upper:]' '[:lower:]' | sed 's/^-*//' | tr -d ' ')
        echo -e "\n  ${BLUE}[>] $child_folder${NC} (weight-specific, overrides Family)"
        export_paths_from_layer "$child_id" "$ROOT_DEST/$child_folder"
    done < <(xmlstarlet sel \
        -t -m "//*[@id='$root_id']/*[$IS_LAYER]" \
        -v "concat(@id, '|', $LABEL)" -n \
        "$WORK" 2>/dev/null)

done < <(echo "$ROOT_LAYERS")

echo -e "\n${BLUE}------------------------------------------${NC}"
echo -e "${GREEN}[+] Export complete!${NC}"
echo -e "    $DEST_DIR"
echo -e "${BLUE}------------------------------------------${NC}"