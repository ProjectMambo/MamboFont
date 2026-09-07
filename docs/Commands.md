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

## Current development workflow

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

The test asserts the exact 95-character printable-ASCII map, declared fill/widen outcomes, receiver-aligned diagonals, nominal-thickness punctuation, design-supplied advances, safe bounds, straight on-curve contours with no redundant points, metadata and line metrics, FontForge validity, and deterministic bytes in both formats. A 600-unit-wide, 850-unit-ascent blueprint check guards the shared proportional guides.

`GapRule` validation checks each recipe's declared `natural`, `minimum`, action, and `resolved` values; it does not run a generic post-outline gap detector. One-bit XBM checks preserve the Bold `g` tail aperture and require every non-space ASCII glyph to remain visually distinct at 14, 16, and 24 pixels. The test also rejects any active call to FontForge's stroke expansion.

## Config and editor migration

Phases 1 and 2 are implemented. The strict `sources/config.py` evaluator loads the JSON project, resolves project and glyph references, expands generic filled primitives and the reusable frame component, measures declared gaps, and applies one explicit `fill` or `widen` fallback. The current representative files are `.notdef`, `7`, `A`, `H`, `M`, `O`, and `a`.

JSON does not drive `compile` or `check` yet, and `mbfont edit` does not exist, so use the current Python and specimen commands above until the printable-ASCII migration reaches its parity gate.

Check the JSON source contract without FontForge:

~~~bash
/usr/bin/python3 tests/test_config.py
~~~

It requires 283 target code points, 67 explicit empty code points, 210 pending drawn glyphs, exact JSON/Python guide parity, and exact source-blueprint parity for the seven configured glyphs in every weight. It also checks duplicate-key and cyclic-reference rejection. The FontForge end-to-end test separately requires identical normalized contours between the JSON and current Python recipes.

The existing headless interface remains stable for other repositories:

~~~text
mbfont compile [X.Y.Z] [--config FILE] [--out DIR] [--format ttf woff2]
mbfont check [X.Y.Z] [--config FILE] [--out DIR] [--format ttf woff2]
~~~

`--config` will default to `sources/font.json`; omitting it preserves today's command shape. Both commands will load the same JSON project and call the same Python compiler used by the editor. Downstream builds will not require a browser, JavaScript, Rust, Node.js, or an editor dependency.

The only new authoring command is planned as:

~~~text
mbfont edit [--config FILE]
~~~

It will start a loopback-only local server and open the browser editor. Its Build action invokes the same compile operation rather than maintaining a second geometry implementation.

### Authoring workflow after migration

1. Codex adds the requested Unicode entries under `sources/glyphs/`, reuses components, and extends the small generic primitive vocabulary only when an existing primitive cannot express the character.
2. The loader resolves every new glyph in all four weights and rejects incomplete coverage, invalid references, unsupported shapes, broken gaps, or invalid final contours.
3. Open `mbfont edit`, filter to draft or changed glyphs, and inspect the source geometry, optimized outline, gap outcomes, and 14-, 16-, and 24-pixel previews in every weight.
4. Drag named points or guides, enter exact values, change allowed primitive parameters, and select the declared `fill` or `widen` fallback for vulnerable gaps. The final generated TrueType vertices are never edited as source.
5. A valid working edit compiles a temporary WOFF2 preview. The typable specimen switches to that revision without reloading the page; an invalid edit leaves the last valid preview active and displays the error.
6. Save validates the complete project, then atomically rewrites only the selected stable, two-space-indented JSON file. Preview files remain temporary and ignored.
7. Build TTF and WOFF2, run the end-to-end test and `check`, inspect the JSON and documentation diff, then commit the source rather than preview output.

### Migration sequence

1. **Complete:** establish the strict versioned JSON manifest and resolver, preserve the current source commit as the behavior baseline, and record controls and spaces as explicit empty coverage.
2. **Complete:** translate `.notdef`, `7`, `A`, `H`, `M`, `O`, and `a`, covering bars, diagonals, cuts, components, joins, and both gap actions; require matching source geometry and normalized contours in all four weights.
3. Translate all printable ASCII into JSON and keep both paths only long enough to prove parity. Switch `compile` and `check`, then remove glyph-specific Python recipes in the same checkpoint.
4. Add the editor first as a read-only geometry and live-font viewer, then add point, guide, primitive, gap-rule, undo, and atomic-save operations.
5. Match the current specimen's glyph grid, weights, sizes, optimized-point display, gap diagnostics, and ambiguity strings. Only after that gate, remove the tracked `specimen.html` and the `specimen` command; the editor's typable box becomes the review surface.
6. Expand Latin-1 and the printable Windows-1252 set through new JSON glyph and component files, then use the editor for the human tuning pass.
7. Produce a usable 283-entry candidate, including 216 drawn glyphs and 67 deliberate empty glyphs. Release and MamboWiki work remain separate later decisions.

## Documentation

The canonical source is the MamboDocs vault at `Docs/Projects/MamboFont`. After updating those pages, export only MamboFont:

~~~bash
cd ~/ProjectMambo/notes
node Scripts/sync_docs.js --sync MamboFont
~~~

Do not sync or edit MamboWiki during pilot iterations. Update the Wiki only after the complete base family is approved as a usable release.

## Publishing

The generator intentionally has no release command. The current printable-ASCII pilot is not a usable full font and never writes release files to dist. Publishing remains a separate maintainer decision after Latin-1 and Windows-1252 coverage, the design, and committed candidates are approved.
