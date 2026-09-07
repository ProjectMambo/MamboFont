#!/usr/bin/env python3
"""One dependency-free check for the MamboFont JSON project contract."""

import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sources.config import ConfigError, blueprint_for, load_project, resolved_glyph, resolved_guides
from sources.glyphs import ascii_glyphs
from sources.model import design_for


def main():
    project = load_project()
    assert len(project.coverage) == 283
    assert len(project.empty) == 67
    assert len(project.pending) == 210
    assert project.empty == frozenset((*range(0x00, 0x21), *range(0x7F, 0xA1)))
    assert {0x20AC, 0x0152, 0x0178, 0x2122} <= project.coverage
    assert project.glyphs[".notdef"]["review"] == "approved"
    assert project.font["weights"] == {
        "Regular": {"css": 400, "thickness": 80},
        "Medium": {"css": 500, "thickness": 93},
        "SemiBold": {"css": 600, "thickness": 107},
        "Bold": {"css": 700, "thickness": 120},
    }

    for weight in project.font["weights"]:
        design = design_for(weight)
        assert project.font["metrics"] == {
            name: getattr(design, name)
            for name in (
                "upm", "advance", "ascent", "descent", "cap_height", "x_height",
                "descender", "ink_left", "ink_right",
            )
        }
        guides = resolved_guides(project, weight)
        assert all(abs(guides["x"][name] - design.x(name)) < 1e-9 for name in guides["x"])
        assert all(abs(guides["y"][name] - design.y(name)) < 1e-9 for name in guides["y"])
        notdef = resolved_glyph(project, ".notdef", weight)
        assert notdef["advance"] == design.advance
        assert notdef["shapes"] == (
            {
                "id": "outer", "operation": "add", "primitive": "rectangle",
                "contour": (
                    (design.ink_left, 0), (design.ink_right, 0),
                    (design.ink_right, design.cap_height), (design.ink_left, design.cap_height),
                ),
            },
            {
                "id": "counter", "operation": "subtract", "primitive": "rectangle",
                "contour": (
                    (design.ink_left + design.thickness, design.thickness),
                    (design.ink_right - design.thickness, design.thickness),
                    (design.ink_right - design.thickness, design.cap_height - design.thickness),
                    (design.ink_left + design.thickness, design.cap_height - design.thickness),
                ),
            },
        )
        legacy = ascii_glyphs(design)
        for char in "7AHMOa":
            configured = blueprint_for(project, f"U+{ord(char):04X}", weight)
            assert sorted(configured["ink"]) == sorted(legacy[char]["ink"])
            assert configured["cuts"] == legacy[char]["cuts"]
            assert configured["gaps"] == legacy[char]["gaps"]

    with tempfile.TemporaryDirectory(prefix="mambofont-config-test.") as temporary:
        bad = Path(temporary) / "font.json"
        bad.write_text('{"format":"mambofont","format":"duplicate"}')
        try:
            load_project(bad)
        except ConfigError as error:
            assert "duplicate JSON key" in str(error)
        else:
            raise AssertionError("duplicate JSON fields must fail")

        project_copy = Path(temporary) / "project"
        shutil.copytree(ROOT / "sources", project_copy)
        manifest_path = project_copy / "font.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["guides"]["x"]["cell_left"] = {"ref": "guide.x.center"}
        manifest["guides"]["x"]["center"] = {"ref": "guide.x.cell_left"}
        manifest_path.write_text(json.dumps(manifest))
        try:
            load_project(manifest_path)
        except ConfigError as error:
            assert "cyclic reference" in str(error)
        else:
            raise AssertionError("cyclic guide references must fail")

    print("ok: strict JSON project and representative glyph parity")


if __name__ == "__main__":
    main()
