"""Strict loader for the versioned MamboFont JSON project."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from sources.model import (
    Design,
    diagonal,
    gap_rule,
    glyph as make_glyph,
    hbar,
    joined_descending_diagonal,
    polygon,
    rectangle,
    vbar,
)


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
COMPONENT_DEFINITION_KEYS = {"parameters", "shapes"}
GLYPH_KEYS = {
    "format", "schema_version", "codepoint", "name", "advance", "review",
    "values", "points", "shapes", "gaps", "anchors",
}
SHAPE_FIELDS = {
    "rectangle": {"left", "bottom", "right", "top"},
    "hbar": {"left", "right", "bottom", "thickness"},
    "vbar": {"left", "bottom", "top", "thickness"},
    "diagonal": {"from", "to", "thickness"},
    "joined_diagonal": {
        "lower_y", "upper_y", "lower_left", "upper_right", "upper_stem",
    },
    "polygon": {"vertices"},
}
COMPONENT_SHAPE_KEYS = {"id", "component", "parameters"}
POINT_KEYS = {"x", "y"}
GAP_KEYS = {"id", "name", "minimum", "probes", "if_below"}
PROBE_KEYS = {"axis", "between"}
FILL_KEYS = {"action", "to"}
WIDEN_KEYS = {"action", "set"}


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


def design_for(project, weight):
    metrics = project.font["metrics"]
    return Design(
        thickness=project.font["weights"][weight]["thickness"],
        advance=metrics["advance"],
        upm=metrics["upm"],
        ascent=metrics["ascent"],
        descent=metrics["descent"],
        cap_height=metrics["cap_height"],
        x_height=metrics["x_height"],
        descender=metrics["descender"],
        ink_left=metrics["ink_left"],
        ink_right=metrics["ink_right"],
        review_ppem=project.font["review"]["minimum_ppem"],
        minimum_gap=project.font["review"]["minimum_gap"],
    )


def _build_primitive(shape, resolve, points, design, where):
    primitive = shape["primitive"]

    def value(field):
        return resolve(shape[field], f"{where}.{field}")

    if primitive == "rectangle":
        return rectangle(value("left"), value("bottom"), value("right"), value("top"))
    if primitive == "hbar":
        return hbar(
            design, value("left"), value("right"), value("bottom"), value("thickness")
        )
    if primitive == "vbar":
        return vbar(
            design, value("left"), value("bottom"), value("top"), value("thickness")
        )
    if primitive == "diagonal":
        return diagonal(design, points[shape["from"]], points[shape["to"]], value("thickness"))
    if primitive == "joined_diagonal":
        return joined_descending_diagonal(
            design,
            value("lower_y"),
            value("upper_y"),
            lower_left=value("lower_left"),
            upper_right=value("upper_right"),
            upper_stem=shape["upper_stem"],
        )
    if primitive == "polygon":
        return polygon(*(
            (resolve(point["x"], f"{where}.vertices[{index}].x"),
             resolve(point["y"], f"{where}.vertices[{index}].y"))
            for index, point in enumerate(shape["vertices"])
        ))
    raise ConfigError(f"{where}: unsupported primitive {primitive}")


def _resolved_glyph(project: Project, key: str, weight: str, overrides=None):
    try:
        glyph_source = project.glyphs[key]
    except KeyError:
        raise ConfigError(f"unknown glyph: {key}") from None
    guides = resolved_guides(project, weight)
    references = _base_references(project, weight)
    references.update(
        (f"guide.{axis}.{name}", value)
        for axis, resolved in guides.items()
        for name, value in resolved.items()
    )
    definitions = {
        f"value.{name}": scalar for name, scalar in glyph_source["values"].items()
    }
    definitions.update(
        (f"point.{name}.{axis}", scalar)
        for name, point in glyph_source["points"].items()
        for axis, scalar in point.items()
    )
    for name, scalar in (overrides or {}).items():
        definitions[f"value.{name}"] = scalar
    active = set()

    def resolve(value, where):
        return _resolve_scalar(value, references, definitions, weight, active, where)

    for reference in definitions:
        _resolve_reference(reference, references, definitions, weight, active, reference)
    points = {
        name: (references[f"point.{name}.x"], references[f"point.{name}.y"])
        for name in glyph_source["points"]
    }
    design = design_for(project, weight)
    shapes = []
    for shape in glyph_source["shapes"]:
        if "component" not in shape:
            shapes.append({
                "id": shape["id"],
                "operation": shape["operation"],
                "primitive": shape["primitive"],
                "contour": _build_primitive(
                    shape, resolve, points, design, f"{key}.{shape['id']}"
                ),
            })
            continue
        component = project.components["components"][shape["component"]]
        parameters = {
            f"parameter.{name}": resolve(scalar, f"{key}.{shape['id']}.{name}")
            for name, scalar in shape["parameters"].items()
        }

        def resolve_parameter(value, where):
            return _resolve_scalar(value, parameters, {}, weight, set(), where)

        for part in component["shapes"]:
            shapes.append({
                "id": f"{shape['id']}.{part['id']}",
                "operation": part["operation"],
                "primitive": part["primitive"],
                "contour": _build_primitive(
                    part, resolve_parameter, {}, design,
                    f"{key}.{shape['id']}.{part['id']}",
                ),
            })
    return {
        "name": glyph_source["name"],
        "advance": resolve(glyph_source["advance"], f"{key}.advance"),
        "points": points,
        "shapes": tuple(shapes),
        "resolve": resolve,
    }


def resolved_glyph(project: Project, key: str, weight: str):
    state = _resolved_glyph(project, key, weight)
    return {name: value for name, value in state.items() if name != "resolve"}


def _probe(state, probe):
    axis = 0 if probe["axis"] == "x" else 1
    across = 1 - axis
    by_id = {shape["id"]: shape["contour"] for shape in state["shapes"]}
    try:
        first, second = (by_id[name] for name in probe["between"])
    except KeyError as error:
        raise ConfigError(f"gap probe references unexpanded shape {error.args[0]}") from None
    if "at" not in probe:
        first_edge = max(point[axis] for point in first)
        second_edge = min(point[axis] for point in second)
        return max(0, second_edge - first_edge), None, None
    at = state["resolve"](probe["at"], "gap probe")

    def intersections(contour):
        result = set()
        for start, end in zip(contour, (*contour[1:], contour[0])):
            a, b = start[across], end[across]
            if a == b == at:
                result.update((start[axis], end[axis]))
            elif a != b and min(a, b) <= at <= max(a, b):
                result.add(start[axis] + (end[axis] - start[axis]) * (at - a) / (b - a))
        if not result:
            raise ConfigError("gap probe does not intersect its shape")
        return result

    first_edge = max(intersections(first))
    second_edge = min(intersections(second))
    first_point = (first_edge, at) if axis == 0 else (at, first_edge)
    second_point = (second_edge, at) if axis == 0 else (at, second_edge)
    return max(0, second_edge - first_edge), first_point, second_point


def blueprint_for(project: Project, key: str, weight: str):
    source = project.glyphs[key]
    state = _resolved_glyph(project, key, weight)
    rules = []
    patches = []
    for gap_source in source["gaps"]:
        measured = [_probe(state, probe) for probe in gap_source["probes"]]
        natural = min(value for value, _, _ in measured)
        minimum = state["resolve"](gap_source["minimum"], f"{key}.{gap_source['id']}.minimum")
        fallback = gap_source["if_below"]
        resolved = natural
        if natural < minimum and fallback["action"] == "widen":
            state = _resolved_glyph(project, key, weight, fallback["set"])
            resolved = min(_probe(state, probe)[0] for probe in gap_source["probes"])
        elif natural < minimum and fallback["action"] == "fill":
            if len(measured) != 1 or measured[0][1] is None:
                raise ConfigError(f"{key}.{gap_source['id']}: fill needs one cross-section")
            _, first, second = measured[0]
            if natural:
                patches.append(polygon(first, second, state["points"][fallback["to"]]))
            resolved = 0
        rules.append(gap_rule(
            design_for(project, weight), gap_source["name"], natural,
            fallback["action"], resolved, minimum,
        ))
    ink = [shape["contour"] for shape in state["shapes"] if shape["operation"] == "add"]
    cuts = tuple(
        shape["contour"] for shape in state["shapes"] if shape["operation"] == "subtract"
    )
    return make_glyph(*ink, *patches, cuts=cuts, gaps=tuple(rules))


def _validate_components(value):
    _keys(value, COMPONENT_KEYS, "components")
    if value["format"] != "mambofont-components" or value["schema_version"] != 1:
        raise ConfigError("components: unsupported format or schema version")
    if not isinstance(value["components"], dict):
        raise ConfigError("components: expected an object")


def _validate_shape(shape, where, weight_ids, point_ids, components, *, allow_component):
    if not isinstance(shape, dict) or not isinstance(shape.get("id"), str) or not NAME.fullmatch(shape["id"]):
        raise ConfigError(f"{where}: invalid shape or id")
    if "component" in shape:
        if not allow_component:
            raise ConfigError(f"{where}: nested components are not supported")
        _keys(shape, COMPONENT_SHAPE_KEYS, where)
        if not isinstance(shape["component"], str) or shape["component"] not in components:
            raise ConfigError(f"{where}: unknown component {shape['component']}")
        parameters = components[shape["component"]]["parameters"]
        if not isinstance(shape["parameters"], dict) or set(shape["parameters"]) != set(parameters):
            raise ConfigError(f"{where}: component parameters do not match")
        for name, scalar in shape["parameters"].items():
            _scalar(scalar, f"{where}.parameters.{name}", weight_ids)
        return
    primitive = shape.get("primitive")
    if primitive not in SHAPE_FIELDS:
        raise ConfigError(f"{where}: unsupported primitive {primitive!r}")
    _keys(shape, {"id", "operation", "primitive"} | SHAPE_FIELDS[primitive], where)
    if shape["operation"] not in {"add", "subtract"}:
        raise ConfigError(f"{where}: invalid operation")
    if primitive == "diagonal":
        if (
            not isinstance(shape["from"], str)
            or not isinstance(shape["to"], str)
            or shape["from"] not in point_ids
            or shape["to"] not in point_ids
        ):
            raise ConfigError(f"{where}: diagonal references an unknown point")
        _scalar(shape["thickness"], f"{where}.thickness", weight_ids)
        return
    if primitive == "polygon":
        vertices = shape["vertices"]
        if not isinstance(vertices, list) or len(vertices) < 3:
            raise ConfigError(f"{where}.vertices: expected at least three points")
        for index, point in enumerate(vertices):
            _keys(point, POINT_KEYS, f"{where}.vertices[{index}]")
            for axis, scalar in point.items():
                _scalar(scalar, f"{where}.vertices[{index}].{axis}", weight_ids)
        return
    if primitive == "joined_diagonal":
        if not isinstance(shape["upper_stem"], bool):
            raise ConfigError(f"{where}.upper_stem: expected a boolean")
        fields = SHAPE_FIELDS[primitive] - {"upper_stem"}
    else:
        fields = SHAPE_FIELDS[primitive]
    for field in fields:
        _scalar(shape[field], f"{where}.{field}", weight_ids)


def _validate_component_definitions(value, weight_ids):
    for name, component in value["components"].items():
        where = f"components.{name}"
        if not isinstance(name, str) or not NAME.fullmatch(name) or not isinstance(component, dict):
            raise ConfigError(f"{where}: invalid component")
        _keys(component, COMPONENT_DEFINITION_KEYS, where)
        parameters = component["parameters"]
        if (
            not isinstance(parameters, list)
            or not parameters
            or len(parameters) != len(set(parameters))
            or not all(isinstance(item, str) and NAME.fullmatch(item) for item in parameters)
        ):
            raise ConfigError(f"{where}.parameters: expected unique names")
        if not isinstance(component["shapes"], list) or not component["shapes"]:
            raise ConfigError(f"{where}.shapes: expected shapes")
        ids = set()
        for index, shape in enumerate(component["shapes"]):
            _validate_shape(
                shape, f"{where}.shapes[{index}]", weight_ids, set(), value["components"],
                allow_component=False,
            )
            if shape["id"] in ids:
                raise ConfigError(f"{where}: duplicate shape id {shape['id']}")
            ids.add(shape["id"])


def _validate_glyph(value, filename, weight_ids, components):
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
    if value["anchors"]:
        raise ConfigError(f"{filename}: anchors are deferred until component composition")
    for name, scalar in value["values"].items():
        if not NAME.fullmatch(name):
            raise ConfigError(f"{filename}.values: invalid name {name!r}")
        _scalar(scalar, f"{filename}.values.{name}", weight_ids)
    for name, point in value["points"].items():
        if not NAME.fullmatch(name):
            raise ConfigError(f"{filename}.points: invalid name {name!r}")
        _keys(point, POINT_KEYS, f"{filename}.points.{name}")
        for axis, scalar in point.items():
            _scalar(scalar, f"{filename}.points.{name}.{axis}", weight_ids)
    if not isinstance(value["gaps"], list):
        raise ConfigError(f"{filename}: gaps must be an array")
    if not isinstance(value["shapes"], list) or not value["shapes"]:
        raise ConfigError(f"{filename}: expected at least one shape")
    shape_ids = set()
    for index, shape in enumerate(value["shapes"]):
        where = f"{filename}.shapes[{index}]"
        _validate_shape(
            shape, where, weight_ids, set(value["points"]), components, allow_component=True
        )
        if shape["id"] in shape_ids:
            raise ConfigError(f"{where}: duplicate shape id")
        shape_ids.add(shape["id"])
    if len(value["gaps"]) > 1:
        raise ConfigError(f"{filename}: Phase 2 supports one gap rule per glyph")
    for index, gap in enumerate(value["gaps"]):
        where = f"{filename}.gaps[{index}]"
        _keys(gap, GAP_KEYS, where)
        if (
            not isinstance(gap["id"], str)
            or not NAME.fullmatch(gap["id"])
            or not isinstance(gap["name"], str)
            or not gap["name"]
        ):
            raise ConfigError(f"{where}: invalid gap identity")
        _scalar(gap["minimum"], f"{where}.minimum", weight_ids)
        if not isinstance(gap["probes"], list) or not gap["probes"]:
            raise ConfigError(f"{where}.probes: expected at least one probe")
        for probe_index, probe in enumerate(gap["probes"]):
            probe_where = f"{where}.probes[{probe_index}]"
            allowed = (PROBE_KEYS, PROBE_KEYS | {"at"})
            if not isinstance(probe, dict) or set(probe) not in allowed:
                raise ConfigError(f"{probe_where}: invalid probe fields")
            if probe["axis"] not in {"x", "y"}:
                raise ConfigError(f"{probe_where}: invalid axis")
            if (
                not isinstance(probe["between"], list)
                or len(probe["between"]) != 2
                or any(not isinstance(item, str) or item not in shape_ids for item in probe["between"])
            ):
                raise ConfigError(f"{probe_where}: unknown shape in between")
            if "at" in probe:
                _scalar(probe["at"], f"{probe_where}.at", weight_ids)
        fallback = gap["if_below"]
        if not isinstance(fallback, dict) or fallback.get("action") not in {"fill", "widen"}:
            raise ConfigError(f"{where}.if_below: invalid fallback")
        if fallback["action"] == "fill":
            _keys(fallback, FILL_KEYS, f"{where}.if_below")
            if not isinstance(fallback["to"], str) or fallback["to"] not in value["points"]:
                raise ConfigError(f"{where}.if_below: unknown fill point")
        else:
            _keys(fallback, WIDEN_KEYS, f"{where}.if_below")
            if not isinstance(fallback["set"], dict) or not fallback["set"]:
                raise ConfigError(f"{where}.if_below.set: expected value replacements")
            for name, scalar in fallback["set"].items():
                if name not in value["values"]:
                    raise ConfigError(f"{where}.if_below.set: unknown value {name}")
                _scalar(scalar, f"{where}.if_below.set.{name}", weight_ids)
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
    _validate_component_definitions(components, font["weights"])
    if not glyphs_path.is_dir():
        raise ConfigError(f"files.glyphs: not a directory: {glyphs_path}")
    glyphs = {}
    for glyph_path in sorted(glyphs_path.glob("*.json")):
        glyph = _read(glyph_path)
        _validate_glyph(glyph, glyph_path.name, font["weights"], components["components"])
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
            try:
                blueprint_for(project, key, weight)
            except (ConfigError, ValueError) as error:
                raise ConfigError(f"{key} ({weight}): {error}") from error
    return project


if __name__ == "__main__":
    project = load_project()
    print(
        f"ok: {len(project.coverage)} target code points, "
        f"{len(project.empty)} empty, {len(project.pending)} pending"
    )
