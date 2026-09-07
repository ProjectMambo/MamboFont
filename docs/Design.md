---
description: Geometry, weight, coverage, and compatibility rules for MamboFont.
title: MamboFont Design Rules
order: 20
---

::page{layout="docs" width="normal" sidebar=true}

# MamboFont Design Rules

## Scope and ownership

Mambo Font keeps the character of the archived v0.2 drawings while making its outlines, weights, and coverage systematic. The active generator owns only the base text family. Previous Mambo Icons drawings, binaries, and generator code live under `archive/`; icon design and a separate icon font are deferred until the base family reaches a usable release.

MamboDocs owns the canonical documentation under `Docs/Projects/MamboFont`. The MamboFont repository receives a synchronized snapshot. MamboWiki is deliberately left unchanged during pilot work and will be updated only for a usable release.

## Current source architecture

The font has one short, direct path from parameters to binaries:

1. `sources/model.py` defines the design dimensions, proportional named guides, weight values, filled-outline primitives, blueprint schema, and `GapRule` contract validation.
2. `sources/glyphs.py` defines each character recipe and the explicit decision for every readability-sensitive gap.
3. `script/mbfont.py` resolves one design per weight, compiles the contours, normalizes and validates them, writes TTF and WOFF2, byte-checks candidates, and generates the review specimen.
4. `tests/test_build.py` checks geometry contracts, raster outcomes, metadata, format validity, and deterministic builds.
5. `specimen.html` is generated review output, not another source of glyph geometry.

There is no SVG-to-font source pipeline and no cache. SVG appears only in the specimen's blueprint cards. Editing a dimension or glyph rule and rebuilding is the complete source-of-truth workflow.

## Config and editor architecture

This architecture is being introduced in gated phases. Phase 1 provides `sources/font.json`, `sources/components.json`, a strict standard-library loader/resolver, and the first `.notdef` JSON recipe. The JSON source does not drive font compilation yet, visible glyph files have not been migrated, and `mbfont edit` does not exist. The current Python recipes and generated specimen remain authoritative until the migration gates in [MamboFont Commands](Commands.md) pass.

### Architecture decisions

- Strict JSON becomes the complete editable font source. JSON is native to Python and browsers, produces deterministic text diffs, and needs no YAML, TOML, or GUI serialization dependency.
- The source is split by ownership rather than stored as one large document. `font.json` owns project-wide values and deliberate empty ranges, `components.json` owns reusable geometry, and one `glyphs/U+XXXX.json` file owns each drawn glyph. This lets the GUI save one glyph without rewriting the whole family and keeps Codex-generated additions reviewable. Identical empty controls are expanded from ranges instead of duplicated across 67 files.
- Python remains the only configuration resolver, geometry engine, validator, and TTF/WOFF2 compiler. The browser never reimplements font rules and other repositories keep a headless command-line build.
- The editor is a local browser application made from native HTML, CSS, JavaScript, and SVG, served by Python's standard library. A Rust GUI is deferred: while the compiler remains Python/FontForge, Rust would add a second runtime and an IPC boundary or duplicate the resolver without improving this 283-entry workload.
- SVG is a precise interactive view, not an intermediate font format. The compiler writes normalized filled contours directly to the font backend.
- Preview and final vertices are derived data. Only semantic guides, points, primitives, components, and rules are saved.

Rust can be reconsidered if MamboFont later requires a separately packaged native desktop editor or if the compiler itself moves to Rust. Until then, a browser editor is smaller and uniquely verifies the WOFF2 result in its real rendering environment.

### Target source layout

~~~text
sources/
  font.json             schema version, metadata, metrics, weights, guides, coverage
  components.json       reusable frames, marks, accents, and other shared geometry
  glyphs/
    _notdef.json
    U+0020.json
    U+0021.json
    ...
  config.py             strict loading, reference resolution, and validation
  model.py              generic filled-outline primitives and normalization
editor/
  index.html
  app.js
  style.css
script/mbfont.py        compile, check, and edit commands
tests/test_config.py    dependency-free JSON contract and guide-parity check
tests/test_build.py     end-to-end outline, font, raster, and determinism check
~~~

The loader treats the directory containing `font.json` as the project root. `font.json` names the component file and glyph directory, so `--config` can point at another project without relying on the repository's working directory.

### JSON project contract

Every JSON document carries `format` and `schema_version` fields. The first format version is intentionally closed: unknown fields, primitives, actions, and scalar forms are errors instead of silently ignored extensions. JSON object ordering never affects generated contours or glyph order.

`font.json` owns:

- family metadata, units per em, advance, ascent, descent, and vertical metrics;
- the four weights and their nominal thicknesses;
- the supported review sizes and default minimum gap;
- named global horizontal and vertical guides;
- the required Unicode coverage and deterministic glyph order;
- paths to the components document and glyph directory.

Glyph filenames and map keys use uppercase `U+XXXX` code points so whitespace, escaping, and names cannot make the source ambiguous. Deliberately empty ranges create encoded, contourless glyphs with the family advance and appear in the future editor like other entries; an individual file is needed only if an empty entry later needs special metrics or metadata. A drawn glyph document owns:

- its code point, production name, advance, and review state;
- named local values and semantic points;
- an ordered list of additive and subtractive shapes with stable IDs;
- its explicit vulnerable-gap probes and fallback actions;
- optional anchors and component or base-glyph references.

Reusable components use the same point and shape vocabulary with named parameters. Accented characters reference a base glyph and an accent component at declared anchors; bespoke characters such as `Æ`, `Œ`, `ß`, `Ð`, and `Þ` remain explicit glyph geometry. Component and glyph reference cycles are invalid.

The scalar language stays data-only. A value is one of:

1. A finite number such as `80`.
2. A named reference such as `{ "ref": "guide.x.center" }`.
3. An affine value such as `{ "constant": 20, "terms": { "guide.x.center": 1, "weight.thickness": -0.5 } }`.
4. A complete `by_weight` map for a reviewed optical exception.

References may address project metrics, review settings, global guides, the current weight, glyph-local values and points, or component parameters. The resolver evaluates them as an acyclic dependency graph. There are no expression strings, scripts, loops, arbitrary conditionals, Python calls, or `eval`. Geometry-specific mathematics stays inside the small tested primitive implementation.

Phase 1 resolves rectangle geometry for `.notdef`. Later migration phases add the rest of the deliberately narrow primitive vocabulary as real converted glyphs require it:

- rectangle, horizontal bar, and vertical bar;
- true level-capped diagonal and receiver-aware joined diagonal;
- explicit polygon for an irreducible silhouette;
- additive component and composed-glyph reference;
- translation and horizontal or vertical mirroring.

Every shape has a semantic ID and an `add` or `subtract` operation. Arbitrary transforms, curves, rotation, and scaling are excluded from the first schema. A feature is added only after a real glyph cannot be expressed by the existing vocabulary.

### Config-driven gap rules

Gap decisions stay explicit and per glyph. A gap record names one or more semantic probes, a minimum clearance, and exactly one fallback. The compiler evaluates it independently in every weight:

1. Build the unconditional source shapes and measure only the declared cross-sections.
2. Preserve the geometry when every measured clearance reaches the minimum.
3. If a probe is smaller, apply its configured `fill` patch or `widen` replacement once.
4. Rebuild and measure the final normalized outline. `fill` must close the declared opening; `widen` must meet the threshold. Otherwise compilation fails.

A fallback may add a named patch or replace/remove named shapes supplied in that same rule. Nested gap rules, rule-dependent rules, and two rules that edit the same shape are invalid. The compiler never guesses whether a small void is important, runs a global morphology pass, or searches for arbitrary nearest edges.

This represents the approved pilot decisions directly: `A` and sub-threshold `M`, `W`, `m`, and `w` notches fill; the lower `g` aperture widens or remains at least the declared minimum. The GUI exposes the natural measurement, action, and resolved measurement for every weight.

### Compiler boundary and pipeline

The CLI and editor call one Python project API. Loading or saving a project, resolving one glyph for interactive feedback, compiling a preview, and compiling final fonts all pass through the same validator and primitive implementation.

~~~text
load JSON project
  -> validate format, schema version, coverage, IDs, and references
  -> resolve guides, points, and values for one weight
  -> expand components and generic filled primitives
  -> measure and apply declared gap fallbacks once
  -> union ink and subtract cuts
  -> snap to integer font units
  -> remove exact duplicate and same-direction collinear vertices
  -> normalize direction, contour order, and start points
  -> validate bounds, topology, gaps, thickness contracts, and readability gates
  -> write and reopen deterministic TTF and WOFF2
~~~

Optimization is exact and shape-preserving. It removes duplicate and truly collinear vertices but never uses tolerance simplification or generic smoothing. Short non-collinear edges, receiver teeth, slivers, self-intersections, and unintended point contacts are reported against the source shape that produced them. They are fixed by a joined primitive, point, or explicit polygon rather than silently deleting a corner and changing the glyph.

### Browser editor contract

`mbfont edit` will bind an ephemeral port on `127.0.0.1`, create a per-run mutation token, serve only fixed editor assets and project endpoints, then open the local page. The standard-library server is development tooling, never a network service. It exposes no arbitrary path, shell command, or repository API.

The editor has four working areas:

- A searchable glyph grid with Unicode, name, review state, changed state, and validation warnings.
- A zoomable SVG canvas with toggles for bounds, reference lines, named points, source shapes, final normalized contours, and final vertices. Final contours are the default so raw overlap points cannot be mistaken for excess TTF points.
- An inspector for exact coordinates, references and offsets, snapping, primitive endpoints and thickness, component placement, shape order, gap probes, minimums, and `fill` or `widen` alternatives.
- An all-weight review area with actual-size 14-, 16-, and 24-pixel samples, gap outcomes, ambiguity strings, and a free typable text box.

Dragging updates the selected semantic point or guide, never an optimized TTF vertex. The page sends a debounced working patch to Python; Python returns resolved source shapes, final contours, gap diagnostics, and errors for all four weights. Undo, redo, and reset live in the browser session. Invalid working state is visible but cannot overwrite the project.

After a valid working change settles, Python compiles a temporary WOFF2 preview keyed by a content revision. JavaScript loads it as a uniquely named `FontFace`, adds it to `document.fonts`, switches the typable box to that family, and releases the old preview. The newest config therefore appears without a page reload. The last valid preview remains visible while an invalid edit is corrected.

Save first resolves and validates the complete project in all four weights, writes a same-directory temporary file with stable two-space formatting and key order, then uses an atomic replace for only the selected JSON document. Build calls the normal compiler and writes the requested TTF/WOFF2 destination. Neither action commits files or writes release assets.

The first editor version does not need React, a UI framework, WebSockets, a database, or a second geometry engine. Fixed HTTP endpoints for editor state, preview, save, build, and revisioned preview-font bytes are sufficient.

### Target validation contract

Before a project can save or build, validation rejects:

- unknown keys or unsupported schema versions;
- malformed, duplicate, missing, or extra code points relative to declared coverage;
- duplicate shape/point IDs, missing references, dependency cycles, and component cycles;
- non-finite numbers, incomplete `by_weight` maps, invalid thicknesses, and out-of-bounds geometry;
- unsupported operations, conflicting gap branches, an incomplete fill, or a widened gap below its minimum;
- open or self-intersecting contours, zero-area edges, unintended contacts, and short popup edges;
- duplicate or removable collinear final vertices and nondeterministic contour or glyph ordering.

The end-to-end build still checks exact advances and cmap coverage, consistent line metrics and metadata, all four weights, raster distinction at the supported review sizes, valid reopened TTF/WOFF2 files, and byte-identical repeated builds. GUI save round-trips must also prove stable JSON output, and a rejected edit must leave the last saved file unchanged. Headless `compile` and `check` tests run without starting or importing the editor.

## Coordinate and weight model

Every encoded glyph currently advances 500 units in a 1000-unit em. The compiler reads that advance from `Design` rather than embedding 500 in the outline stage. The fixed default vertical metrics are an 800-unit ascent and 200-unit descent; line metrics do not change between weights.

The default `x` guides include cell edges 0 and 500, ink edges 40 and 460, center 250, and upper-bowl receiver 390. The inner guides remain weight-dependent at `ink_left + thickness` and `ink_right - thickness`. Shared optical positions have names and ratios within the ink width: diagonal terminals at 5/42 from either edge, the `1` flag at 5/21 from the left, lowercase stem at 11/42, `r` shoulder at 31/42, lowercase foot at 5/6, and the upper `B` receiver at two thirds of the distance from center to the right ink edge. A few punctuation layouts use explicit coordinates as deliberate optical exceptions in the default 500-unit cell.

The default `y` guides are descender -140, baseline 0, x-mid at half the x-height, midline at half the cap height, x-height 400, cap height 640, and ascender 800. Former literal join positions are also derived: the `r` join is 3/5 of x-height, the `M` join is 13/32 of cap height, the `1` flag is 25/32 of cap height, and accent height is 3/4 of the way from cap height to ascender. This keeps optical relationships intact when the design dimensions change. `Design` rejects dimensions that cannot leave room for the declared protected gaps.

| Style | CSS weight | Nominal thickness |
|---|---:|---:|
| Regular | 400 | 80 |
| Medium | 500 | 93 |
| SemiBold | 600 | 107 |
| Bold | 700 | 120 |

All four weights use the same blueprint fields and glyph recipes. Exterior surfaces normally stay fixed while weight grows inward. A local thickness, receiver clip, or conditional fill patch is allowed when a declared gap contract requires it for readability; such a fill may intentionally add one source contour at a heavier weight.

## Blueprint and style grammar

A glyph blueprint has exactly three fields:

- `ink`: additive filled contours.
- `cuts`: explicit negative contours for counters or holes.
- `gaps`: named `GapRule` records for vulnerable clearances.

Glyph recipes select guide intersections and use a small primitive set: rectangles, horizontal and vertical bars, constant-perpendicular-width diagonal polygons with horizontal caps, and receiver-aware joined diagonals. Explicit polygons or cuts are used only when those primitives cannot express the intended shape.

The visual rules are:

- Counters and bowl corners are square. Rounded, beveled, or corner-smoothing surfaces are outside the grammar.
- Horizontal and ordinary vertical terminals stay level. A diagonal is a true straight band with parallel sides and level ends, never a staircase, except for a declared receiver-cap clip at an outer ink bound.
- Slanted surfaces appear only where the glyph's identifying diagonal requires them. Joined diagonal endpoints sit inside their receiving bar or stem so no shelf, spike, concave corner, or point contact remains.
- M, N, and W retain vertical exterior stems and place their diagonals inside. A, V, and X retain identity-critical exterior diagonals.
- Receiver caps in `1` and `?` are clipped to the stem they join. The `5` and `7` use the same receiver-aware diagonal calculation as `Z` and `2`, so their level ends terminate flush with the connected horizontal bars.
- Ambiguous monospace characters remain distinct: serifed `I`, footed `l`, flagged `1`, square `O`, and slashed `0`.
- Readability outranks nominal thickness only at a declared local exception; the rest of the glyph keeps the weight's nominal thickness.

### Printable-ASCII recipe families

The active pilot contains all 95 printable ASCII code points. Recipes share geometry by visual grammar rather than by alphabetic order:

- Square frames and open `C` frames form `B`, `C`, `E`, `G`, `O`, `P`, `D`, the round lowercase family, and the enclosed figures.
- Exterior stems plus internal diagonals form `M`, `N`, `W`, and their lowercase relatives. `A`, `K`, `R`, `V`, `X`, `Z`, and the diagonal figures use true level-capped diagonal polygons where the diagonal identifies the character.
- `Z`, `z`, and `2` use receiver-aware diagonal polygons whose ends meet their horizontal bars without exposed shelves. Lowercase `s` instead uses a compact square S construction so `s` and `z` remain distinct.
- Dense horizontal stacks in `a`, `e`, and `s` may use locally thinner horizontal bars. Ordinary punctuation, dots, commas, the `#` grid, `%`, and punctuation diagonals use the weight's full nominal thickness. The compact `@` construction alone uses half of nominal thickness so both its counter and exit remain visible; this is an explicit readability exception, not an alternate weight.
- Punctuation is assembled from the same rectangles, square dots, and true diagonals. Parentheses use one direct angular outline with diagonal upper and lower sides, brackets remain orthogonal, mirrored pairs share one source recipe, and `~` is a three-segment diagonal zigzag. The dollar uses two full-thickness vertical segments that enter its upper and lower spaces without blacking out the middle. The ampersand follows the archived angular crossed-stroke topology. `%` uses solid square nodes because miniature counters would not survive the supported review floor.

## Gap rules

The compiler never guesses whether a small space matters. A vulnerable glyph declares a `GapRule` as a recipe contract with a name, its `natural` clearance, its own `minimum`, an `on_small` action, and the geometry's `resolved` clearance.

The design-level defaults are a 14-pixel review floor and an 80-unit minimum gap. Eighty units corresponds to 1.12 pixels at 14 ppem before rasterization. The rule is evaluated as follows:

1. If `natural >= minimum`, the outcome is `preserve` and `resolved` must equal `natural`.
2. If `natural < minimum` and `on_small` is `widen`, the glyph recipe changes local geometry and `resolved` must be at least that rule's `minimum`.
3. If `natural < minimum` and `on_small` is `fill`, the space closes completely and `resolved` must be 0.
4. A nonzero result below the rule's `minimum` is invalid.

The glyph author chooses `widen` or `fill` because that choice is semantic. A space is widened when keeping it open is required for recognition. It is filled when a sub-threshold pinhole or tapered notch is less readable than a complete surface. The contract validates author-supplied scalar values; it does not run a generic nearest-distance scan or reshape a finished outline.

Clearance is measured at a glyph-declared protected cross-section, not by a global closest-point search. For example, a stacked horizontal space is measured vertically between bars, a center notch at its open edge, and a slash window where the slash passes the frame. A taper endpoint that is intentionally buried in a receiver is outside the protected section; treating it as a zero-width gap would be a false collision.

The `0` slash always uses the weight's nominal thickness. There is no automatic thinning fallback: if a future geometry change makes its declared windows too small, blueprint construction fails until the recipe and its raster golden are deliberately revised.

The Bold pilot resolves its declared gaps as follows. Values are font units, rounded here to one decimal place.

| Glyph | Protected space | Natural | Minimum | Outcome | Resolved geometry |
|---|---|---:|---:|---|---:|
| `A` | upper counter | 6.3 | 80 | fill the upper triangular sliver | 0 |
| `@` | nested-frame clearance | 20.0 | 80 | widen with half-thickness local frames | 80.0 |
| `B` | bowl counters | 110.0 | 80 | preserve | 110.0 |
| `M` | tapered center notch | 56.7 | 80 | fill the complete notch | 0 |
| `N` | diagonal windows | 117.7 | 80 | preserve | 117.7 |
| `W` | tapered center notch | 55.3 | 80 | fill the complete notch | 0 |
| `a` | spaces between horizontal bars | 20.0 | 80 | widen with 80-unit local horizontal bars | 80.0 |
| `e` | spaces between horizontal bars | 20.0 | 80 | widen with 80-unit local horizontal bars | 80.0 |
| `g` | lower tail aperture | 80.0 | 80 | preserve | 80.0 |
| `j` | lower tail aperture | 80.0 | 80 | preserve | 80.0 |
| `m` | tapered center notch | 48.4 | 80 | fill the complete notch | 0 |
| `s` | spaces between horizontal bars | 20.0 | 80 | widen with 80-unit local horizontal bars | 80.0 |
| `w` | tapered center notch | 48.4 | 80 | fill the complete notch | 0 |
| `y` | lower tail aperture | 80.0 | 80 | preserve | 80.0 |
| `0` | slash windows | 95.7 | 80 | preserve | 95.7 |

The same declarations run at every weight. `A` fills at all four current weights. The `M`, `W`, `m`, and `w` notches remain naturally open in Regular, Medium, and SemiBold, then fill in Bold. The `g`, `j`, and `y` hooks reach the full -200 descent so their lower apertures retain at least 80 units without thinning the main stems.

## Outline compilation

Glyph recipes already produce filled contours; FontForge never expands a stroked path. Compilation is ordered so cuts cannot be destroyed by an earlier overlap:

1. Add every positive `ink` contour clockwise.
2. Union positive overlaps and correct their direction.
3. Add each `cut` counterclockwise.
4. Union remaining overlaps, correct directions, and round coordinates to integer font units.
5. Remove only exact duplicate vertices and vertices that are collinear in the same direction.
6. Correct direction again, canonicalize contour order and start points, then validate the glyph.
7. Set the advance from `Design` (500 in the current family), assemble fixed font metadata, generate TTF and WOFF2 to temporary files, reopen and validate them, then atomically replace the destination.

No generic smoothing, morphology, or tolerance-based simplification runs after the glyph rule. Those operations could round a hard corner, erase an intentional opening, or silently make the `widen`/`fill` decision. The final TrueType outlines contain only straight, on-curve vertices.

Build ordering and the source epoch are fixed. `check` rebuilds selected formats in a temporary directory and requires byte-for-byte equality with the local candidate.

## Small-size and build validation

Fourteen ppem is the pilot's geometry and readability review floor, not a promise about every renderer or platform. The 10- and 12-pixel specimen rows are non-gating stress tests and the font is not designed for sizes below 14. Browser review at 14, 16, and 24 pixels remains a human gate across all four weights; the 64-pixel sample and blueprint cards expose shape and join defects.

The end-to-end check enforces:

- The exact 95-code-point printable-ASCII map, design-supplied advances, bounds, fixed line metrics, metadata, and valid TTF/WOFF2 files.
- Valid blueprint fields and declared gap outcomes at every weight, including zero clearance for a triggered fill.
- Receiver-aligned `Z`, `2`, `5`, and `7` diagonals, a bounded `1` flag, nominal-thickness punctuation marks, direct filled outlines, and no active stroke expansion.
- Integer, all-on-curve output with no duplicate or removable collinear points.
- A resized 600-unit-wide, 850-unit-ascent blueprint whose proportional `A` terminals resolve from named guides and whose ink and cuts remain inside the resized design bounds.
- Every declarative gap scalar: preserved values remain unchanged, widened values reach their rule's minimum, and the validated `fill` branch resolves to zero. This check does not remeasure final contours.
- Expected Bold gap outcomes plus one-bit 14-, 16-, and 24-ppem XBM goldens for the protected `g` tail aperture.
- A unique one-bit raster signature for every non-space ASCII glyph at 14, 16, and 24 ppem, catching collisions such as `B`/`8`, `s`/`z`, or punctuation that loses its identifying detail.
- Two independent builds with byte-identical TTF and WOFF2 output. The separate `check` command then compares a clean rebuild with the local candidate.

FontForge validation is mandatory during generation and after reopening each file. Maintainer review also includes `fontlint`, `fc-scan`, and the generated specimen before a release candidate is approved.

## Coverage and release gates

The milestone target contains 283 encoded entries:

- The complete U+0000–U+00FF range.
- The 27 defined printable Windows-1252 additions.

C0 controls U+0000–U+001F, space U+0020, DEL and C1 controls U+007F–U+009F, and no-break space U+00A0 are encoded with the 500-unit family advance and no contours. This includes Unicode control characters at U+0080–U+009F as empty glyphs while the printable Windows-1252 characters for those byte positions use their actual Unicode code points such as U+20AC. Undefined Windows-1252 byte positions do not create extra mappings beyond their corresponding empty Unicode C1 controls.

The 67 empty entries leave 216 drawn glyphs. The current compiler contains the 95 printable ASCII entries, including the empty regular space; the JSON manifest already declares all 283 target entries and reports the 216 drawn glyphs as pending until they receive JSON recipes. Latin-1 and the printable Windows-1252 geometry expands only after the ASCII grammar is reviewed and migrated.

A usable base-font release requires all 283 target entries, all four weights, an explicit gap decision for every vulnerable drawn glyph, passing structural/deterministic/raster checks, visual approval at the supported review sizes, approved final family metadata and binaries, and no unresolved base-font design blockers. Only then are release files and a tag created and MamboWiki updated. Icon work remains a separate later milestone.
