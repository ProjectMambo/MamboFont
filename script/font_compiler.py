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
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m' # No Color

def get_sorted_icon_paths(base_path):
    """Recursively scan directory in strict alphabetical order."""
    items = sorted(base_path.iterdir(), key=lambda x: x.name.lower())
    svg_files = []

    for item in items:
        if item.is_dir():
            svg_files.extend(get_sorted_icon_paths(item))
        elif item.is_file() and item.suffix.lower() == ".svg":
            svg_files.append(item)
            
    return svg_files

def main():
    # Exit if version argument is missing
    if len(sys.argv) < 2:
        print(f"{RED}Usage: {sys.argv[0]} [version_number]{NC}")
        sys.exit(1)
        
    version = sys.argv[1]

    # Establish structural paths
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    svg_root = project_root / "svg"
    output_dir = project_root / "ttf"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    output_ttf = output_dir / f"MamboFont_v{version}.ttf"

    print(f"{BLUE}------------------------------------------{NC}")
    print(f" Target:  {GREEN}MamboFont v{version}{NC}")
    print(f" Output:  {output_ttf.relative_to(project_root)}")
    print(f"{BLUE}------------------------------------------{NC}")

    # FontForge Configuration
    font = fontforge.font()
    font.fontname = "MamboFont"
    font.fullname = "Mambo Font"
    font.familyname = "Mambo Font"
    font.version = version
    
    # Canvas adjustments
    font.ascent = 800
    font.descent = 200

    # Parse standard alphabets
    alphabet_dirs = [svg_root / "alphabet-lower", svg_root / "alphabet-upper"]
    for alpha_dir in alphabet_dirs:
        if not alpha_dir.exists():
            continue
            
        print(f" [*] Processing: {alpha_dir.name}")
        for file in alpha_dir.glob("*.svg"):
            char_name = file.stem
            if char_name:
                char = char_name[0]
                codepoint = ord(char)
                
                glyph = font.createChar(codepoint, f"uni{codepoint:04X}")
                glyph.importOutlines(str(file.resolve()))
                glyph.width = 1000 

    # Generate font asset
    font.generate(str(output_ttf))
    
    print(f"{BLUE}------------------------------------------{NC}")
    print(f"{GREEN}[+] Compilation successful!{NC}")
    print(f"{BLUE}------------------------------------------{NC}")

if __name__ == "__main__":
    main()