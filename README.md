# MamboFont

MamboFont is Project Mambo's square, blocky monospace type system. The 0.3 candidate separates text and icons into two focused families:

- **Mambo Font** — Regular, Medium, SemiBold, and Bold; every glyph advances 500 units.
- **Mambo Icons** — Regular; every icon advances 1000 units.

The source of truth is compact Python geometry. FontForge turns it directly into deterministic TTF and WOFF2 files; Inkscape, exported SVG caches, and hand-maintained per-weight drawings are no longer part of the build.

## Build

Install Python 3 with FontForge's Python bindings, then run:

```bash
./script/mbfont.py compile 0.3.0 --family all --format ttf woff2 --out dist
```

To expose the same `mbfont` command used by downstream repos, run `./script/install.sh`. It installs a symlink in `$HOME/.local/bin` by default; override that with `MAMBOFONT_BIN_DIR`.

Useful review commands:

```bash
./script/mbfont.py check 0.3.0 --family all --format ttf woff2 --out dist
./script/mbfont.py specimen 0.3.0 --fonts dist --out specimen.html
/usr/bin/python3 tests/test_build.py
```

`check` rebuilds into a temporary directory and byte-compares the result with `dist/`. There is no cache to invalidate: edit a rule, rebuild, and Git shows both the readable source change and any changed candidate binaries.

## Coverage

Mambo Font contains 218 encoded characters: printable ASCII, Latin-1, and the defined printable Windows-1252 additions. Control-code slots are intentionally omitted. Accented letters reuse the same base skeletons and accent components across all four weights.

Mambo Icons contains 30 redesigned functional icons in frozen legacy PUA slots. The three old brand illustrations are retired and their slots stay reserved.

See [DESIGN.md](DESIGN.md) for the geometry rules and icon map. Open [specimen.html](specimen.html) after building to review every weight and icon.

## Layout

```text
sources/        text, icon, and geometry rules
script/         direct build/check/specimen command
tests/          one end-to-end deterministic build check
dist/           review candidate TTF and WOFF2 files
archive/v0.2/   frozen drawings, exports, binaries, docs, and old tooling
```

Nothing in this branch publishes a release or updates downstream consumers. The checked-in 0.3 files are review candidates only.

## License

Distributed under the MIT License. See [LICENSE](LICENSE).
