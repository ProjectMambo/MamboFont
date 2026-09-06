---
description: Geometry, weight, coverage, and compatibility rules for MamboFont.
title: MamboFont Design Rules
order: 20
---

::page{layout="docs" width="normal" sidebar=true}

# MamboFont Design Rules

## Mambo Font

Mambo Font keeps the character of the archived v0.2 drawings while making its outlines, coverage, and weights systematic.

- Every encoded glyph advances exactly 500 units in a 1000-unit em.
- The design space has an 800-unit ascent and 200-unit descent. Cap height is 640, x-height is 400, baseline is 0, and the working descender is -140.
- Typographic metrics are fixed across weights so accents never change line height.
- Regular, Medium, SemiBold, and Bold use the same blueprint topology with thicknesses 80, 93, 107, and 120.
- Counters and bowl corners are rectangular. Rounded and beveled corner treatments are not part of the grammar.
- Diagonals are used only when they identify a character. They are true straight bands with parallel sides and level horizontal ends, never stair steps or short corner-smoothing cuts.
- Ambiguous monospace characters remain distinct: serifed I, footed l, flagged 1, square O, and slashed 0.

## Blueprint grammar

One immutable design record defines the dimensions, named x/y guides, and weight thickness. Glyph recipes select guide intersections and combine a deliberately small vocabulary:

- Edge-anchored horizontal and vertical filled bars.
- Constant-thickness diagonal polygons with horizontal caps.
- Explicit filled polygons or cuts only for shapes the shared primitives cannot express.
- Reusable components when accent work begins.

Most exterior surfaces stay fixed while weight grows inward. M, N, and W keep vertical outer stems and place diagonals inside them. A, V, and X retain identity-critical exterior diagonals, but their terminals still end level. Intended joins overlap and are unioned; accidental contacts and gaps fail review instead of being guessed into shape.

## Outline compilation

The recipe already produces filled contours; FontForge never expands a stroked path. The compiler normalizes polygon winding, unions intended overlaps, rounds to integer font units, removes only exact duplicate or collinear vertices, canonicalizes contour order, and validates the result. It does not call generic smoothing or simplification.

SVG is a review view, not an intermediate font format. The same final straight contours are written as all-on-curve TrueType vertices, then serialized as TTF and WOFF2.

## Character coverage

The milestone target contains 218 characters:

- Printable ASCII U+0020–U+007E.
- Latin-1 U+00A0–U+00FF.
- The 27 defined printable Windows-1252 additions.

C0 and C1 controls and undefined Windows-1252 holes will remain absent. The current pilot contains space plus 23 representative letters and figures; it must pass visual review before coverage expands.

## Build invariants

The pilot generator rejects missing or extra codepoints, incorrect advances, design-space overhangs, curve points, invalid outlines, and stale review files. Source checks enforce shared primitive topology and horizontal diagonal caps across weights. The end-to-end check rebuilds twice and requires byte-identical TTF and WOFF2 output.

Visual style remains an explicit human gate. The compiler repairs topology only; it never makes aesthetic decisions on behalf of a glyph recipe.
