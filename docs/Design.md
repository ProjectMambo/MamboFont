---
description: Geometry, weight, coverage, and compatibility rules for MamboFont.
title: MamboFont Design Rules
order: 20
---

::page{layout="docs" width="normal" sidebar=true}

# MamboFont Design Rules

## Mambo Font

Mambo Font keeps the character of the archived v0.2 drawings while making their metrics, coverage, and weights systematic.

- Every encoded glyph advances exactly 500 units in a 1000-unit em.
- Cap height is 640, x-height is 400, baseline is 0, and the working descender is -140.
- Typographic metrics are fixed across weights so accents never change line height.
- Regular, Medium, SemiBold, and Bold use the same centerline skeleton with stroke widths 80, 93, 107, and 120.
- Ends are square and joins are mitered.
- Counters and bowl corners are rectangular. Rounded and beveled corner treatments are not part of the grammar.
- Diagonals are used only when they identify a character, such as A, K, N, R, V, 2, 7, or slash-like punctuation. They are never short corner-smoothing cuts.
- Ambiguous monospace characters remain distinct: serifed I, footed l, flagged 1, square O, and slashed 0.

Accented letters reuse base skeletons and shared mark components. The build positions marks by cap-height or x-height class, flattens the references, and validates the generated outlines.

## Character coverage

The encoded text set contains 218 characters:

- Printable ASCII U+0020–U+007E.
- Latin-1 U+00A0–U+00FF.
- The 27 defined printable Windows-1252 additions.

C0 and C1 controls and undefined Windows-1252 holes are intentionally absent. Combining-mark codepoints are not yet encoded; precomposed characters are supported.

## Build invariants

The generator rejects missing or extra codepoints, incorrect advances, horizontal overhangs, invalid FontForge outlines, and stale committed candidates. The end-to-end check also rebuilds twice and requires byte-identical TTF and WOFF2 output.
