---
title: MamboFont
description: Project Mambo's generated blocky monospace typeface.
order: 60
---

::page{layout="project" width="normal" sidebar=true}

# MamboFont

MamboFont is Project Mambo's generated typeface. A small Python blueprint compiler produces four deterministic TTF and WOFF2 weights from direct filled outlines and explicit per-glyph readability rules.

::button{label="Source code" href="https://github.com/ProjectMambo/MamboFont" variant="secondary" external=true}

## Family

- **Mambo Font** is a 500-unit monospace family in Regular 400, Medium 500, SemiBold 600, and Bold 700.

## Design

The family uses square counters, right-angle corners, and no rounded or beveled corner treatment. True diagonals remain only when they identify the glyph and have level ends. Optical positions come from named proportional guides, and all weights share one blueprint topology while thickness grows inward.

Every vulnerable counter, aperture, or notch owns a declarative recipe contract: its minimum clearance and what the recipe does if the natural space is smaller. The default is 80 font units. Identity-bearing apertures such as the lower `g` tail are kept open; tiny `A`, `M`, `W`, `m`, and `w` voids fill when they fall below the threshold. Compiled Bold outlines are raster-gated at 14, 16, and 24 pixels; 10 and 12 pixels are stress tests only.

The current compiler covers all 95 printable ASCII characters. The milestone manifest covers 283 encoded entries: U+0000–U+00FF plus the 27 defined printable Windows-1252 additions. C0, DEL, C1, regular space, and no-break space account for 67 explicit empty glyphs; the remaining 216 entries require drawn geometry.

The active project covers only the base text family. Previous Mambo Icons assets and generator work are archived until a separate icon-font project is resumed.

## Documentation

::children{view="list" sort="order" direction="asc" show=["title","description"]}

## Current status

Version 0.4.0 is an intentionally incomplete design pilot. The direct-outline generator, gap policy, and local validation exist; no release files, tag, or downstream migration have been made.

The JSON project manifest and strict standard-library evaluator now resolve a seven-glyph representative set across all four weights. It covers rectangles, bars, true and receiver-aware diagonals, subtraction, a reusable frame component, and both threshold-driven gap actions. Tests require its source geometry and final normalized contours to match the current Python recipes.

JSON still does not drive the production font build, and there is no `mbfont edit` command today. The Python recipes and generated `specimen.html` remain the current workflow until all printable ASCII migrates and later editor phases reach parity. MamboWiki will be updated only after the full base family becomes a usable release.
