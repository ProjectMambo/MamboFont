# MamboFont

<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/TTF-4A4A4A?style=flat-square" alt="TrueType font" />
  <img src="https://img.shields.io/badge/WOFF2-4A4A4A?style=flat-square" alt="WOFF2 web font" />
  <img src="https://img.shields.io/badge/FontForge-202020?style=flat-square" alt="FontForge" />
</p>
<p align="left">
  <img src="https://img.shields.io/badge/Maintenance-Active-brightgreen?style=flat-square" alt="Maintenance status: active" />
  <img src="https://img.shields.io/github/last-commit/ProjectMambo/MamboFont?style=flat-square&color=7a5fff" alt="Last commit" />
  <a href="../LICENSE"><img src="https://img.shields.io/github/license/ProjectMambo/MamboFont?style=flat-square&color=orange" alt="License" /></a>
</p>

MamboFont is Project Mambo's blocky monospace type system. Its compact Python geometry generates two focused families directly through FontForge:

- **Mambo Font** — Regular, Medium, SemiBold, and Bold, with a fixed 500-unit advance.
- **Mambo Icons** — one Regular icon family with a fixed 1000-unit advance.

## Start here

| Goal | Document or path |
|---|---|
| Read the canonical Wiki documentation | [projectmambo.org/mambofont/](https://projectmambo.org/mambofont/) |
| Build, check, or review the fonts | [Commands](Commands.md) |
| Understand the glyph and icon rules | [Design rules](Design.md) |
| Edit the generator source | [sources/](../sources/) |
| Inspect candidate binaries | [dist/](../dist/) |
| Review every weight and icon | [specimen.html](../specimen.html) |

## Build

Install Python 3 with FontForge's Python bindings, then run:

~~~bash
./script/mbfont.py compile 0.3.0 --family all --format ttf woff2 --out dist
./script/mbfont.py specimen 0.3.0 --fonts dist --out specimen.html
~~~

The generated files are deterministic. There is no glyph cache to invalidate: edit a rule, rebuild, and review the Python diff together with the changed candidate binaries.

To install the same mbfont command used by downstream repositories:

~~~bash
./script/install.sh
~~~

The installer creates a symlink under $HOME/.local/bin by default. Set MAMBOFONT_BIN_DIR to choose a different existing command directory. It does not install font files into the operating system.

See [Commands](Commands.md) for all options and the required verification sequence.

## Coverage

Mambo Font encodes 218 printable characters: ASCII, Latin-1, and all defined printable Windows-1252 additions. Accented letters reuse the same base skeletons and mark components across all four weights. Control-code slots and undefined Windows-1252 holes are intentionally omitted.

Mambo Icons contains 30 functional icons in frozen legacy private-use slots. Three old brand illustrations are retired, and their slots remain reserved.

## Repository layout

~~~text
sources/        text, icon, and shared geometry rules
script/         direct compile, check, specimen, and installer commands
tests/          one deterministic end-to-end build check
dist/           review-candidate TTF and WOFF2 files
docs/           synchronized MamboDocs snapshot
archive/v0.2/   frozen drawings, exports, binaries, docs, and old tooling
~~~

The former SVG/export pipeline remains available only in archive/v0.2 for reference. The 0.3.0 files are review candidates and have not been released.

## Verification

~~~bash
/usr/bin/python3 tests/test_build.py
./script/mbfont.py check 0.3.0 --family all --format ttf woff2 --out dist
git diff --check
~~~

The check covers exact character maps, fixed advances, bounding boxes, font validation, metadata, stable icon assignments, and byte-for-byte deterministic output.

## Issues and feedback

This font is maintained for Project Mambo, so external pull requests are not currently requested. Glyph legibility and generator bug reports are welcome as repository issues.

## License

Distributed under the MIT License. See **[LICENSE](../LICENSE)** for details.
