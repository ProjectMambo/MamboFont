---
description: Generate, compare, and visually review MamboFont.
title: MamboFont Commands
order: 10
---

::page{layout="docs" width="normal" sidebar=true}

# MamboFont Commands

## Requirements

Building requires Python 3 with FontForge's Python bindings. WOFF2 support must be available in the installed FontForge build.

Every command can be run directly:

~~~bash
./script/mbfont.py --help
~~~

Or install a local mbfont symlink:

~~~bash
./script/install.sh
mbfont --help
~~~

The installer uses $HOME/.local/bin by default. Set MAMBOFONT_BIN_DIR to select another command directory. It refuses to replace a non-symlink and does not install compiled fonts into the operating system.

## Compile

~~~text
mbfont compile [X.Y.Z] [--out DIR] [--format ttf woff2]
~~~

The version defaults to the generator's current version and must be exact core SemVer such as 0.4.0. The output directory defaults to build/pilot; both file formats are generated when --format is omitted.

Build all four weights:

~~~bash
mbfont compile 0.4.0 --format ttf woff2 --out build/pilot
~~~

Build only text TTF files into a temporary review directory:

~~~bash
mbfont compile 0.4.0 --format ttf --out /tmp/mambofont
~~~

The pilot produces Regular, Medium, SemiBold, and Bold under the temporary internal family name Mambo Font Pilot. Each output is validated before it atomically replaces its destination.

## Check committed candidates

~~~text
mbfont check [X.Y.Z] [--out DIR] [--format ttf woff2]
~~~

Check rebuilds into a temporary directory and byte-compares every selected file with the destination. A missing or stale file makes the command fail.

~~~bash
mbfont check 0.4.0 --format ttf woff2 --out build/pilot
~~~

Generation uses a fixed source epoch and fixed ordering, so identical rules produce identical TTF and WOFF2 bytes. There is no separate build cache.

## Generate the specimen

~~~text
mbfont specimen [X.Y.Z] [--fonts DIR] [--out FILE]
~~~

The specimen is a local HTML review page containing all four weights and the supported character groups.

~~~bash
mbfont specimen 0.4.0 --fonts build/pilot --out specimen.html
~~~

Open specimen.html in a browser after any geometry, weight, or gap-rule change. It includes all printable ASCII in every weight, ambiguity strings at 10, 12, 14, 16, and 24 pixels, and Regular and Bold geometry cards. Red points on those cards are the final TTF vertices after union, integer rounding, and exact duplicate/collinear cleanup; declared gap decisions appear below vulnerable glyphs. Fourteen pixels per em is the review floor, while 10 and 12 pixels are non-gating stress tests. The command requires the matching WOFF2 pilot files to exist first.

## Development workflow

1. Change dimensions, named proportional guides, primitives, or the default 14-pixel/80-unit gap settings in sources/model.py; change glyph geometry and each vulnerable glyph's explicit gap action in sources/glyphs.py.
2. Compile all four weights into build/pilot.
3. Regenerate and inspect specimen.html at large and small sizes and in the blueprint views.
4. Run the deterministic end-to-end check.
5. Run `check` against the local candidate directory and inspect the source and specimen diffs together.

~~~bash
./script/mbfont.py compile 0.4.0 --format ttf woff2 --out build/pilot
./script/mbfont.py specimen 0.4.0 --fonts build/pilot --out specimen.html
/usr/bin/python3 tests/test_build.py
./script/mbfont.py check 0.4.0 --format ttf woff2 --out build/pilot
git diff --check
git status --short
~~~

The test asserts the exact 95-character printable-ASCII map, declared fill/widen outcomes, receiver-aligned diagonals, design-supplied advances, safe bounds, straight on-curve contours with no redundant points, metadata and line metrics, FontForge validity, and deterministic bytes in both formats. A 600-unit-wide, 850-unit-ascent blueprint check guards the shared proportional guides.

`GapRule` validation checks each recipe's declared `natural`, `minimum`, action, and `resolved` values; it does not run a generic post-outline gap detector. One-bit XBM checks preserve the Bold `g` tail aperture and require every non-space ASCII glyph to remain visually distinct at 14, 16, and 24 pixels. The test also rejects any active call to FontForge's stroke expansion.

## Documentation

The canonical source is the MamboDocs vault at `Docs/Projects/MamboFont`. After updating those pages, export only MamboFont:

~~~bash
cd ~/ProjectMambo/notes
node Scripts/sync_docs.js --sync MamboFont
~~~

Do not sync or edit MamboWiki during pilot iterations. Update the Wiki only after the complete base family is approved as a usable release.

## Publishing

The generator intentionally has no release command. The current printable-ASCII pilot is not a usable full font and never writes release files to dist. Publishing remains a separate maintainer decision after Latin-1 and Windows-1252 coverage, the design, and committed candidates are approved.
