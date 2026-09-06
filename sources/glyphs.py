"""Direct filled-polygon recipes for the first Mambo Font review set."""

from __future__ import annotations

from sources.model import Design, diagonal, glyph, hbar, joined_descending_diagonal, validate_blueprint, vbar


PILOT_CHARACTERS = "HOBSANMVWXZaegmnrIl0128"


def _frame(design: Design, left, bottom, right, top):
    """A square frame made from inward-growing exterior surfaces."""
    t = design.thickness
    return (
        vbar(design, left, bottom, top),
        vbar(design, right - t, bottom, top),
        hbar(design, left, right, bottom),
        hbar(design, left, right, top - t),
    )


def _midbar(design: Design, left, right, center):
    return hbar(design, left, right, center - design.thickness // 2)


def pilot_glyphs(design: Design):
    """Resolve the shared recipes at one weight."""
    t = design.thickness
    left, center, right = design.x("ink_left"), design.x("center"), design.x("ink_right")
    baseline, x_mid = design.y("baseline"), design.y("x_mid")
    mid, x_height, cap = design.y("midline"), design.y("x_height"), design.y("cap_height")
    descender = design.y("descender")
    upper_bowl_right = design.x("upper_bowl_right")

    cap_frame = _frame(design, left, baseline, right, cap)
    x_frame = _frame(design, left, baseline, right, x_height)
    center_stem = center - t // 2

    # Diagonals are continuous four-point polygons. Joined endpoints sit under
    # receiving bars/stems so boolean union cannot leave point-contact joins.
    recipes = {
        "H": glyph(
            vbar(design, left, baseline, cap),
            vbar(design, right - t, baseline, cap),
            _midbar(design, left, right, mid),
        ),
        "O": glyph(*cap_frame),
        "B": glyph(
            vbar(design, left, baseline, cap),
            hbar(design, left, upper_bowl_right, cap - t),
            vbar(design, upper_bowl_right - t, mid, cap),
            _midbar(design, left, right, mid),
            vbar(design, right - t, baseline, mid),
            hbar(design, left, right, baseline),
        ),
        "S": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, left, mid, cap),
            _midbar(design, left, right, mid),
            vbar(design, right - t, baseline, mid),
            hbar(design, left, right, baseline),
        ),
        "A": glyph(
            diagonal(design, (90, baseline), (center, cap)),
            diagonal(design, (410, baseline), (center, cap)),
            _midbar(design, left, right, mid),
        ),
        "N": glyph(
            vbar(design, left, baseline, cap),
            diagonal(design, (left + t, cap), (right - t, baseline)),
            vbar(design, right - t, baseline, cap),
        ),
        "M": glyph(
            vbar(design, left, baseline, cap),
            diagonal(design, (left + t, cap), (center, 260)),
            diagonal(design, (right - t, cap), (center, 260)),
            vbar(design, right - t, baseline, cap),
        ),
        "V": glyph(
            diagonal(design, (90, cap), (center, baseline)),
            diagonal(design, (410, cap), (center, baseline)),
        ),
        "W": glyph(
            vbar(design, left, baseline, cap),
            diagonal(design, (left + t, baseline), (center, mid)),
            diagonal(design, (right - t, baseline), (center, mid)),
            vbar(design, right - t, baseline, cap),
        ),
        "X": glyph(
            diagonal(design, (90, baseline), (410, cap)),
            diagonal(design, (410, baseline), (90, cap)),
        ),
        "Z": glyph(
            hbar(design, left, right, cap - t),
            joined_descending_diagonal(design, baseline + t, cap - t),
            hbar(design, left, right, baseline),
        ),
        "a": glyph(
            hbar(design, left, right, x_height - t),
            vbar(design, right - t, baseline, x_height),
            _midbar(design, left, right, x_mid),
            vbar(design, left, baseline, x_mid),
            hbar(design, left, right, baseline),
        ),
        "e": glyph(
            vbar(design, left, baseline, x_height),
            hbar(design, left, right, x_height - t),
            _midbar(design, left, right, x_mid),
            hbar(design, left, right, baseline),
        ),
        "g": glyph(
            *x_frame,
            vbar(design, right - t, descender, x_height),
            hbar(design, left, right, descender),
        ),
        "m": glyph(
            vbar(design, left, baseline, x_height),
            diagonal(design, (left + t, x_height), (center, x_mid)),
            diagonal(design, (right - t, x_height), (center, x_mid)),
            vbar(design, right - t, baseline, x_height),
        ),
        "n": glyph(
            vbar(design, left, baseline, x_height),
            hbar(design, left, right, x_height - t),
            vbar(design, right - t, baseline, x_height),
        ),
        "r": glyph(
            vbar(design, left, baseline, x_height),
            hbar(design, left, 350, x_height - t),
            vbar(design, 350 - t, x_mid + 40, x_height),
        ),
        "I": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, center_stem, baseline, cap),
            hbar(design, left, right, baseline),
        ),
        "l": glyph(
            vbar(design, 150, baseline, cap),
            hbar(design, 150, 390, baseline),
        ),
        "0": glyph(
            *cap_frame,
            diagonal(design, (left + t, baseline + t / 2), (right - t, cap - t / 2)),
        ),
        "1": glyph(
            diagonal(design, (140, 500), (center, cap)),
            vbar(design, center_stem, baseline, cap),
            hbar(design, left, right, baseline),
        ),
        "2": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, right - t, x_height, cap),
            joined_descending_diagonal(design, baseline + t, x_height, upper_stem=True),
            hbar(design, left, right, baseline),
        ),
        "8": glyph(*cap_frame, _midbar(design, left, right, mid)),
    }

    if set(recipes) != set(PILOT_CHARACTERS):
        raise AssertionError("pilot recipe set is incomplete")
    for blueprint in recipes.values():
        validate_blueprint(blueprint)
    return recipes


for _weight in (80, 93, 107, 120):
    _pilot = pilot_glyphs(Design(thickness=_weight))
    assert all(
        0 <= x <= 500
        for blueprint in _pilot.values()
        for contour in blueprint["ink"]
        for x, _ in contour
    )
