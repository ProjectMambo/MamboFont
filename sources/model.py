"""Small direct-outline vocabulary for the Mambo Font blueprint pilot."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite, sqrt


Number = int | float
Point = tuple[Number, Number]
Contour = tuple[Point, ...]
GAP_ACTIONS = {"widen", "fill"}

WEIGHT_THICKNESSES = {
    "Regular": 80,
    "Medium": 93,
    "SemiBold": 107,
    "Bold": 120,
}


@dataclass(frozen=True, slots=True)
class Design:
    """Dimensions shared by every glyph; weight changes only ``thickness``."""

    thickness: int = 80
    advance: int = 500
    upm: int = 1000
    ascent: int = 800
    descent: int = 200
    cap_height: int = 640
    x_height: int = 400
    descender: int = -140
    ink_left: int = 40
    ink_right: int = 460
    review_ppem: int = 14
    minimum_gap: int = 80

    def __post_init__(self):
        if self.ascent + self.descent != self.upm:
            raise ValueError("ascent + descent must equal units per em")
        if not 0 < self.thickness * 2 < self.ink_right - self.ink_left:
            raise ValueError("thickness leaves no usable counter space")
        if not 0 <= self.ink_left < self.ink_right <= self.advance:
            raise ValueError("ink bounds must fit the advance width")
        if not self.descender < 0 < self.x_height < self.cap_height <= self.ascent:
            raise ValueError("vertical guides are out of order")
        if self.review_ppem < 1 or not 0 < self.minimum_gap < self.advance:
            raise ValueError("small-size review settings are invalid")
        if self.x_height <= 2 * self.minimum_gap or self.descent <= self.minimum_gap:
            raise ValueError("dimensions leave no room for protected gaps")

    def x(self, name: str) -> Number:
        """Resolve a named horizontal guide."""
        center = self.advance / 2
        ink_width = self.ink_right - self.ink_left
        guides = {
            "cell_left": 0,
            "ink_left": self.ink_left,
            "inner_left": self.ink_left + self.thickness,
            "one_flag": self.ink_left + ink_width * 5 / 21,
            "lowercase_stem": self.ink_left + ink_width * 11 / 42,
            "diagonal_left": self.ink_left + ink_width * 5 / 42,
            "center": center,
            "shoulder_right": self.ink_left + ink_width * 31 / 42,
            "lowercase_foot": self.ink_left + ink_width * 5 / 6,
            "inner_right": self.ink_right - self.thickness,
            "upper_bowl_right": center + (self.ink_right - center) * 2 / 3,
            "diagonal_right": self.ink_right - ink_width * 5 / 42,
            "ink_right": self.ink_right,
            "cell_right": self.advance,
        }
        try:
            return guides[name]
        except KeyError:
            raise KeyError(f"unknown x guide: {name}") from None

    def y(self, name: str) -> Number:
        """Resolve a named vertical guide."""
        guides = {
            "descender": self.descender,
            "baseline": 0,
            "x_mid": self.x_height / 2,
            "r_join": self.x_height * 3 / 5,
            "m_join": self.cap_height * 13 / 32,
            "midline": self.cap_height / 2,
            "x_height": self.x_height,
            "one_flag": self.cap_height * 25 / 32,
            "cap_height": self.cap_height,
            "accent_height": self.cap_height + (self.ascent - self.cap_height) * 3 / 4,
            "ascender": self.ascent,
        }
        try:
            return guides[name]
        except KeyError:
            raise KeyError(f"unknown y guide: {name}") from None

    def point(self, x: str | Number, y: str | Number) -> Point:
        """Return the intersection of two named guides (or literal values)."""
        return (self.x(x) if isinstance(x, str) else x, self.y(y) if isinstance(y, str) else y)


def design_for(weight: str) -> Design:
    try:
        return Design(thickness=WEIGHT_THICKNESSES[weight])
    except KeyError:
        raise ValueError(f"unknown weight: {weight}") from None


@dataclass(frozen=True, slots=True)
class GapRule:
    """A glyph author's explicit response to one readability-sensitive gap."""

    name: str
    natural: Number
    minimum: Number
    on_small: str
    resolved: Number

    def __post_init__(self):
        if not self.name or not isfinite(self.natural) or self.natural < 0:
            raise ValueError("gap name and natural clearance must be valid")
        if not isfinite(self.minimum) or self.minimum <= 0:
            raise ValueError("minimum gap must be positive")
        if not isfinite(self.resolved) or self.resolved < 0:
            raise ValueError("resolved gap must be finite and non-negative")
        if self.on_small not in GAP_ACTIONS:
            raise ValueError(f"unknown small-gap action: {self.on_small}")
        if self.outcome == "preserve" and self.resolved != self.natural:
            raise ValueError("a preserved gap must remain unchanged")
        if self.outcome == "widen" and self.resolved < self.minimum:
            raise ValueError("a widened gap must reach the minimum")
        if self.outcome == "fill" and self.resolved != 0:
            raise ValueError("a filled gap must close completely")

    @property
    def outcome(self) -> str:
        return "preserve" if self.natural >= self.minimum else self.on_small


def gap_rule(
    design: Design,
    name: str,
    natural: Number,
    on_small: str,
    resolved: Number,
    minimum: Number | None = None,
) -> GapRule:
    return GapRule(
        name,
        natural,
        design.minimum_gap if minimum is None else minimum,
        on_small,
        resolved,
    )


def polygon(*points: Point) -> Contour:
    """Create one straight-edged filled contour."""
    if len(points) < 3:
        raise ValueError("a polygon needs at least three points")
    if points[0] == points[-1]:
        points = points[:-1]
    if len(points) < 3 or any(left == right for left, right in zip(points, (*points[1:], points[0]))):
        raise ValueError("a polygon cannot contain a zero-length edge")
    if not all(isfinite(value) for point_value in points for value in point_value):
        raise ValueError("polygon coordinates must be finite")
    return tuple(points)


def rectangle(left: Number, bottom: Number, right: Number, top: Number) -> Contour:
    if not left < right or not bottom < top:
        raise ValueError("rectangle edges are out of order")
    return polygon((left, bottom), (right, bottom), (right, top), (left, top))


def vbar(
    design: Design,
    left: Number,
    bottom: Number,
    top: Number,
    thickness: Number | None = None,
) -> Contour:
    """Build a vertical bar from its fixed left surface."""
    width = design.thickness if thickness is None else thickness
    return rectangle(left, bottom, left + width, top)


def hbar(
    design: Design,
    left: Number,
    right: Number,
    bottom: Number,
    thickness: Number | None = None,
) -> Contour:
    """Build a horizontal bar from its fixed bottom surface."""
    height = design.thickness if thickness is None else thickness
    return rectangle(left, bottom, right, bottom + height)


def diagonal(
    design: Design,
    start: Point,
    end: Point,
    thickness: Number | None = None,
) -> Contour:
    """Build a constant-perpendicular-width diagonal with horizontal caps."""
    x0, y0 = start
    x1, y1 = end
    if y0 == y1:
        raise ValueError("use hbar for a horizontal segment")
    if y0 > y1:
        x0, y0, x1, y1 = x1, y1, x0, y0
    width = design.thickness if thickness is None else thickness
    if width <= 0:
        raise ValueError("diagonal thickness must be positive")
    dx, dy = x1 - x0, y1 - y0
    half_cap = width * hypot(dx, dy) / (2 * dy)
    return polygon(
        (x0 - half_cap, y0),
        (x0 + half_cap, y0),
        (x1 + half_cap, y1),
        (x1 - half_cap, y1),
    )


def joined_descending_diagonal(
    design: Design,
    lower_y: Number,
    upper_y: Number,
    *,
    upper_stem: bool = False,
) -> Contour:
    """Join left/bottom and right/top receivers without exposed shelves."""
    if not lower_y < upper_y:
        raise ValueError("diagonal guides are out of order")
    width = design.ink_right - design.ink_left
    height = upper_y - lower_y
    thickness = design.thickness
    if height <= thickness:
        raise ValueError("diagonal is too short for its thickness")
    a = height * height - thickness * thickness
    b = 2 * thickness * thickness * width
    c = -thickness * thickness * (width * width + height * height)
    cap = (-b + sqrt(b * b - 4 * a * c)) / (2 * a)
    points = [
        (design.ink_left, lower_y),
        (design.ink_left + cap, lower_y),
        (design.ink_right, upper_y),
    ]
    if upper_stem:
        run = width - cap
        join_top = upper_y + (cap - thickness) * height / run
        points.extend(((design.ink_right, join_top), (design.ink_right - thickness, join_top)))
    else:
        points.append((design.ink_right - cap, upper_y))
    return polygon(*points)


def glyph(
    *ink: Contour,
    cuts: tuple[Contour, ...] = (),
    gaps: tuple[GapRule, ...] = (),
):
    """Represent a blueprint as additive ink and explicit cuts."""
    return {"ink": tuple(ink), "cuts": tuple(cuts), "gaps": tuple(gaps)}


def validate_blueprint(blueprint) -> None:
    if set(blueprint) != {"ink", "cuts", "gaps"}:
        raise ValueError("invalid blueprint fields")
    for contour in (*blueprint["ink"], *blueprint["cuts"]):
        polygon(*contour)
    if not all(isinstance(rule, GapRule) for rule in blueprint["gaps"]):
        raise ValueError("invalid gap rule")
    names = [rule.name for rule in blueprint["gaps"]]
    if len(names) != len(set(names)):
        raise ValueError("gap rule names must be unique within a glyph")


_sample = diagonal(Design(), (120, 0), (380, 640))
assert _sample[0][1] == _sample[1][1] == 0
assert _sample[2][1] == _sample[3][1] == 640
_side = (_sample[3][0] - _sample[0][0], _sample[3][1] - _sample[0][1])
_gap = (_sample[1][0] - _sample[0][0], _sample[1][1] - _sample[0][1])
assert abs(abs(_side[0] * _gap[1] - _side[1] * _gap[0]) / hypot(*_side) - 80) < 1e-9
assert tuple(design_for(name).thickness for name in WEIGHT_THICKNESSES) == (80, 93, 107, 120)
assert GapRule("demo", 20, 80, "widen", 80).outcome == "widen"
assert GapRule("demo", 20, 80, "fill", 0).outcome == "fill"
assert GapRule("demo", 80, 80, "fill", 80).outcome == "preserve"
