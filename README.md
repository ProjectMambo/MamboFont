# MamboFont

<p align="left">
  <img src="https://img.shields.io/badge/SVG-F9A03F?style=flat-square&logo=svg&logoColor=white" alt="SVG" />
  <img src="https://img.shields.io/badge/TTF-4A4A4A?style=flat-square" alt="TrueType font" />
  <img src="https://img.shields.io/badge/WOFF2-4A4A4A?style=flat-square" alt="WOFF2 web font" />
  <img src="https://img.shields.io/badge/FontForge-202020?style=flat-square" alt="FontForge" />
</p>
<p align="left">
  <img src="https://img.shields.io/badge/Maintenance-Active-brightgreen?style=flat-square" alt="Maintenance status: active" />
  <img src="https://img.shields.io/github/last-commit/ProjectMambo/MamboFont?style=flat-square&color=7a5fff" alt="Last commit" />
  <img src="https://img.shields.io/github/repo-size/ProjectMambo/MamboFont?style=flat-square&color=yellow" alt="Repository size" />
  <a href="LICENSE"><img src="https://img.shields.io/github/license/ProjectMambo/MamboFont?style=flat-square&color=orange" alt="License" /></a>
</p>

MamboFont is Project Mambo's custom monospace font family. A layered SVG drawing is exported into per-glyph assets and compiled into Regular, Medium, SemiBold, and Bold TTF/WOFF2 files by one Python command-line tool.

## Start here

| Goal | Document or path |
|---|---|
| Read the canonical Wiki documentation | [projectmambo.org/mambofont/](https://projectmambo.org/mambofont/) |
| Export glyph layers or compile fonts | [Command and Release Workflow](docs/Commands.md) |
| Edit the source drawing | [`drawings/drawing.svg`](drawings/drawing.svg) |
| Use existing font binaries | [`ttf/`](ttf/) |

## Pipeline

```text
drawings/drawing.svg
    -> Inkscape layer export
    -> XMLStarlet cleanup and path processing
    -> drawings/exported/<weight>/ glyph cache
    -> FontForge compilation
    -> TTF + WOFF2
    -> optional GitHub release assets
```

The generator maps named layers to ASCII, Latin-1, symbols, Unicode characters, and private-use icons. Full-width and standard-width groups are compiled with different metrics.

## Local setup

The command requires Python 3. Exporting requires Inkscape and XMLStarlet; compilation additionally requires FontForge's Python bindings.

```bash
git clone https://github.com/ProjectMambo/MamboFont.git
cd MamboFont
./script/install.sh
```

The installer targets `/usr/local/bin` by default. It creates the `mbfont` symlink, refuses to replace a non-symlink at that target, and uses `sudo` only when the destination directory is absent or not writable. Set `MAMBOFONT_BIN_DIR` to use another bin directory; create that directory first to avoid `sudo`:

```bash
mkdir -p "$HOME/.local/bin"
MAMBOFONT_BIN_DIR="$HOME/.local/bin" ./script/install.sh
```

The installer exposes the build command only; it does **not** install a compiled font into the system font directory.

Run the script directly without installation:

```bash
python3 script/mambo_font.py --help
```

## Common commands

```bash
mbfont export
mbfont compile 0.2.4
mbfont compile 0.2.4 --format woff2 --out /tmp/mambofont
```

See [Command and Release Workflow](docs/Commands.md) before publishing or deleting a release.

## Repository layout

```text
drawings/drawing.svg       layered source of truth
drawings/exported/         committed processed-glyph cache for filtered builds
drawings/site-icons/       Project Mambo application/site icon exports
ttf/                       committed historical TTF and WOFF2 builds
script/mambo_font.py       export, compile, release, and unrelease CLI
script/install.sh          command symlink installer
script/test_cli.py         CLI, release, output-safety, and installer checks
```

## Status

The source currently compiles four weights. The repository contains v0.2.4 binaries, while the newest Git tag is v0.2.3; committed artifacts and published releases are not yet enforced by CI. A focused local regression suite exists, but there is no CI workflow.

Before committing generator changes, at minimum run:

```bash
bash -n script/install.sh
python3 script/mambo_font.py --help
python3 script/mambo_font.py compile --help
python3 script/test_cli.py
git diff --check
git status --short
```

Perform a full export and compile when Inkscape, XMLStarlet, and FontForge are available.

## Issues and feedback

This font is maintained for Project Mambo, so external pull requests are not currently requested. Glyph and build-pipeline bug reports are welcome as repository issues.

## License

Distributed under the MIT License. See **[LICENSE](LICENSE)** for details.
