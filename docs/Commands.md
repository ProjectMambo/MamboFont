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

The version defaults to the generator's current version and must be exact core SemVer such as 0.3.0. The output directory defaults to dist; both file formats are generated when --format is omitted.

Build all four weights:

~~~bash
mbfont compile 0.3.0 --format ttf woff2 --out dist
~~~

Build only text TTF files into a temporary review directory:

~~~bash
mbfont compile 0.3.0 --format ttf --out /tmp/mambofont
~~~

MamboFont produces Regular, Medium, SemiBold, and Bold. Each output is validated before it atomically replaces its destination.

## Check committed candidates

~~~text
mbfont check [X.Y.Z] [--out DIR] [--format ttf woff2]
~~~

Check rebuilds into a temporary directory and byte-compares every selected file with the destination. A missing or stale file makes the command fail.

~~~bash
mbfont check 0.3.0 --format ttf woff2 --out dist
~~~

Generation uses a fixed source epoch and fixed ordering, so identical rules produce identical TTF and WOFF2 bytes. There is no separate build cache.

## Generate the specimen

~~~text
mbfont specimen [X.Y.Z] [--fonts DIR] [--out FILE]
~~~

The specimen is a local HTML review page containing all four weights and the supported character groups.

~~~bash
mbfont specimen 0.3.0 --fonts dist --out specimen.html
~~~

Open specimen.html in a browser after any geometry or weight change. The command requires the matching WOFF2 candidates to exist first.

## Development workflow

1. Change the shared rules in sources/text.py or sources/geometry.py.
2. Compile all four weights into dist.
3. Regenerate and inspect specimen.html at large and small sizes.
4. Run the deterministic end-to-end check.
5. Run check against dist and inspect the source and binary diffs together.

~~~bash
./script/mbfont.py compile 0.3.0 --format ttf woff2 --out dist
./script/mbfont.py specimen 0.3.0 --fonts dist --out specimen.html
/usr/bin/python3 tests/test_build.py
./script/mbfont.py check 0.3.0 --format ttf woff2 --out dist
git diff --check
git status --short
~~~

The test asserts the exact character map, fixed advances, safe bounding boxes, metadata and line metrics, FontForge validity, and deterministic bytes in both formats.

## Publishing

The generator intentionally has no release command. Compile and review candidates first; publishing remains a separate maintainer decision. Do not infer a release from files appearing in dist.
