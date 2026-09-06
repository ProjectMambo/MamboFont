# MamboFont design rules

## Mambo Font

- 1000 units per em; 800/-200 typographic metrics and fixed 900/-200 line bounds so accents never change line height between weights.
- Exactly 500 units of advance for every encoded glyph, including spaces and symbols.
- Polygonal centerline skeletons with square ends, mitered joins, open counters, and no intentional rounded corners.
- Cap height 640, x-height 440, baseline 0, working descender -160.
- One skeleton per glyph; weights change only the shared stroke width: Regular 70, Medium 87, SemiBold 103, Bold 120.
- Accents are shared components positioned by cap-height or x-height class. Composite letters are flattened and validated during generation.
- Ambiguous monospace characters stay distinct: `I`, `l`, and `1`; `O` and slashed `0`.

The encoded set is printable ASCII U+0020–U+007E, Latin-1 U+00A0–U+00FF, and the 27 defined printable Windows-1252 additions. That is 218 characters. C0/C1 control bytes and undefined Windows-1252 holes are not glyphs.

## Mambo Icons

- A separate family so wide artwork cannot break the text font's fixed-pitch classification.
- 1000-unit advance, one Regular weight, 60-unit stroke.
- Main shells use x=120–880 and y=-80–680; outward CPU pins stay inside x=60–940. Shapes use straight edges, 45-degree chamfers, and at least 80 units between major features; repeated level ticks use smaller regular gaps.
- State families reuse one shell and vary only the level marks, fill, or explicit off slash.
- Existing v0.2 PUA assignments remain stable. Retired slots are never reused; new icons begin at U+E100.

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

The unusual alphabetical legacy ordering is intentional compatibility behavior, not a sequence to repack.
