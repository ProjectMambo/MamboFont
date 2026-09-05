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
| Unrelease | Python 3, Git, authenticated GitHub CLI, and Neovim (currently checked even though no editor opens) |

`./script/install.sh` exposes the Python script as `mbfont`. Every example can instead start with `python3 script/mambo_font.py`.

## Export SVG glyphs

```bash
mbfont export [-o DIR] [-f LAYER ...]
```

Export reads the layered `drawings/drawing.svg`, converts strokes and shapes into processed glyph paths, and writes all selected weight/layer assets. The default destination is `drawings/exported/`.

Layer filters are case-insensitive partial matches:

```bash
mbfont export -f alphabetupper symbol
mbfont export -o /tmp/mambofont-svg -f icons
```

## Compile fonts

```bash
mbfont compile <version> [-o DIR] [-f LAYER ...] [-t ttf woff2] [--svg-cache DIR]
```

Without filters, compile exports every glyph in memory and builds all four weights. The default output directory is `ttf/`, and both TTF and WOFF2 are written.

```bash
mbfont compile 0.2.4
mbfont compile 0.2.4 -t woff2 -o /tmp/mambofont
```

A filtered compile overlays freshly exported matching layers on the remaining processed SVGs loaded from `drawings/exported/` or `--svg-cache`. Keep that cache complete when using filters; otherwise unselected glyphs may be absent from the result.

```bash
mbfont compile 0.2.4 -f icons --svg-cache drawings/exported
```

## Release

```bash
mbfont release <version>
```

Release performs a complete in-memory build of every weight and both formats, creates individual files plus TTF and WOFF2 zip archives, tags the current commit as `v<version>`, pushes that tag, opens Neovim for release notes, and creates a GitHub release with all assets.

Before running it:

1. Run a full local compile and inspect every expected output.
2. Confirm the working tree is clean and the intended commit and branch are checked out.
3. Confirm the version and tag do not conflict with committed artifacts or an existing release.
4. Run `gh auth status`.

The command does not currently enforce a clean tree, branch, or version policy. It pushes the remote tag before release notes are edited and before the GitHub release is created. If a later step fails, inspect and clean up the tag before retrying.

If the release already exists, the command offers to delete it first and reuse its notes as the editing seed.

## Unrelease

```bash
mbfont unrelease <version>
```

This destructive command deletes the matching GitHub release, its remote tag, and its local tag. It does not remove compiled files already committed to the repository.

The command does not prompt for confirmation after invocation; it asks GitHub CLI to delete the release with `--yes`. Verify the version carefully before running it.

## Verification

```bash
bash -n script/install.sh
python3 script/mambo_font.py --help
mbfont export -o /tmp/mambofont-export
mbfont compile 0.0.0 -o /tmp/mambofont-build -t ttf woff2
```

There is no automated regression suite, so a release should also verify that all four weights and both file formats open and report the intended family, style, and version metadata.
