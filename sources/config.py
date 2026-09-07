"""Strict loader for the versioned MamboFont JSON project."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from math import isfinite
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).with_name("font.json")
CODEPOINT = re.compile(r"U\+([0-9A-F]{4,6})")
NAME = re.compile(r"[a-z][a-z0-9_]*")
SCALAR_KEYS = ({"ref"}, {"constant", "terms"}, {"by_weight"})
FONT_KEYS = {
    "format", "schema_version", "family", "metrics", "review", "weights",
    "guides", "coverage", "empty", "files",
}
FAMILY_KEYS = {"name", "postscript_name", "vendor", "copyright", "license", "license_url"}
METRIC_KEYS = {
    "upm", "advance", "ascent", "descent", "cap_height", "x_height",
    "descender", "ink_left", "ink_right",
}
REVIEW_KEYS = {"minimum_ppem", "minimum_gap", "review_ppem", "stress_ppem"}
WEIGHT_KEYS = {"css", "thickness"}
SET_KEYS = {"ranges", "codepoints"}
FILE_KEYS = {"components", "glyphs"}
COMPONENT_KEYS = {"format", "schema_version", "components"}
GLYPH_KEYS = {
    "format", "schema_version", "codepoint", "name", "advance", "review",
    "values", "points", "shapes", "gaps", "anchors",
}
RECTANGLE_KEYS = {"id", "operation", "primitive", "left", "bottom", "right", "top"}


class ConfigError(ValueError):
    """A JSON project is unsafe, incomplete, or internally inconsistent."""


@dataclass(frozen=True, slots=True)
class Project:
    path: Path
    font: dict
    components: dict
    glyphs: dict[str, dict]
    coverage: frozenset[int]
    empty: frozenset[int]

    @property
    def pending(self) -> frozenset[int]:
        configured = {
            parse_codepoint(glyph["codepoint"])
            for glyph in self.glyphs.values()
            if "codepoint" in glyph
        }
        return self.coverage - self.empty - configured


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ConfigError(f"non-finite JSON number: {value}")


def _read(path: Path):
    try:
        with path.open(encoding="utf-8") as source:
            value = json.load(source, object_pairs_hook=_object, parse_constant=_constant)
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise ConfigError(f"{path}: top level must be an object")
    return value


def _keys(value, expected, where):
    if not isinstance(value, dict) or set(value) != expected:
        missing = sorted(expected - set(value)) if isinstance(value, dict) else sorted(expected)
        extra = sorted(set(value) - expected) if isinstance(value, dict) else []
        raise ConfigError(f"{where}: invalid fields; missing={missing}, extra={extra}")


def _number(value, where, *, integer=False, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ConfigError(f"{where}: expected a finite number")
    if integer and not isinstance(value, int):
        raise ConfigError(f"{where}: expected an integer")
    if positive and value <= 0:
        raise ConfigError(f"{where}: expected a positive number")
    return value


def parse_codepoint(value: str) -> int:
    match = CODEPOINT.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ConfigError(f"invalid code point: {value!r}")
    codepoint = int(match.group(1), 16)
    if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
        raise ConfigError(f"invalid Unicode scalar: {value}")
    return codepoint


def _codepoint_set(value, where):
    _keys(value, SET_KEYS, where)
    if not isinstance(value["ranges"], list) or not isinstance(value["codepoints"], list):
        raise ConfigError(f"{where}: ranges and codepoints must be arrays")
    result = set()
    for index, item in enumerate(value["ranges"]):
        if not isinstance(item, list) or len(item) != 2:
            raise ConfigError(f"{where}.ranges[{index}]: expected [first, last]")
        first, last = map(parse_codepoint, item)
        if first > last:
            raise ConfigError(f"{where}.ranges[{index}]: reversed range")
        additions = set(range(first, last + 1))
        if result & additions:
            raise ConfigError(f"{where}.ranges[{index}]: overlapping code points")
        result.update(additions)
    for item in value["codepoints"]:
        codepoint = parse_codepoint(item)
        if codepoint in result:
            raise ConfigError(f"{where}: duplicate code point {item}")
        result.add(codepoint)
    return frozenset(result)


def _scalar(value, where, weight_ids):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        _number(value, where)
        return
    if not isinstance(value, dict) or set(value) not in SCALAR_KEYS:
        raise ConfigError(f"{where}: invalid scalar")
    if "ref" in value:
        if not isinstance(value["ref"], str) or not value["ref"]:
            raise ConfigError(f"{where}.ref: expected a reference")
    elif "terms" in value:
        _number(value["constant"], f"{where}.constant")
        if not isinstance(value["terms"], dict) or not value["terms"]:
            raise ConfigError(f"{where}.terms: expected reference coefficients")
        for reference, coefficient in value["terms"].items():
            if not isinstance(reference, str) or not reference:
                raise ConfigError(f"{where}.terms: invalid reference")
            _number(coefficient, f"{where}.terms.{reference}")
    else:
        if not isinstance(value["by_weight"], dict) or set(value["by_weight"]) != set(weight_ids):
            raise ConfigError(f"{where}.by_weight: expected every configured weight")
        for weight, number in value["by_weight"].items():
            _number(number, f"{where}.by_weight.{weight}")


def _relative_path(root, value, where):
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{where}: expected a relative path")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ConfigError(f"{where}: path must stay inside the project")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ConfigError(f"{where}: path must stay inside the project")
    return path


def _validate_font(font):
    _keys(font, FONT_KEYS, "font")
    if font["format"] != "mambofont" or font["schema_version"] != 1:
        raise ConfigError("font: unsupported format or schema version")
    _keys(font["family"], FAMILY_KEYS, "family")
    if not all(isinstance(value, str) and value for value in font["family"].values()):
        raise ConfigError("family: metadata must be non-empty strings")

    metrics = font["metrics"]
    _keys(metrics, METRIC_KEYS, "metrics")
    for name, value in metrics.items():
        _number(value, f"metrics.{name}", integer=True)
    if metrics["upm"] != metrics["ascent"] + metrics["descent"]:
        raise ConfigError("metrics: ascent + descent must equal upm")
    if not 0 <= metrics["ink_left"] < metrics["ink_right"] <= metrics["advance"]:
        raise ConfigError("metrics: ink bounds must fit the advance")
    if not metrics["descender"] < 0 < metrics["x_height"] < metrics["cap_height"] <= metrics["ascent"]:
        raise ConfigError("metrics: vertical guides are out of order")

    review = font["review"]
    _keys(review, REVIEW_KEYS, "review")
    _number(review["minimum_ppem"], "review.minimum_ppem", integer=True, positive=True)
    _number(review["minimum_gap"], "review.minimum_gap", integer=True, positive=True)
    for field in ("review_ppem", "stress_ppem"):
        values = review[field]
        if not isinstance(values, list) or values != sorted(set(values)):
            raise ConfigError(f"review.{field}: expected sorted unique sizes")
        for index, value in enumerate(values):
            _number(value, f"review.{field}[{index}]", integer=True, positive=True)
    if review["minimum_ppem"] not in review["review_ppem"]:
        raise ConfigError("review: minimum_ppem must be a review size")
    if set(review["review_ppem"]) & set(review["stress_ppem"]):
        raise ConfigError("review: review and stress sizes must not overlap")

    weights = font["weights"]
    if not isinstance(weights, dict) or not weights:
        raise ConfigError("weights: expected at least one weight")
    css_values = set()
    for name, weight in weights.items():
        if not isinstance(name, str) or not name:
            raise ConfigError("weights: invalid weight name")
        _keys(weight, WEIGHT_KEYS, f"weights.{name}")
        _number(weight["css"], f"weights.{name}.css", integer=True, positive=True)
        _number(weight["thickness"], f"weights.{name}.thickness", integer=True, positive=True)
        if weight["css"] in css_values:
            raise ConfigError("weights: CSS weights must be unique")
        css_values.add(weight["css"])
        if weight["thickness"] * 2 >= metrics["ink_right"] - metrics["ink_left"]:
            raise ConfigError(f"weights.{name}: thickness leaves no counter space")

    guides = font["guides"]
    _keys(guides, {"x", "y"}, "guides")
    for axis in ("x", "y"):
        if not isinstance(guides[axis], dict) or not guides[axis]:
            raise ConfigError(f"guides.{axis}: expected named guides")
        for name, scalar in guides[axis].items():
            if not NAME.fullmatch(name):
                raise ConfigError(f"guides.{axis}: invalid name {name!r}")
            _scalar(scalar, f"guides.{axis}.{name}", weights)

    _keys(font["files"], FILE_KEYS, "files")


def _resolve_scalar(value, references, definitions, weight, active, where):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if "by_weight" in value:
        return value["by_weight"][weight]
    if "ref" in value:
        return _resolve_reference(value["ref"], references, definitions, weight, active, where)
    return value["constant"] + sum(
        coefficient * _resolve_reference(reference, references, definitions, weight, active, where)
        for reference, coefficient in value["terms"].items()
    )


def _resolve_reference(reference, references, definitions, weight, active, where):
    if reference in references:
        return references[reference]
    if reference not in definitions:
        raise ConfigError(f"{where}: unknown reference {reference}")
    if reference in active:
        raise ConfigError(f"{where}: cyclic reference through {reference}")
    active.add(reference)
    result = _resolve_scalar(
        definitions[reference], references, definitions, weight, active, reference
    )
    active.remove(reference)
    _number(result, reference)
    references[reference] = result
    return result


def _base_references(project, weight):
    try:
        weight_data = project.font["weights"][weight]
    except KeyError:
        raise ConfigError(f"unknown weight: {weight}") from None
    return {
        **{f"metrics.{name}": value for name, value in project.font["metrics"].items()},
        **{f"review.{name}": value for name, value in project.font["review"].items() if isinstance(value, (int, float))},
        **{f"weight.{name}": value for name, value in weight_data.items()},
    }


def resolved_guides(project: Project, weight: str):
    values = _base_references(project, weight)
    definitions = {
        f"guide.{axis}.{name}": scalar
        for axis, guides in project.font["guides"].items()
        for name, scalar in guides.items()
    }
    active = set()
    for reference in definitions:
        _resolve_reference(reference, values, definitions, weight, active, reference)
    x = {name: values[f"guide.x.{name}"] for name in project.font["guides"]["x"]}
    y = {name: values[f"guide.y.{name}"] for name in project.font["guides"]["y"]}
    metrics = project.font["metrics"]
    if not all(0 <= value <= metrics["advance"] for value in x.values()):
        raise ConfigError(f"guides.x: {weight} guide outside the advance")
    if not all(-metrics["descent"] <= value <= metrics["ascent"] for value in y.values()):
        raise ConfigError(f"guides.y: {weight} guide outside vertical bounds")
    return {"x": x, "y": y}


def resolved_glyph(project: Project, key: str, weight: str):
    try:
        glyph = project.glyphs[key]
    except KeyError:
        raise ConfigError(f"unknown glyph: {key}") from None
    guides = resolved_guides(project, weight)
    values = _base_references(project, weight)
    values.update(
        (f"guide.{axis}.{name}", value)
        for axis, resolved in guides.items()
        for name, value in resolved.items()
    )
    advance = _resolve_scalar(glyph["advance"], values, {}, weight, set(), f"{key}.advance")
    shapes = []
    for shape in glyph["shapes"]:
        resolved = {field: shape[field] for field in ("id", "operation", "primitive")}
        for field in ("left", "bottom", "right", "top"):
            resolved[field] = _resolve_scalar(
                shape[field], values, {}, weight, set(), f"{key}.{shape['id']}.{field}"
            )
        if not resolved["left"] < resolved["right"] or not resolved["bottom"] < resolved["top"]:
            raise ConfigError(f"{key}.{shape['id']}: rectangle edges are out of order")
        shapes.append(resolved)
    return {"name": glyph["name"], "advance": advance, "shapes": tuple(shapes)}


def _validate_components(value):
    _keys(value, COMPONENT_KEYS, "components")
    if value["format"] != "mambofont-components" or value["schema_version"] != 1:
        raise ConfigError("components: unsupported format or schema version")
    if not isinstance(value["components"], dict) or value["components"]:
        raise ConfigError("components: Phase 1 requires an empty component map")


def _validate_glyph(value, filename, weight_ids):
    required = GLYPH_KEYS - {"codepoint"}
    if not isinstance(value, dict) or not required <= set(value) <= GLYPH_KEYS:
        raise ConfigError(f"{filename}: invalid glyph fields")
    if value["format"] != "mambofont-glyph" or value["schema_version"] != 1:
        raise ConfigError(f"{filename}: unsupported format or schema version")
    if not isinstance(value["name"], str) or not value["name"]:
        raise ConfigError(f"{filename}: invalid glyph name")
    if value["review"] not in {"draft", "review", "approved"}:
        raise ConfigError(f"{filename}: invalid review state")
    _scalar(value["advance"], f"{filename}.advance", weight_ids)
    if not all(isinstance(value[field], dict) for field in ("values", "points", "anchors")):
        raise ConfigError(f"{filename}: values, points, and anchors must be objects")
    if not isinstance(value["gaps"], list):
        raise ConfigError(f"{filename}: gaps must be an array")
    if value["values"] or value["points"] or value["anchors"] or value["gaps"]:
        raise ConfigError(f"{filename}: Phase 1 supports only the .notdef rectangle pilot")
    if not isinstance(value["shapes"], list) or not value["shapes"]:
        raise ConfigError(f"{filename}: expected at least one shape")
    shape_ids = set()
    for index, shape in enumerate(value["shapes"]):
        where = f"{filename}.shapes[{index}]"
        _keys(shape, RECTANGLE_KEYS, where)
        if shape["primitive"] != "rectangle" or shape["operation"] not in {"add", "subtract"}:
            raise ConfigError(f"{where}: unsupported Phase 1 shape")
        if not isinstance(shape["id"], str) or not NAME.fullmatch(shape["id"]):
            raise ConfigError(f"{where}: invalid shape id")
        if shape["id"] in shape_ids:
            raise ConfigError(f"{where}: duplicate shape id")
        shape_ids.add(shape["id"])
        for field in ("left", "bottom", "right", "top"):
            _scalar(shape[field], f"{where}.{field}", weight_ids)
    if "codepoint" in value:
        codepoint = parse_codepoint(value["codepoint"])
        if filename != f"U+{codepoint:04X}.json":
            raise ConfigError(f"{filename}: filename does not match code point")
    elif filename != "_notdef.json" or value["name"] != ".notdef":
        raise ConfigError(f"{filename}: only _notdef.json may omit codepoint")


def load_project(path: Path | str = DEFAULT_CONFIG) -> Project:
    path = Path(path).resolve()
    font = _read(path)
    _validate_font(font)
    root = path.parent
    components_path = _relative_path(root, font["files"]["components"], "files.components")
    glyphs_path = _relative_path(root, font["files"]["glyphs"], "files.glyphs")
    components = _read(components_path)
    _validate_components(components)
    if not glyphs_path.is_dir():
        raise ConfigError(f"files.glyphs: not a directory: {glyphs_path}")
    glyphs = {}
    for glyph_path in sorted(glyphs_path.glob("*.json")):
        glyph = _read(glyph_path)
        _validate_glyph(glyph, glyph_path.name, font["weights"])
        key = glyph.get("codepoint", ".notdef")
        if key in glyphs:
            raise ConfigError(f"duplicate glyph: {key}")
        glyphs[key] = glyph
    if ".notdef" not in glyphs:
        raise ConfigError("glyphs: missing _notdef.json")
    coverage = _codepoint_set(font["coverage"], "coverage")
    empty = _codepoint_set(font["empty"], "empty")
    if not empty <= coverage:
        raise ConfigError("empty: code points must be part of coverage")
    for glyph in glyphs.values():
        if "codepoint" in glyph and parse_codepoint(glyph["codepoint"]) not in coverage:
            raise ConfigError(f"glyph outside coverage: {glyph['codepoint']}")
    project = Project(path, font, components, glyphs, coverage, empty)
    for weight in font["weights"]:
        resolved_guides(project, weight)
        for key in glyphs:
            resolved_glyph(project, key, weight)
    return project


if __name__ == "__main__":
    project = load_project()
    print(
        f"ok: {len(project.coverage)} target code points, "
        f"{len(project.empty)} empty, {len(project.pending)} pending"
    )
