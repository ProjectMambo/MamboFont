---
title: MamboFont
description: Project Mambo's custom monospace font and SVG-to-font build pipeline.
order: 60
---

::page{layout="project" width="normal" sidebar=true}

# MamboFont

MamboFont is a four-weight monospace family designed for Project Mambo's interfaces. Its repository owns the layered vector source, processed glyph cache, compiled desktop and web fonts, icons, and release tooling.

::button{label="Source code" href="https://github.com/ProjectMambo/MamboFont" variant="secondary" external=true}

## What it contains

- Regular 400, Medium 500, SemiBold 600, and Bold 700 weights.
- ASCII, Latin-1, symbols, broader Unicode mappings, and private-use icons.
- TTF output for desktop use and WOFF2 output for websites.
- A filtered export/compile loop and an all-assets GitHub release command.

## Documentation

::children{view="list" sort="order" direction="asc" show=["title","description"]}

## Current status

The build pipeline is active and has focused local CLI and installer regression checks, but it is not automated by CI. v0.2.4 files are committed locally in the repository, while the latest Git tag is v0.2.3.
