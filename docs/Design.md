---
title: MamboFont Design Rules
description: Geometry, weight, coverage, and compatibility rules for both generated families.
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

## Mambo Icons

Mambo Icons is separate because its artwork needs twice the text cell width.

- Every icon advances exactly 1000 units.
- The family has one Regular weight with a 60-unit stroke.
- Main artwork stays within x=120–880 and y=-80–680; CPU pins may extend to x=60–940.
- Shells, counters, and state boxes use square corners.
- Diagonals remain only where they carry meaning, such as the speaker cone, level waves, camera-off slash, or headphone silhouette.
- Related level and state icons reuse one shell and change only their indicators, fill, or explicit off mark.

## Stable icon map

The unusual alphabetical v0.2 private-use ordering is frozen for compatibility. Retired brand artwork leaves permanent holes, and future icons begin at U+E100.

| Codepoint | Name | Codepoint | Name |
|---|---|---|---|
| U+E000 | audio-0 | U+E001 | audio-100 |
| U+E002 | audio-25 | U+E003 | audio-50 |
| U+E004 | audio-75 | U+E005 | battery-0 |
| U+E006 | battery-100 | U+E007 | battery-25 |
| U+E008 | battery-50 | U+E009 | battery-75 |
| U+E00A | camera-off | U+E00B | camera-on |
| U+E00C | retired: coconut | U+E00D | retired: cod |
| U+E00E | coffee-empty | U+E00F | coffee-full |
| U+E010 | cpu | U+E011 | disk |
| U+E012 | headphones-0 | U+E013 | headphones-100 |
| U+E014 | headphones-25 | U+E015 | headphones-50 |
| U+E016 | headphones-75 | U+E017 | light-0 |
| U+E018 | light-100 | U+E019 | light-25 |
| U+E01A | light-50 | U+E01B | light-75 |
| U+E01C | lock | U+E01D | retired: mambo |
| U+E01E | off | U+E01F | on |
| U+E020 | unlock |  |  |

## Build invariants

The generator rejects missing or extra codepoints, incorrect advances, horizontal overhangs, invalid FontForge outlines, and stale committed candidates. The end-to-end check also rebuilds twice and requires byte-identical TTF and WOFF2 output.
