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

The current compiler covers all 95 printable ASCII characters and encodes every C0, DEL, and C1 control as a deliberate empty glyph. That produces 161 current entries. The milestone manifest covers 283 encoded entries: U+0000–U+00FF plus the 27 defined printable Windows-1252 additions. C0, DEL, C1, regular space, and no-break space account for 67 explicit empty glyphs; the remaining 216 entries require drawn geometry.

The active project covers only the base text family. Previous Mambo Icons assets and generator work are archived until a separate icon-font project is resumed.

## Documentation

::children{view="list" sort="order" direction="asc" show=["title","description"]}

## Current status

Version 0.4.0 is an intentionally incomplete design pilot. The direct-outline generator, gap policy, and local validation exist; no release files, tag, or downstream migration have been made.

The JSON project manifest and strict standard-library evaluator now resolve `.notdef` and every printable ASCII glyph across all four weights. The config covers rectangles, bars, true and receiver-aware diagonals, explicit polygons, subtraction, reusable components, and both threshold-driven gap actions. `compile`, `check`, and `specimen` all consume this same JSON source; the glyph-specific Python recipes were removed after exact normalized-contour parity was proven.

There is no `mbfont edit` command today. The generated `specimen.html` remains the review surface until the editor reaches parity, after which the editor's typable live preview replaces it. The next drawn-coverage phase has 122 Latin-1 and Windows-1252 glyphs pending. MamboWiki will be updated only after the full base family becomes a usable release.
