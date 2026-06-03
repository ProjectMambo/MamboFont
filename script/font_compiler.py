#!/usr/bin/env python3
import sys
from pathlib import Path
try:
    import fontforge
except ImportError:
    print("\033[0;31m[!] Error: FontForge Python bindings not found.\033[0m")
    print("    Please run: 'sudo pacman -S fontforge'")
    sys.exit(1)

# Color codes for clean scannable terminal output
GREEN = '\033[0;32m'
RED   = '\033[0;31m'
BLUE  = '\033[0;34m'
NC    = '\033[0m' # No Color

# ----------------------------------------------------------------
# Icon source folders to scan (relative to drawings/)
# SVGs whose stem is a single ASCII character go to their
# matching codepoint; everything else lands in PUA (E000+)
# ----------------------------------------------------------------
ICON_DIRS = [
    "exported",
]

def get_sorted_svg_files(base_path):
    """Recursively scan directory in strict alphabetical order."""
    items = sorted(base_path.iterdir(), key=lambda x: x.name.lower())
    svg_files = []
    for item in items:
        if item.is_dir():
            svg_files.extend(get_sorted_svg_files(item))
        elif item.is_file() and item.suffix.lower() == ".svg":
            svg_files.append(item)
    return svg_files

def is_single_ascii(name):
    """Return True if the stem is exactly one printable ASCII character."""
    return len(name) == 1 and 0x20 <= ord(name) <= 0x7E

def main():
    # Exit if version argument is missing
    if len(sys.argv) < 2:
        print(f"{RED}Usage: {sys.argv[0]} [version_number]{NC}")
        sys.exit(1)

    version = sys.argv[1]

    # Establish structural paths
    script_dir   = Path(__file__).resolve().parent
    project_root = script_dir.parent
    svg_root     = project_root / "drawings"
    output_dir   = project_root / "ttf"

    # Create output directory
    output_dir.mkdir(exist_ok=True)
    output_ttf = output_dir / f"MamboFont_v{version}.ttf"

    print(f"{BLUE}------------------------------------------{NC}")
    print(f" Target:  {GREEN}MamboFont v{version}{NC}")
    print(f" Output:  {output_ttf.relative_to(project_root)}")
    print(f"{BLUE}------------------------------------------{NC}")

    # FontForge configuration
    font = fontforge.font()
    font.fontname   = "MamboFont"
    font.fullname   = "Mambo Font"
    font.familyname = "Mambo Font"
    font.version    = version

    # Canvas adjustments
    font.ascent  = 800
    font.descent = 200

    # ----------------------------------------------------------------
    # Parse standard alphabet directories
    # ----------------------------------------------------------------
    alphabet_dirs = [svg_root / "alphabet-lower", svg_root / "alphabet-upper"]
    for alpha_dir in alphabet_dirs:
        if not alpha_dir.exists():
            continue
        print(f"\n{BLUE}[*] Alphabet:{NC} {alpha_dir.name}")
        for file in sorted(alpha_dir.glob("*.svg"), key=lambda x: x.name.lower()):
            char_name = file.stem
            if char_name:
                char      = char_name[0]
                codepoint = ord(char)
                glyph     = font.createChar(codepoint, f"uni{codepoint:04X}")
                glyph.importOutlines(str(file.resolve()))
                glyph.width = 1000
                print(f"   -> U+{codepoint:04X}  {GREEN}{char}{NC}  ({file.name})")

    # ----------------------------------------------------------------
    # Parse icon directories
    # SVG stem is a single printable ASCII char -> mapped codepoint
    # Anything else -> next free PUA slot starting at U+E000
    # ----------------------------------------------------------------
    pua_counter = 0xE000  # Private Use Area start

    for icon_dir_name in ICON_DIRS:
        icon_dir = svg_root / icon_dir_name
        if not icon_dir.exists():
            print(f"\n{RED}[!] Icon dir not found, skipping:{NC} {icon_dir_name}")
            continue

        svg_files = get_sorted_svg_files(icon_dir)
        if not svg_files:
            print(f"\n   -> No SVGs found in {icon_dir_name}, skipping.")
            continue

        print(f"\n{BLUE}[*] Icons:{NC} {icon_dir_name}  ({len(svg_files)} glyphs)")

        for file in svg_files:
            stem = file.stem  # PascalCase name, e.g. "ArrowLeft"

            if is_single_ascii(stem):
                # Single ASCII character — map to its codepoint
                codepoint  = ord(stem)
                glyph_name = f"uni{codepoint:04X}"
                slot_label = f"U+{codepoint:04X}  (ASCII '{stem}')"
            else:
                # Multi-char or non-ASCII name — assign next PUA slot
                codepoint  = pua_counter
                glyph_name = f"uni{codepoint:04X}"
                slot_label = f"U+{codepoint:04X}  (PUA)"
                pua_counter += 1

            glyph = font.createChar(codepoint, glyph_name)
            glyph.importOutlines(str(file.resolve()))
            glyph.width = 1000

            print(f"   -> {slot_label}  {GREEN}{stem}{NC}")

    pua_used = pua_counter - 0xE000
    if pua_used:
        print(f"\n{BLUE}[i] PUA slots used:{NC} {pua_used}  (U+E000 – U+{pua_counter - 1:04X})")

    # Generate font asset
    font.generate(str(output_ttf))

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f"{GREEN}[+] Compilation successful!{NC}")
    print(f"{BLUE}------------------------------------------{NC}")

if __name__ == "__main__":
    main()