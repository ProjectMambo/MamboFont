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

## Source architecture

The font has one short, direct path from parameters to binaries:

1. `sources/model.py` defines the design dimensions, proportional named guides, weight values, filled-outline primitives, blueprint schema, and `GapRule` contract validation.
2. `sources/glyphs.py` defines each character recipe and the explicit decision for every readability-sensitive gap.
3. `script/mbfont.py` resolves one design per weight, compiles the contours, normalizes and validates them, writes TTF and WOFF2, byte-checks candidates, and generates the review specimen.
4. `tests/test_build.py` checks geometry contracts, raster outcomes, metadata, format validity, and deterministic builds.
5. `specimen.html` is generated review output, not another source of glyph geometry.

There is no SVG-to-font source pipeline and no cache. SVG appears only in the specimen's blueprint cards. Editing a dimension or glyph rule and rebuilding is the complete source-of-truth workflow.

## Coordinate and weight model

Every encoded glyph currently advances 500 units in a 1000-unit em. The compiler reads that advance from `Design` rather than embedding 500 in the outline stage. The fixed default vertical metrics are an 800-unit ascent and 200-unit descent; line metrics do not change between weights.

The default `x` guides include cell edges 0 and 500, ink edges 40 and 460, center 250, and upper-bowl receiver 407.5. The inner guides remain weight-dependent at `ink_left + thickness` and `ink_right - thickness`. Former literal optical positions now have names and ratios within the ink width: diagonal terminals at 5/42 from either edge, the `1` flag at 5/21 from the left, lowercase stem at 11/42, `r` shoulder at 31/42, and lowercase foot at 5/6.

The default `y` guides are descender -140, baseline 0, x-mid at half the x-height, midline at half the cap height, x-height 400, cap height 640, and ascender 800. Former literal join positions are also derived: the `r` join is 3/5 of x-height, the `M` join is 13/32 of cap height, the `1` flag is 25/32 of cap height, and accent height is 3/4 of the way from cap height to ascender. This keeps optical relationships intact when the design dimensions change.

| Style | CSS weight | Nominal thickness |
|---|---:|---:|
| Regular | 400 | 80 |
| Medium | 500 | 93 |
| SemiBold | 600 | 107 |
| Bold | 700 | 120 |

All four weights use the same blueprint fields and primitive topology. Exterior surfaces normally stay fixed while weight grows inward. A local thickness or receiver-position exception is allowed when the gap contract requires it for readability.

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
- M, N, and W retain vertical exterior stems and place their diagonals inside. The tapered diagonal pairs in `M`, `W`, and `m` are clipped at `ink_left` and `ink_right`, keeping the exterior stems square; that local receiver-cap clipping is their explicit exception to constant diagonal thickness. A, V, and X retain identity-critical exterior diagonals.
- Ambiguous monospace characters remain distinct: serifed `I`, footed `l`, flagged `1`, square `O`, and slashed `0`.
- Readability outranks nominal thickness only at a declared local exception; the rest of the glyph keeps the weight's nominal thickness.

## Gap rules

The compiler never guesses whether a small space matters. A vulnerable glyph declares a `GapRule` as a recipe contract with a name, its `natural` clearance, its own `minimum`, an `on_small` action, and the geometry's `resolved` clearance.

The design-level defaults are a 14-pixel review floor and an 80-unit minimum gap. Eighty units corresponds to 1.12 pixels at 14 ppem before rasterization. A recipe may override the minimum for a geometry that needs more raster protection; the resulting value is stored on that rule rather than changing unrelated glyphs. The rule is evaluated as follows:

1. If `natural >= minimum`, the outcome is `preserve` and `resolved` must equal `natural`.
2. If `natural < minimum` and `on_small` is `widen`, the glyph recipe changes local geometry and `resolved` must be at least that rule's `minimum`.
3. If `natural < minimum` and `on_small` is `fill`, the space closes completely and `resolved` must be 0.
4. A nonzero result below the rule's `minimum` is invalid.

The glyph author chooses `widen` or `fill` because that choice is semantic. Counters, apertures, and notches that distinguish a character are widened. Only an incidental sliver that adds no recognition value may be filled. The contract validates author-supplied scalar values; it does not remeasure the final contours after union and rounding, so active outcomes also require raster goldens.

The current pilot has no `fill` geometry and no active `fill` outcome. Only the branch semantics—a small declared gap must resolve to zero—are validated. A future glyph that chooses `fill` must implement the actual closed geometry and add its own raster golden before the outcome is accepted.

Clearance is measured at a glyph-declared protected cross-section, not by a global closest-point search. For example, a stacked horizontal space is measured vertically between bars, a center notch at its open edge, and a slash window where the slash passes the frame. A taper endpoint that is intentionally buried in a receiver is outside the protected section; treating it as a zero-width gap would be a false collision.

The open-edge center notches of `M`, `W`, and `m` taper immediately after their measured mouth. At the default 80 units that mouth can rasterize closed even though the scalar contract passes, so those three rules use a 150-unit minimum, equivalent to 2.4 pixels at 16 ppem before rasterization. Their recipes widen the receiver positions until the open-edge measurement reaches 150 and clip the outer receiver caps to the ink bounds; all other current pilot rules retain the 80-unit default.

The `0` slash always uses the weight's nominal thickness. There is no automatic thinning fallback: if a future geometry change makes its declared windows too small, blueprint construction fails until the recipe and its raster golden are deliberately revised.

The Bold pilot resolves its declared gaps as follows. Values are font units, rounded here to one decimal place.

| Glyph | Protected space | Natural | Minimum | Outcome | Resolved geometry |
|---|---|---:|---:|---|---:|
| `A` | upper counter | 6.3 | 80 | widen with explicit counter cut | 80.0 |
| `B` | bowl counters | 127.5 | 80 | preserve | 127.5 |
| `M` | tapered center notch | 56.7 | 150 | widen by moving diagonal receivers outward | 150.2 |
| `N` | diagonal windows | 117.7 | 80 | preserve | 117.7 |
| `W` | tapered center notch | 55.3 | 150 | widen by moving diagonal receivers outward | 150.9 |
| `a` | spaces between horizontal bars | 20.0 | 80 | widen with 80-unit local horizontal bars | 80.0 |
| `e` | spaces between horizontal bars | 20.0 | 80 | widen with 80-unit local horizontal bars | 80.0 |
| `m` | tapered center notch | 48.4 | 150 | widen by moving diagonal receivers outward | 150.0 |
| `0` | slash windows | 95.7 | 80 | preserve | 95.7 |

The same declarations run at every weight. A thinner weight may naturally preserve a space that Bold must widen.

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

- The exact pilot character map, design-supplied advances, bounds, fixed line metrics, metadata, and valid TTF/WOFF2 files.
- The same blueprint fields and primitive topology at every weight.
- Level diagonal caps, nominal diagonal thickness except for declared clipped receiver caps in `M`, `W`, and `m`, direct filled outlines, and no active stroke expansion.
- Integer, all-on-curve output with no duplicate or removable collinear points.
- A resized 600-unit-wide, 850-unit-ascent blueprint whose proportional `A` terminals resolve from named guides and whose ink and cuts remain inside the resized design bounds.
- Every declarative gap scalar: preserved values remain unchanged, widened values reach their rule's minimum, and the validated `fill` branch resolves to zero. This check does not remeasure final contours.
- Expected Bold outcomes plus one-bit 14-ppem XBM raster goldens for `A`, `B`, `M`, `N`, `W`, `a`, `e`, `m`, and `0`, so an opening cannot disappear unnoticed.
- Focused one-bit 16- and 24-ppem XBM goldens for the tapered `M`, `W`, and `m` open-edge notches, covering the raster failure that requires their 150-unit override.
- Two independent builds with byte-identical TTF and WOFF2 output. The separate `check` command then compares a clean rebuild with the local candidate.

FontForge validation is mandatory during generation and after reopening each file. Maintainer review also includes `fontlint`, `fc-scan`, and the generated specimen before a release candidate is approved.

## Coverage and release gates

The milestone target contains 218 characters:

- Printable ASCII U+0020–U+007E.
- Latin-1 U+00A0–U+00FF.
- The 27 defined printable Windows-1252 additions.

C0 and C1 controls and undefined Windows-1252 holes remain absent. The current pilot contains space plus 23 representative letters and figures; coverage expands only after its geometry is approved.

A usable base-font release requires all 218 target characters, all four weights, an explicit gap decision for every vulnerable glyph, passing structural/deterministic/raster checks, visual approval at the supported review sizes, approved final family metadata and binaries, and no unresolved base-font design blockers. Only then are release files and a tag created and MamboWiki updated. Icon work remains a separate later milestone.
