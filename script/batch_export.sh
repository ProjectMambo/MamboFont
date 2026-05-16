#!/bin/bash

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SVG_DIR=$(dirname "$SCRIPT_DIR")/svg
DEST_DIR="$SVG_DIR/exported"

SOURCE="$SVG_DIR/drawing.svg"

# Exit if argument empty
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 LayerName1 LayerName2 LayerName3 ..."
    echo "Example: $0 AlphabetUpper AlphabetLower Numbers"
    exit 1
fi

# Captures every argument
TARGET_PARENTS=("$@")

for parent_name in "${TARGET_PARENTS[@]}"; do
    echo "-----------------------------------------------"
    echo "Looking for parent layer: $parent_name"

    # Find the XML ID of the big parent layer; Skip if not found
    PARENT_ID=$(xmlstarlet sel -t -v "//*[@inkscape:label='$parent_name']/@id" "$SOURCE" 2>/dev/null)
    if [[ -z "$PARENT_ID" ]]; then
        echo "Warning: Could not find layer '$parent_name' in the SVG file. Skipping."
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
        echo " -> No sublayers found inside $parent_name."
        continue
    fi

    # Export each child layer into the subfolder
    echo "$CHILD_LAYERS" | while IFS='|' read -r layer_id layer_name; do
        [[ -z "$layer_id" || -z "$layer_name" ]] && continue

        echo " -> Exporting sublayer: $layer_name into $parent_name/"

        # Pipe source to Inkscape
        inkscape "$SOURCE" \
            --export-id="$layer_id" \
            --export-id-only \
            --export-area-page \
            --export-plain-svg \
            --export-type="svg" \
            --export-filename="$TARGET_DEST/${layer_name}.svg"
    done
done

echo "-----------------------------------------------"
echo "Done! Folders organized inside $DEST_DIR"