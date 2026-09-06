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

MamboFont is Project Mambo's blocky monospace typeface. Its Python blueprint compiler generates filled, straight-edged outlines for four consistent weights:

- **Mambo Font** — Regular, Medium, SemiBold, and Bold, with a fixed 500-unit advance.

## Start here

| Goal | Document or path |
|---|---|
| Read the canonical Wiki documentation | [projectmambo.org/mambofont/](https://projectmambo.org/mambofont/) |
| Build, check, or review the fonts | [Commands](Commands.md) |
| Understand the glyph rules | [Design rules](Design.md) |
| Edit the generator source | [sources/](../sources/) |
| Inspect local pilot binaries | `build/pilot/` after compiling |
| Review every weight | [specimen.html](../specimen.html) |

## Build

Install Python 3 with FontForge's Python bindings, then run:

~~~bash
./script/mbfont.py compile 0.4.0 --format ttf woff2 --out build/pilot
./script/mbfont.py specimen 0.4.0 --fonts build/pilot --out specimen.html
~~~

The generated files are deterministic. There is no glyph cache to invalidate: edit a rule, rebuild, and review the Python and specimen diffs. Pilot binaries stay in the ignored build directory and are not release assets.

To install the same mbfont command used by downstream repositories:

~~~bash
./script/install.sh
~~~

The installer creates a symlink under $HOME/.local/bin by default. Set MAMBOFONT_BIN_DIR to choose a different existing command directory. It does not install font files into the operating system.

See [Commands](Commands.md) for all options and the required verification sequence.

## Current scope

The current review pilot encodes space plus 23 representative letters and figures. It exists to approve the outline grammar at Regular and Bold before expanding it. The milestone target remains 218 printable ASCII, Latin-1, and defined Windows-1252 characters.

## Repository layout

~~~text
sources/        dimensions, primitive rules, and pilot glyph blueprints
script/         direct-outline compile, check, specimen, and installer commands
tests/          one deterministic end-to-end build check
build/pilot/    ignored local TTF and WOFF2 review files
docs/           synchronized MamboDocs snapshot
archive/v0.2/   frozen drawings, exports, binaries, docs, and old tooling
archive/v0.3-stroke-prototype/  rejected generator and deferred work
~~~

The former SVG/export pipeline and the rejected centerline-stroke generator remain available only in the archive for comparison. The 0.4.0 pilot is deliberately incomplete and has not been released.

## Verification

~~~bash
/usr/bin/python3 tests/test_build.py
./script/mbfont.py check 0.4.0 --format ttf woff2 --out build/pilot
git diff --check
~~~

The check covers the exact pilot map, fixed advances, design bounds, all-on-curve contours, font validation, metadata, shared topology across weights, the absence of stroke expansion, and byte-for-byte deterministic output.

## Issues and feedback

This font is maintained for Project Mambo, so external pull requests are not currently requested. Glyph legibility and generator bug reports are welcome as repository issues.

## License

Distributed under the MIT License. See **[LICENSE](../LICENSE)** for details.
