"""Direct filled-polygon recipes for the first Mambo Font review set."""

from __future__ import annotations

from sources.model import (
    Design,
    diagonal,
    gap_rule,
    glyph,
    hbar,
    joined_descending_diagonal,
    rectangle,
    validate_blueprint,
    vbar,
)


PILOT_CHARACTERS = "HOBSANMVWXZaegmnrIl0128"
TAPERED_NOTCH_MINIMUM = 150


def _frame(design: Design, left, bottom, right, top):
    """A square frame made from inward-growing exterior surfaces."""
    t = design.thickness
    return (
        vbar(design, left, bottom, top),
        vbar(design, right - t, bottom, top),
        hbar(design, left, right, bottom),
        hbar(design, left, right, top - t),
    )


def _midbar(design: Design, left, right, center, thickness=None):
    height = design.thickness if thickness is None else thickness
    return hbar(design, left, right, center - height // 2, height)


def _line_x(start, end, y):
    x0, y0 = start
    x1, y1 = end
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def _edge_gap(left_shape, right_shape, edge_y):
    left_edge = max(x for x, y in left_shape if y == edge_y)
    right_edge = min(x for x, y in right_shape if y == edge_y)
    return right_edge - left_edge


def _notched_pair(design: Design, edge_y, join_y, name):
    """Keep an identity notch open by moving diagonal receivers outward."""
    left, center, right = design.ink_left, design.advance / 2, design.ink_right

    def pair(inset):
        left_shape = diagonal(design, (left + inset, edge_y), (center, join_y))
        right_shape = diagonal(design, (right - inset, edge_y), (center, join_y))
        return (
            tuple((max(x, left), y) for x, y in left_shape),
            tuple((min(x, right), y) for x, y in right_shape),
        )

    shapes = pair(design.thickness)
    natural = _edge_gap(*shapes, edge_y)
    if natural < TAPERED_NOTCH_MINIMUM:
        for inset in range(design.thickness - 1, 0, -1):
            shapes = pair(inset)
            if _edge_gap(*shapes, edge_y) >= TAPERED_NOTCH_MINIMUM:
                break
        else:
            raise ValueError(f"{name}: cannot preserve the notch")
    resolved = _edge_gap(*shapes, edge_y)
    return (
        *shapes,
        gap_rule(
            design,
            name,
            natural,
            "widen",
            resolved,
            minimum=TAPERED_NOTCH_MINIMUM,
        ),
    )


def pilot_glyphs(design: Design):
    """Resolve the shared recipes at one weight."""
    t = design.thickness
    left, center, right = design.x("ink_left"), design.x("center"), design.x("ink_right")
    diagonal_left, diagonal_right = design.x("diagonal_left"), design.x("diagonal_right")
    baseline, x_mid = design.y("baseline"), design.y("x_mid")
    mid, x_height, cap = design.y("midline"), design.y("x_height"), design.y("cap_height")
    descender = design.y("descender")
    upper_bowl_right = design.x("upper_bowl_right")

    cap_frame = _frame(design, left, baseline, right, cap)
    x_frame = _frame(design, left, baseline, right, x_height)
    center_stem = center - t // 2

    mid_bottom = mid - t // 2
    mid_top = mid_bottom + t
    upper_b_counter = min(
        upper_bowl_right - left - 2 * t,
        cap - t - mid_top,
    )
    b_gap = gap_rule(design, "counters", upper_b_counter, "widen", upper_b_counter)

    a_left = diagonal(design, (diagonal_left, baseline), (center, cap))
    a_right = diagonal(design, (diagonal_right, baseline), (center, cap))
    a_natural = max(
        0,
        _line_x(a_right[0], a_right[3], mid_top)
        - _line_x(a_left[1], a_left[2], mid_top),
    )
    a_gap = gap_rule(design, "counter", a_natural, "widen", max(a_natural, design.minimum_gap))
    a_patch = () if a_gap.outcome == "preserve" or not a_natural else (
        rectangle(center - a_natural / 2, mid_top, center + a_natural / 2, cap),
    )
    a_cuts = () if a_gap.outcome == "preserve" else (
        rectangle(
            center - a_gap.resolved / 2,
            mid_top,
            center + a_gap.resolved / 2,
            cap - t,
        ),
    )

    natural_x_gaps = (x_height - 3 * t) / 2
    detail_t = t if natural_x_gaps >= design.minimum_gap else (
        x_height - 2 * design.minimum_gap
    ) // 3
    resolved_x_gaps = (x_height - 3 * detail_t) / 2
    a_bar_gap = gap_rule(design, "horizontal spaces", natural_x_gaps, "widen", resolved_x_gaps)
    e_bar_gap = gap_rule(design, "horizontal spaces", natural_x_gaps, "widen", resolved_x_gaps)

    m_left, m_right, m_gap = _notched_pair(design, x_height, x_mid, "center notch")
    cap_m_left, cap_m_right, cap_m_gap = _notched_pair(
        design, cap, design.y("m_join"), "center notch"
    )
    w_left, w_right, w_gap = _notched_pair(design, baseline, mid, "center notch")

    n_diagonal = diagonal(design, (left + t, cap), (right - t, baseline))
    n_clearance = min(
        (right - t) - max(x for x, y in n_diagonal if y == cap),
        min(x for x, y in n_diagonal if y == baseline) - (left + t),
    )
    n_gap = gap_rule(design, "diagonal windows", n_clearance, "widen", n_clearance)

    def zero_clearance(shape):
        upper = _line_x(shape[0], shape[3], cap - t) - (left + t)
        lower = (right - t) - _line_x(shape[1], shape[2], baseline + t)
        return min(upper, lower)

    slash = diagonal(
        design,
        (left + t, baseline + t / 2),
        (right - t, cap - t / 2),
    )
    zero_natural = zero_clearance(slash)
    zero_gap = gap_rule(design, "slash windows", zero_natural, "widen", zero_natural)

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
            gaps=(b_gap,),
        ),
        "S": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, left, mid, cap),
            _midbar(design, left, right, mid),
            vbar(design, right - t, baseline, mid),
            hbar(design, left, right, baseline),
        ),
        "A": glyph(
            a_left,
            a_right,
            *a_patch,
            _midbar(design, left, right, mid),
            cuts=a_cuts,
            gaps=(a_gap,),
        ),
        "N": glyph(
            vbar(design, left, baseline, cap),
            n_diagonal,
            vbar(design, right - t, baseline, cap),
            gaps=(n_gap,),
        ),
        "M": glyph(
            vbar(design, left, baseline, cap),
            cap_m_left,
            cap_m_right,
            vbar(design, right - t, baseline, cap),
            gaps=(cap_m_gap,),
        ),
        "V": glyph(
            diagonal(design, (diagonal_left, cap), (center, baseline)),
            diagonal(design, (diagonal_right, cap), (center, baseline)),
        ),
        "W": glyph(
            vbar(design, left, baseline, cap),
            w_left,
            w_right,
            vbar(design, right - t, baseline, cap),
            gaps=(w_gap,),
        ),
        "X": glyph(
            diagonal(design, (diagonal_left, baseline), (diagonal_right, cap)),
            diagonal(design, (diagonal_right, baseline), (diagonal_left, cap)),
        ),
        "Z": glyph(
            hbar(design, left, right, cap - t),
            joined_descending_diagonal(design, baseline + t, cap - t),
            hbar(design, left, right, baseline),
        ),
        "a": glyph(
            hbar(design, left, right, x_height - detail_t, detail_t),
            vbar(design, right - t, baseline, x_height),
            _midbar(design, left, right, x_mid, detail_t),
            vbar(design, left, baseline, x_mid),
            hbar(design, left, right, baseline, detail_t),
            gaps=(a_bar_gap,),
        ),
        "e": glyph(
            vbar(design, left, baseline, x_height),
            hbar(design, left, right, x_height - detail_t, detail_t),
            _midbar(design, left, right, x_mid, detail_t),
            hbar(design, left, right, baseline, detail_t),
            gaps=(e_bar_gap,),
        ),
        "g": glyph(
            *x_frame,
            vbar(design, right - t, descender, x_height),
            hbar(design, left, right, descender),
        ),
        "m": glyph(
            vbar(design, left, baseline, x_height),
            m_left,
            m_right,
            vbar(design, right - t, baseline, x_height),
            gaps=(m_gap,),
        ),
        "n": glyph(
            vbar(design, left, baseline, x_height),
            hbar(design, left, right, x_height - t),
            vbar(design, right - t, baseline, x_height),
        ),
        "r": glyph(
            vbar(design, left, baseline, x_height),
            hbar(design, left, design.x("shoulder_right"), x_height - t),
            vbar(
                design,
                design.x("shoulder_right") - t,
                design.y("r_join"),
                x_height,
            ),
        ),
        "I": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, center_stem, baseline, cap),
            hbar(design, left, right, baseline),
        ),
        "l": glyph(
            vbar(design, design.x("lowercase_stem"), baseline, cap),
            hbar(
                design,
                design.x("lowercase_stem"),
                design.x("lowercase_foot"),
                baseline,
            ),
        ),
        "0": glyph(
            *cap_frame,
            slash,
            gaps=(zero_gap,),
        ),
        "1": glyph(
            diagonal(design, design.point("one_flag", "one_flag"), (center, cap)),
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
    _design = Design(thickness=_weight)
    _pilot = pilot_glyphs(_design)
    assert all(
        0 <= x <= _design.advance
        for blueprint in _pilot.values()
        for contour in blueprint["ink"]
        for x, _ in contour
    )
