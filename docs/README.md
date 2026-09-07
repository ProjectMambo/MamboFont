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

MamboFont is Project Mambo's blocky monospace typeface. Its Python blueprint compiler generates filled, straight-edged outlines from proportional guides and declarative readability contracts for four consistent weights:

- **Mambo Font** — Regular, Medium, SemiBold, and Bold, with a fixed 500-unit advance.

## Start here

| Goal | Document or path |
|---|---|
| Read the project overview | [docs/index.md](index.md) |
| Build, check, or review the fonts | [Commands](Commands.md) |
| Understand the glyph rules | [Design rules](Design.md) |
| Read the JSON/editor architecture | [Config and editor architecture](Design.md#config-and-editor-architecture) |
| Edit the generator source | [sources/](../sources/) |
| Inspect local pilot binaries | `build/pilot/` after compiling |
| Review every weight | [specimen.html](../specimen.html) |

## Build

Install Python 3 with FontForge's Python bindings, then run:

~~~bash
./script/mbfont.py compile 0.4.0 --format ttf woff2 --out build/pilot
./script/mbfont.py specimen 0.4.0 --fonts build/pilot --out specimen.html
~~~

The generated files are deterministic. There is no glyph cache to invalidate: edit JSON, rebuild, and review the config and specimen diffs. Pilot binaries stay in the ignored build directory and are not release assets.

To install the same mbfont command used by downstream repositories:

~~~bash
./script/install.sh
~~~

The installer creates a symlink under $HOME/.local/bin by default. Set MAMBOFONT_BIN_DIR to choose a different existing command directory. It does not install font files into the operating system.

See [Commands](Commands.md) for all options and the required verification sequence.

## Current scope

The current compiler encodes 161 entries: all 95 printable ASCII characters plus the remaining C0, DEL, and C1 controls as deliberate empty glyphs. It exists to approve the complete ASCII outline and gap grammar across all four weights before Latin-1 and Windows-1252 expansion. The JSON manifest expands the milestone target to 283 encoded entries: U+0000–U+00FF plus the 27 defined printable Windows-1252 additions. Sixty-seven controls and spaces are explicitly empty, leaving 216 characters with drawn glyphs.

The first three config-driven migration phases are implemented. `sources/font.json` owns the family dimensions, guides, weights, target coverage, and empty ranges; `sources/components.json` owns reusable geometry; and `sources/glyphs/` owns one JSON recipe per drawn glyph. The strict evaluator resolves `.notdef` and every printable ASCII glyph, including receiver-aware diagonals, explicit polygons, subtraction, and threshold-driven fill/widen rules. `compile`, `check`, and `specimen` all consume this same JSON project, and `--config FILE` provides the same headless interface to other repositories.

JSON is now the sole active glyph source. The generated specimen remains the review surface until the editor can replace every function it provides; `specimen.html` and its command will be removed only after that parity gate.

Only the base text family is active. All previous Mambo Icons drawings, binaries, and generator work are archived; a separate icon font can be designed after the base family reaches a usable release.

## Repository layout

~~~text
sources/        JSON font project plus the generic Python resolver and geometry engine
script/         direct-outline compile, check, specimen, and installer commands
tests/          dependency-free JSON contract and deterministic font build checks
build/pilot/    ignored local TTF and WOFF2 review files
docs/           synchronized MamboDocs snapshot
archive/v0.2/   frozen drawings, exports, binaries, icons, docs, and old tooling
archive/v0.3-stroke-prototype/  rejected stroke generator and deferred icon work
~~~

The former SVG/export pipeline and the rejected centerline-stroke generator remain available only in the archive for comparison. The 0.4.0 pilot is deliberately incomplete and has not been released.

## Verification

~~~bash
/usr/bin/python3 tests/test_config.py
/usr/bin/python3 tests/test_build.py
./script/mbfont.py check 0.4.0 --format ttf woff2 --out build/pilot
git diff --check
~~~

The check covers the 161 currently encoded entries, all 67 deliberate empty glyphs, fixed advances, bounds, all-on-curve contours without duplicate or removable collinear points, font validation, metadata, declarative gap contracts, the protected Bold `g` aperture, visually distinct non-space glyphs at 14, 16, and 24 pixels, the absence of stroke expansion, and byte-for-byte deterministic output. Fourteen pixels per em is the review floor; 10- and 12-pixel rows are non-gating stress tests.

MamboDocs owns the canonical pages under `Docs/Projects/MamboFont`. Sync only that project into this repository with `node Scripts/sync_docs.js --sync MamboFont` from the MamboDocs vault. MamboWiki stays unchanged until the base family is complete enough for a usable release.

## Issues and feedback

This font is maintained for Project Mambo, so external pull requests are not currently requested. Glyph legibility and generator bug reports are welcome as repository issues.

## License

Distributed under the MIT License. See **[LICENSE](../LICENSE)** for details.
