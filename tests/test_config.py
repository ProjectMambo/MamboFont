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


ASCII = set(range(0x21, 0x7F))


def main():
    project = load_project()
    assert len(project.coverage) == 283
    assert len(project.empty) == 67
    assert len(project.pending) == 122
    assert project.empty == frozenset((*range(0x00, 0x21), *range(0x7F, 0xA1)))
    assert {0x20AC, 0x0152, 0x0178, 0x2122} <= project.coverage
    assert {int(key[2:], 16) for key in project.glyphs if key != ".notdef"} == ASCII
    assert project.glyphs[".notdef"]["review"] == "approved"
    assert project.font["weights"] == {
        "Regular": {"css": 400, "thickness": 80},
        "Medium": {"css": 500, "thickness": 93},
        "SemiBold": {"css": 600, "thickness": 107},
        "Bold": {"css": 700, "thickness": 120},
    }

    for weight in project.font["weights"]:
        guides = resolved_guides(project, weight)
        assert guides["x"]["center"] == project.font["metrics"]["advance"] / 2
        assert guides["y"]["baseline"] == 0
        assert all(blueprint_for(project, key, weight)["ink"] for key in project.glyphs)
        assert resolved_glyph(project, ".notdef", weight)["advance"] == 500
        assert all(
            rule.resolved == 0 or rule.resolved >= rule.minimum
            for key in project.glyphs
            for rule in blueprint_for(project, key, weight)["gaps"]
        )

    assert {
        char: blueprint_for(project, f"U+{ord(char):04X}", "Bold")["gaps"][0].outcome
        for char in "AMWgmw"
    } == {"A": "fill", "M": "fill", "W": "fill", "g": "preserve", "m": "fill", "w": "fill"}

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

    print("ok: strict JSON project, printable ASCII configured, controls empty")


if __name__ == "__main__":
    main()
