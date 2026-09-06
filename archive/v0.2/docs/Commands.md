---
title: MamboFont Command and Release Workflow
description: Export SVG glyphs, compile font files, and manage GitHub releases with mbfont.
order: 10
---

::page{layout="docs" width="normal" sidebar=true}

# MamboFont Command and Release Workflow

## Requirements

| Operation | Required tools |
|---|---|
| Help and syntax validation | Python 3 |
| Export | Python 3, Inkscape, and XMLStarlet |
| Compile | Export requirements plus FontForge Python bindings |
| Release | Compile requirements, Git, authenticated GitHub CLI, and Neovim |
| Unrelease | Python 3, Git, and authenticated GitHub CLI |

`./script/install.sh` exposes the Python script as `mbfont`. It honors `MAMBOFONT_BIN_DIR`, defaults to `/usr/local/bin`, refuses to replace a non-symlink command, and uses `sudo` only when the destination is absent or not writable. Every example can instead start with `python3 script/mambo_font.py`.

The CLI uses Python's standard argument parser. Run `mbfont <command> --help` for command-specific syntax; unknown options are rejected as usage errors.

## Export SVG glyphs

```bash
mbfont export [--out DIR] [--filter LAYER ...]
```

Export reads the layered `drawings/drawing.svg`, converts strokes and shapes into processed glyph paths, and writes all selected weight/layer assets. The default destination is `drawings/exported/`.

Layer filters are case-insensitive partial matches:

```bash
mbfont export --filter alphabetupper symbol
mbfont export --out /tmp/mambofont-svg --filter icons
```

`-o` and `-f` are short aliases. An explicit `--out` directory is caller-owned: export records generated paths in `.mambofont-export.json`, removes only stale paths from that manifest, and preserves unrelated files. Unsafe paths derived from source labels are rejected before cleanup or writes. At the default destination, a full export replaces the complete managed cache and a filtered export replaces only affected subdirectories.

## Compile fonts

```bash
mbfont compile <version> [--out DIR] [--filter LAYER ...] [--format ttf woff2] [--svg-cache DIR]
```

`<version>` must be exact core SemVer such as `1.2.3`: no leading `v`, leading-zero segment, prerelease, or build suffix. Validation happens before font work or output writes. Without filters, compile exports every glyph in memory and builds all four weights. The default output directory is `ttf/`, and both TTF and WOFF2 are written.

```bash
mbfont compile 0.2.4
mbfont compile 0.2.4 --format woff2 --out /tmp/mambofont
```

`--format` is the canonical format option. `-t` and `--type` remain compatibility aliases; `-o` and `-f` remain short aliases for `--out` and `--filter`.

A filtered compile overlays freshly exported matching layers on the remaining processed SVGs loaded from `drawings/exported/` or `--svg-cache`. Keep that cache complete when using filters; otherwise unselected glyphs may be absent from the result.

```bash
mbfont compile 0.2.4 --filter icons --svg-cache drawings/exported
```

## Release

```bash
mbfont release <X.Y.Z>
```

Release uses the same exact core SemVer rule and refuses to run unless the project is on `main` with a clean working tree. It then checks its tools and GitHub authentication, requires source SVGs for every weight, performs a complete in-memory build of both formats, prepares individual files plus TTF and WOFF2 zip archives, opens Neovim for release notes, and asks for final publication confirmation. Only after those steps succeed and the maintainer confirms does it tag the current commit as `v<version>`, push the tag, and create the GitHub release with all assets.

Before running it:

1. Run a full local compile and inspect every expected output.
2. Confirm the working tree is clean and the intended commit and branch are checked out.
3. Confirm the version and tag do not conflict with committed artifacts or an existing release.
4. Run `gh auth status`.

The branch, working-tree, version, and complete-weight checks happen before publication. They do not prove that committed binaries already match the requested version, so inspect those artifacts explicitly. If GitHub release creation fails after the tag is pushed, the command attempts to remove any partial release plus its local and remote tags and reports whether manual inspection is still required.

If the release already exists, the command offers to replace it and reuses its notes as the editing seed. The existing release is not deleted until the build, archives, and edited notes are ready.

All Git and GitHub CLI operations run against the project root, regardless of the directory from which `mbfont` was invoked.

## Unrelease

```bash
mbfont unrelease <X.Y.Z> --yes
```

This destructive command asks GitHub CLI to delete the matching release and remote tag as one checked operation, then deletes the local tag. It can also remove tag-only state left by an interrupted release. A remote failure stops before local state changes and reports that the remote state must be inspected. It does not remove compiled files already committed to the repository.

The version follows the same exact core SemVer rule as `release`, and the explicit `--yes` flag is required before deletion begins. The command does not require `main` or a clean tree, so it remains available for release recovery, and it does not open an editor. Verify the version carefully before running it.

## Verification

```bash
bash -n script/install.sh
python3 script/mambo_font.py --help
python3 script/test_cli.py
mbfont export --out /tmp/mambofont-export
mbfont compile 0.0.0 --out /tmp/mambofont-build --format ttf woff2
```

The focused regression suite is not currently run by CI. A release should also verify that all four weights and both file formats open and report the intended family, style, and version metadata.
