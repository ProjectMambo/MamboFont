---
title: MamboFont
description: Project Mambo's generated blocky monospace text and icon families.
order: 60
---

::page{layout="project" width="normal" sidebar=true}

# MamboFont

MamboFont is Project Mambo's generated type system. One small Python geometry source produces four text weights and a separate one-weight icon family as deterministic TTF and WOFF2 files.

::button{label="Source code" href="https://github.com/ProjectMambo/MamboFont" variant="secondary" external=true}

## Families

- **Mambo Font** is a 500-unit monospace family in Regular 400, Medium 500, SemiBold 600, and Bold 700.
- **Mambo Icons** is a separate 1000-unit family for functional icons, so wide artwork cannot break text metrics.

## Design

The text family uses square counters, right-angle corners, and no rounded or beveled corner treatment. Long diagonals remain only when they identify the glyph. All weights expand the same centerline skeleton, keeping proportions and details consistent.

Coverage includes 218 printable ASCII, Latin-1, and Windows-1252 characters. The icon family contains 30 redesigned functional icons in stable legacy private-use slots.

## Documentation

::children{view="list" sort="order" direction="asc" show=["title","description"]}

## Current status

Version 0.3.0 is a review candidate. The generator, candidate files, and local validation exist; no 0.3 release or downstream migration has been made.
