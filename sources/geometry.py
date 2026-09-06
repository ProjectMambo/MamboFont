"""Tiny shared geometry vocabulary for both Mambo font families."""


def path(*points):
    return tuple(points)


def loop(*points):
    return tuple((*points, points[0]))


def glyph(*paths, dots=(), fills=()):
    return {"paths": tuple(paths), "dots": tuple(dots), "fills": tuple(fills)}


def combine(*specs):
    return glyph(
        *(item for spec in specs for item in spec.get("paths", ())),
        dots=tuple(item for spec in specs for item in spec.get("dots", ())),
        fills=tuple(item for spec in specs for item in spec.get("fills", ())),
    )


def transform(spec, sx=1, sy=1, dx=0, dy=0):
    def point(value):
        return (round(value[0] * sx + dx), round(value[1] * sy + dy))

    return glyph(
        *(tuple(point(p) for p in item) for item in spec.get("paths", ())),
        dots=tuple(
            (round(x * sx + dx), round(y * sy + dy), scale * min(abs(sx), abs(sy)))
            for x, y, scale in spec.get("dots", ())
        ),
        fills=tuple(tuple(point(p) for p in item) for item in spec.get("fills", ())),
    )
