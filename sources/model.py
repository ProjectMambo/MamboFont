"""Small direct-outline vocabulary for the Mambo Font blueprint pilot."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite


Number = int | float
Point = tuple[Number, Number]
Contour = tuple[Point, ...]

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

    def __post_init__(self):
        if self.ascent + self.descent != self.upm:
            raise ValueError("ascent + descent must equal units per em")
        if not 0 < self.thickness * 2 < self.ink_right - self.ink_left:
            raise ValueError("thickness leaves no usable counter space")
        if not 0 <= self.ink_left < self.ink_right <= self.advance:
            raise ValueError("ink bounds must fit the advance width")
        if not self.descender < 0 < self.x_height < self.cap_height <= self.ascent:
            raise ValueError("vertical guides are out of order")

    def x(self, name: str) -> Number:
        """Resolve a named horizontal guide."""
        guides = {
            "cell_left": 0,
            "ink_left": self.ink_left,
            "inner_left": self.ink_left + self.thickness,
            "center": self.advance / 2,
            "inner_right": self.ink_right - self.thickness,
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
            "midline": self.cap_height / 2,
            "x_height": self.x_height,
            "cap_height": self.cap_height,
            "accent_height": 760,
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


def glyph(*ink: Contour, cuts: tuple[Contour, ...] = ()):
    """Represent a blueprint as additive ink and explicit cuts."""
    return {"ink": tuple(ink), "cuts": tuple(cuts)}


def validate_blueprint(blueprint) -> None:
    if set(blueprint) != {"ink", "cuts"}:
        raise ValueError("invalid blueprint fields")
    for contour in (*blueprint["ink"], *blueprint["cuts"]):
        polygon(*contour)


_sample = diagonal(Design(), (120, 0), (380, 640))
assert _sample[0][1] == _sample[1][1] == 0
assert _sample[2][1] == _sample[3][1] == 640
_side = (_sample[3][0] - _sample[0][0], _sample[3][1] - _sample[0][1])
_gap = (_sample[1][0] - _sample[0][0], _sample[1][1] - _sample[0][1])
assert abs(abs(_side[0] * _gap[1] - _side[1] * _gap[0]) / hypot(*_side) - 80) < 1e-9
assert tuple(design_for(name).thickness for name in WEIGHT_THICKNESSES) == (80, 93, 107, 120)
