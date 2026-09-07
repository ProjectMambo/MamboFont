"""Direct filled-polygon recipes for printable ASCII."""

from __future__ import annotations

from sources.model import (
    Design,
    diagonal,
    gap_rule,
    glyph,
    hbar,
    joined_descending_diagonal,
    polygon,
    rectangle,
    validate_blueprint,
    vbar,
)


ASCII_CHARACTERS = "".join(map(chr, range(0x21, 0x7F)))


def _frame(design: Design, left, bottom, right, top, thickness=None):
    """A square frame made from inward-growing exterior surfaces."""
    t = design.thickness if thickness is None else thickness
    return (
        vbar(design, left, bottom, top, t),
        vbar(design, right - t, bottom, top, t),
        hbar(design, left, right, bottom, t),
        hbar(design, left, right, top - t, t),
    )


def _c_frame(design: Design, left, bottom, right, top, thickness=None):
    t = design.thickness if thickness is None else thickness
    return (
        vbar(design, left, bottom, top, t),
        hbar(design, left, right, bottom, t),
        hbar(design, left, right, top - t, t),
    )


def _midbar(design: Design, left, right, center, thickness=None):
    height = design.thickness if thickness is None else thickness
    return hbar(design, left, right, center - height / 2, height)


def _square(center_x, center_y, size):
    half = size / 2
    return rectangle(center_x - half, center_y - half, center_x + half, center_y + half)


def _mirror(design: Design, contours):
    return tuple(tuple((design.advance - x, y) for x, y in contour) for contour in contours)


def _clamp_x(contour, left, right):
    return tuple((max(left, min(x, right)), y) for x, y in contour)


def _line_x(start, end, y):
    x0, y0 = start
    x1, y1 = end
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def _edge_gap(left_shape, right_shape, edge_y):
    left_edge = max(x for x, y in left_shape if y == edge_y)
    right_edge = min(x for x, y in right_shape if y == edge_y)
    return right_edge - left_edge


def _notched_pair(design: Design, edge_y, join_y, name):
    """Use nominal diagonals, filling only a too-small tapered notch."""
    left, center, right = design.ink_left, design.advance / 2, design.ink_right
    left_shape = diagonal(design, (left + design.thickness, edge_y), (center, join_y))
    right_shape = diagonal(design, (right - design.thickness, edge_y), (center, join_y))
    natural = _edge_gap(left_shape, right_shape, edge_y)
    resolved = natural if natural >= design.minimum_gap else 0
    rule = gap_rule(design, name, natural, "fill", resolved)
    patch = ()
    if rule.outcome == "fill" and natural:
        left_edge = max(x for x, y in left_shape if y == edge_y)
        right_edge = min(x for x, y in right_shape if y == edge_y)
        patch = (polygon((left_edge, edge_y), (right_edge, edge_y), (center, join_y)),)
    return left_shape, right_shape, patch, rule


def ascii_glyphs(design: Design):
    """Resolve every printable-ASCII recipe at one weight."""
    t = design.thickness
    left, center, right = design.x("ink_left"), design.x("center"), design.x("ink_right")
    diagonal_left, diagonal_right = design.x("diagonal_left"), design.x("diagonal_right")
    baseline, x_mid = design.y("baseline"), design.y("x_mid")
    mid, x_height, cap = design.y("midline"), design.y("x_height"), design.y("cap_height")
    upper_bowl_right = design.x("upper_bowl_right")
    center_stem = center - t / 2
    detail = (2 * t + 1) // 3
    grid_detail = min(t, 90)
    at_detail = (t + 1) // 2

    cap_frame = _frame(design, left, baseline, right, cap)
    x_frame = _frame(design, left, baseline, right, x_height)
    cap_c = _c_frame(design, left, baseline, right, cap)
    x_c = _c_frame(design, left, baseline, right, x_height)

    mid_bottom = mid - t / 2
    mid_top = mid_bottom + t
    upper_b_counter = min(upper_bowl_right - left - 2 * t, cap - t - mid_top)
    b_gap = gap_rule(design, "counters", upper_b_counter, "widen", upper_b_counter)

    a_left = diagonal(design, (diagonal_left, baseline), (center, cap))
    a_right = diagonal(design, (diagonal_right, baseline), (center, cap))
    a_inner_left = _line_x(a_left[1], a_left[2], mid_top)
    a_inner_right = _line_x(a_right[0], a_right[3], mid_top)
    a_natural = max(0, a_inner_right - a_inner_left)
    a_gap = gap_rule(
        design,
        "upper counter",
        a_natural,
        "fill",
        a_natural if a_natural >= design.minimum_gap else 0,
    )
    a_fill = () if a_gap.outcome == "preserve" or not a_natural else (
        polygon((a_inner_left, mid_top), (a_inner_right, mid_top), (center, cap)),
    )

    natural_x_gaps = (x_height - 3 * t) / 2
    horizontal_detail = t if natural_x_gaps >= design.minimum_gap else (
        x_height - 2 * design.minimum_gap
    ) / 3
    resolved_x_gaps = (x_height - 3 * horizontal_detail) / 2
    a_bar_gap = gap_rule(design, "horizontal spaces", natural_x_gaps, "widen", resolved_x_gaps)
    e_bar_gap = gap_rule(design, "horizontal spaces", natural_x_gaps, "widen", resolved_x_gaps)
    s_bar_gap = gap_rule(design, "horizontal spaces", natural_x_gaps, "widen", resolved_x_gaps)

    m_left, m_right, m_fill, m_gap = _notched_pair(design, x_height, x_mid, "center notch")
    cap_m_left, cap_m_right, cap_m_fill, cap_m_gap = _notched_pair(
        design, cap, design.y("m_join"), "center notch"
    )
    w_left, w_right, w_fill, w_gap = _notched_pair(design, baseline, mid, "center notch")
    small_w_left, small_w_right, small_w_fill, small_w_gap = _notched_pair(
        design, baseline, x_mid, "center notch"
    )

    n_diagonal = diagonal(design, (left + t, cap), (right - t, baseline))
    n_clearance = min(
        (right - t) - max(x for x, y in n_diagonal if y == cap),
        min(x for x, y in n_diagonal if y == baseline) - (left + t),
    )
    n_gap = gap_rule(design, "diagonal windows", n_clearance, "widen", n_clearance)

    slash = diagonal(design, (left + t, baseline + t / 2), (right - t, cap - t / 2))
    zero_clearance = min(
        _line_x(slash[0], slash[3], cap - t) - (left + t),
        (right - t) - _line_x(slash[1], slash[2], baseline + t),
    )
    zero_gap = gap_rule(design, "slash windows", zero_clearance, "widen", zero_clearance)

    tail_bottom = -design.descent
    tail_natural = design.descent - t
    tail_thickness = min(t, design.descent - design.minimum_gap)
    tail_resolved = design.descent - tail_thickness

    def tail_gap():
        return gap_rule(design, "tail aperture", tail_natural, "widen", tail_resolved)

    flag = list(diagonal(design, design.point("one_flag", "one_flag"), (center, cap)))
    flag[1] = (center_stem, flag[1][1])
    flag[2] = (center_stem + t, flag[2][1])
    flag[3] = (center_stem, flag[3][1])
    flag = tuple(flag)

    s_parts = (
        hbar(design, left, right, cap - t),
        vbar(design, left, mid, cap),
        _midbar(design, left, right, mid),
        vbar(design, right - t, baseline, mid),
        hbar(design, left, right, baseline),
    )
    small_s_parts = (
        hbar(design, left, right, x_height - horizontal_detail, horizontal_detail),
        vbar(design, left, x_mid, x_height),
        _midbar(design, left, right, x_mid, horizontal_detail),
        vbar(design, right - t, baseline, x_mid),
        hbar(design, left, right, baseline, horizontal_detail),
    )

    recipes = {
        "A": glyph(a_left, a_right, *a_fill, _midbar(design, left, right, mid), gaps=(a_gap,)),
        "B": glyph(
            vbar(design, left, baseline, cap),
            hbar(design, left, upper_bowl_right, cap - t),
            vbar(design, upper_bowl_right - t, mid, cap),
            _midbar(design, left, right, mid),
            vbar(design, right - t, baseline, mid),
            hbar(design, left, right, baseline),
            gaps=(b_gap,),
        ),
        "C": glyph(*cap_c),
        "D": glyph(
            vbar(design, left, baseline, cap),
            hbar(design, left, center + 100, cap - t),
            diagonal(design, (right - t, mid), (center + 80, cap)),
            vbar(design, right - t, baseline, mid + t),
            hbar(design, left, right, baseline),
        ),
        "E": glyph(*cap_c, _midbar(design, left, right, mid)),
        "F": glyph(
            vbar(design, left, baseline, cap),
            hbar(design, left, right, cap - t),
            _midbar(design, left, right - t / 2, mid),
        ),
        "G": glyph(
            *cap_c,
            _midbar(design, center, right, mid),
            vbar(design, right - t, baseline, mid + t / 2),
        ),
        "H": glyph(
            vbar(design, left, baseline, cap),
            vbar(design, right - t, baseline, cap),
            _midbar(design, left, right, mid),
        ),
        "I": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, center_stem, baseline, cap),
            hbar(design, left, right, baseline),
        ),
        "J": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, right - t, baseline, cap),
            hbar(design, left, right, baseline),
            vbar(design, left, baseline, baseline + 2 * t),
        ),
        "K": glyph(
            vbar(design, left, baseline, cap),
            _clamp_x(diagonal(design, (left + t / 2, mid), (diagonal_right, cap)), left, right),
            _clamp_x(diagonal(design, (diagonal_right, baseline), (left + t / 2, mid)), left, right),
        ),
        "L": glyph(vbar(design, left, baseline, cap), hbar(design, left, right, baseline)),
        "M": glyph(
            vbar(design, left, baseline, cap), cap_m_left, cap_m_right, *cap_m_fill,
            vbar(design, right - t, baseline, cap), gaps=(cap_m_gap,),
        ),
        "N": glyph(
            vbar(design, left, baseline, cap), n_diagonal,
            vbar(design, right - t, baseline, cap), gaps=(n_gap,),
        ),
        "O": glyph(*cap_frame),
        "P": glyph(
            vbar(design, left, baseline, cap),
            hbar(design, left, right, cap - t),
            vbar(design, right - t, mid, cap),
            _midbar(design, left, right, mid),
        ),
        "Q": glyph(*cap_frame, diagonal(design, (center + 10, mid / 2), (right - 80, -120))),
        "R": glyph(
            vbar(design, left, baseline, cap),
            hbar(design, left, right, cap - t),
            vbar(design, right - t, mid, cap),
            _midbar(design, left, right, mid),
            diagonal(design, (center + 20, mid), (diagonal_right, baseline)),
        ),
        "S": glyph(*s_parts),
        "T": glyph(hbar(design, left, right, cap - t), vbar(design, center_stem, baseline, cap)),
        "U": glyph(
            vbar(design, left, baseline, cap),
            vbar(design, right - t, baseline, cap),
            hbar(design, left, right, baseline),
        ),
        "V": glyph(
            diagonal(design, (diagonal_left, cap), (center, baseline)),
            diagonal(design, (diagonal_right, cap), (center, baseline)),
        ),
        "W": glyph(
            vbar(design, left, baseline, cap), w_left, w_right, *w_fill,
            vbar(design, right - t, baseline, cap), gaps=(w_gap,),
        ),
        "X": glyph(
            diagonal(design, (diagonal_left, baseline), (diagonal_right, cap)),
            diagonal(design, (diagonal_right, baseline), (diagonal_left, cap)),
        ),
        "Y": glyph(
            vbar(design, left, mid, cap),
            vbar(design, right - t, mid, cap),
            _midbar(design, left, right, mid),
            vbar(design, center_stem, baseline, mid),
        ),
        "Z": glyph(
            hbar(design, left, right, cap - t),
            joined_descending_diagonal(design, baseline + t, cap - t),
            hbar(design, left, right, baseline),
        ),
        "a": glyph(
            hbar(design, left, right, x_height - horizontal_detail, horizontal_detail),
            vbar(design, right - t, baseline, x_height),
            _midbar(design, left, right, x_mid, horizontal_detail),
            vbar(design, left, baseline, x_mid),
            hbar(design, left, right, baseline, horizontal_detail),
            gaps=(a_bar_gap,),
        ),
        "b": glyph(*x_frame, vbar(design, left, baseline, cap)),
        "c": glyph(*x_c),
        "d": glyph(*x_frame, vbar(design, right - t, baseline, cap)),
        "e": glyph(
            vbar(design, left, baseline, x_height),
            hbar(design, left, right, x_height - horizontal_detail, horizontal_detail),
            _midbar(design, left, right, x_mid, horizontal_detail),
            hbar(design, left, right, baseline, horizontal_detail),
            gaps=(e_bar_gap,),
        ),
        "f": glyph(
            vbar(design, center_stem, baseline, cap),
            hbar(design, center, right, cap - t),
            _midbar(design, left, right, x_height),
        ),
        "g": glyph(
            *x_frame,
            vbar(design, right - t, tail_bottom, x_height),
            hbar(design, left, right, tail_bottom, tail_thickness),
            gaps=(tail_gap(),),
        ),
        "h": glyph(
            vbar(design, left, baseline, cap),
            hbar(design, left, right, x_height - t),
            vbar(design, right - t, baseline, x_height),
        ),
        "i": glyph(
            vbar(design, center_stem, baseline, x_height - detail - design.minimum_gap),
            _square(center, x_height - detail / 2, detail),
        ),
        "j": glyph(
            vbar(
                design,
                right - t,
                tail_bottom,
                x_height - detail - design.minimum_gap,
            ),
            hbar(design, left, right, tail_bottom, tail_thickness),
            vbar(design, left, tail_bottom, tail_bottom + 2 * tail_thickness),
            _square(right - t / 2, x_height - detail / 2, detail),
            gaps=(tail_gap(),),
        ),
        "k": glyph(
            vbar(design, left, baseline, cap),
            _clamp_x(diagonal(design, (left + t / 2, x_mid), (diagonal_right, x_height)), left, right),
            _clamp_x(diagonal(design, (diagonal_right, baseline), (left + t / 2, x_mid)), left, right),
        ),
        "l": glyph(
            vbar(design, design.x("lowercase_stem"), baseline, cap),
            hbar(design, design.x("lowercase_stem"), design.x("lowercase_foot"), baseline),
        ),
        "m": glyph(
            vbar(design, left, baseline, x_height), m_left, m_right, *m_fill,
            vbar(design, right - t, baseline, x_height), gaps=(m_gap,),
        ),
        "n": glyph(
            vbar(design, left, baseline, x_height),
            hbar(design, left, right, x_height - t),
            vbar(design, right - t, baseline, x_height),
        ),
        "o": glyph(*x_frame),
        "p": glyph(*x_frame, vbar(design, left, tail_bottom, x_height)),
        "q": glyph(
            *x_frame,
            vbar(design, right - t, tail_bottom, x_height),
            hbar(design, center, right, tail_bottom, tail_thickness),
        ),
        "r": glyph(
            vbar(design, left, baseline, x_height),
            hbar(design, left, design.x("shoulder_right"), x_height - t),
            vbar(design, design.x("shoulder_right") - t, design.y("r_join"), x_height),
        ),
        "s": glyph(*small_s_parts, gaps=(s_bar_gap,)),
        "t": glyph(
            vbar(design, center_stem, baseline, design.y("one_flag")),
            _midbar(design, left, right, x_height),
        ),
        "u": glyph(
            vbar(design, left, baseline, x_height),
            vbar(design, right - t, baseline, x_height),
            hbar(design, left, right, baseline),
        ),
        "v": glyph(
            diagonal(design, (diagonal_left, x_height), (center, baseline)),
            diagonal(design, (diagonal_right, x_height), (center, baseline)),
        ),
        "w": glyph(
            vbar(design, left, baseline, x_height),
            small_w_left, small_w_right, *small_w_fill,
            vbar(design, right - t, baseline, x_height),
            gaps=(small_w_gap,),
        ),
        "x": glyph(
            diagonal(design, (diagonal_left, baseline), (diagonal_right, x_height)),
            diagonal(design, (diagonal_right, baseline), (diagonal_left, x_height)),
        ),
        "y": glyph(
            vbar(design, left, baseline, x_height),
            vbar(design, right - t, tail_bottom, x_height),
            hbar(design, left, right, baseline),
            hbar(design, left, right, tail_bottom, tail_thickness),
            gaps=(tail_gap(),),
        ),
        "z": glyph(
            hbar(design, left, right, x_height - t),
            joined_descending_diagonal(design, baseline + t, x_height - t),
            hbar(design, left, right, baseline),
        ),
        "0": glyph(*cap_frame, slash, gaps=(zero_gap,)),
        "1": glyph(flag, vbar(design, center_stem, baseline, cap), hbar(design, left, right, baseline)),
        "2": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, right - t, x_height, cap),
            joined_descending_diagonal(design, baseline + t, x_height, upper_stem=True),
            hbar(design, left, right, baseline),
        ),
        "3": glyph(
            vbar(design, right - t, baseline, cap),
            hbar(design, left, right, cap - t),
            _midbar(design, left, right, mid),
            hbar(design, left, right, baseline),
        ),
        "4": glyph(
            vbar(design, left, mid, cap),
            _midbar(design, left, right, mid),
            vbar(design, right - t, baseline, cap),
        ),
        "5": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, left, mid, cap),
            _midbar(design, left, right, mid),
            _clamp_x(diagonal(design, (center, baseline + t), (diagonal_right, mid)), left, right),
            hbar(design, left, center + t / 2, baseline),
        ),
        "6": glyph(
            vbar(design, left, baseline, cap),
            hbar(design, left, right, cap - t),
            _midbar(design, left, right, mid),
            vbar(design, right - t, baseline, mid),
            hbar(design, left, right, baseline),
        ),
        "7": glyph(
            hbar(design, left, right, cap - t),
            _clamp_x(
                diagonal(design, (center - t / 2, baseline), (diagonal_right, cap - t / 2)),
                left,
                right,
            ),
        ),
        "8": glyph(*cap_frame, _midbar(design, left, right, mid)),
        "9": glyph(
            hbar(design, left, right, cap - t),
            vbar(design, left, mid, cap),
            _midbar(design, left, right, mid),
            vbar(design, right - t, baseline, cap),
            hbar(design, left, right, baseline),
        ),
    }

    paren = (
        hbar(design, center, right - 60, cap - detail, detail),
        vbar(design, center - detail, cap - 2 * detail, cap, detail),
        hbar(design, left + 90, center, cap - 2 * detail, detail),
        vbar(design, left + 90, 2 * detail, cap - detail, detail),
        hbar(design, left + 90, center, detail, detail),
        vbar(design, center - detail, baseline, 2 * detail, detail),
        hbar(design, center, right - 60, baseline, detail),
    )
    bracket = (
        vbar(design, left + 100, baseline, cap, detail),
        hbar(design, left + 100, right - 70, cap - detail, detail),
        hbar(design, left + 100, right - 70, baseline, detail),
    )
    brace = (
        hbar(design, center, right - 50, cap - detail, detail),
        vbar(design, center - detail, mid + detail, cap, detail),
        hbar(design, left + 100, center, mid, detail),
        vbar(design, left + 100, mid - detail, mid + detail, detail),
        hbar(design, left + 100, center, mid - detail, detail),
        vbar(design, center - detail, baseline, mid - detail, detail),
        hbar(design, center, right - 50, baseline, detail),
    )
    quote_y = cap - 2 * detail
    comma = polygon(
        (center - detail, -detail),
        (center - detail / 2, baseline),
        (center - detail / 2, detail),
        (center + detail / 2, detail),
        (center + detail / 2, baseline),
        (center, -detail),
    )
    question_diagonal = list(
        diagonal(design, (center, mid), (right - detail / 2, 450), detail)
    )
    question_diagonal[0] = (center - detail / 2, question_diagonal[0][1])
    question_diagonal[1] = (center + detail / 2, question_diagonal[1][1])
    question_diagonal[2] = (right, question_diagonal[2][1])
    question_diagonal[3] = (right - detail, question_diagonal[3][1])
    question_diagonal = tuple(question_diagonal)
    punctuation = {
        "!": glyph(
            vbar(design, center_stem, detail + design.minimum_gap, cap),
            _square(center, detail / 2, detail),
        ),
        '"': glyph(
            vbar(design, left + 90, quote_y, cap, detail),
            vbar(design, right - 90 - detail, quote_y, cap, detail),
        ),
        "#": glyph(
            vbar(design, left + 80, baseline, cap, grid_detail),
            vbar(design, right - 80 - grid_detail, baseline, cap, grid_detail),
            hbar(design, left, right, 180, grid_detail),
            hbar(design, left, right, 370, grid_detail),
        ),
        "$": glyph(
            *s_parts,
            vbar(design, center - detail / 2, cap, cap + detail, detail),
            vbar(design, center - detail / 2, -detail, baseline, detail),
        ),
        "%": glyph(
            diagonal(design, (diagonal_left, baseline), (diagonal_right, cap), detail),
            _square(left + 70, cap - 100, detail),
            _square(right - 70, 100, detail),
        ),
        "&": glyph(
            *_frame(design, left + 50, baseline, right - 50, cap, detail),
            _midbar(design, left + 50, right - 50, mid, detail),
            diagonal(design, (center - 40, mid), (diagonal_right, baseline), detail),
        ),
        "'": glyph(vbar(design, center - detail / 2, quote_y, cap, detail)),
        "(": glyph(*paren),
        ")": glyph(*_mirror(design, paren)),
        "*": glyph(
            vbar(design, center - detail / 2, 170, 500, detail),
            diagonal(design, (left + 80, 230), (right - 80, 450), detail),
            diagonal(design, (right - 80, 230), (left + 80, 450), detail),
        ),
        "+": glyph(vbar(design, center_stem, 120, 520), _midbar(design, left, right, mid)),
        ",": glyph(comma),
        "-": glyph(_midbar(design, left + 80, right - 80, mid, detail)),
        ".": glyph(_square(center, detail / 2, detail)),
        "/": glyph(diagonal(design, (diagonal_left, baseline), (diagonal_right, cap))),
        ":": glyph(_square(center, 80, detail), _square(center, x_height - 40, detail)),
        ";": glyph(
            _square(center, x_height - 40, detail),
            comma,
        ),
        "<": glyph(
            diagonal(design, (left + 70, mid), (right - 70, 560)),
            diagonal(design, (right - 70, 80), (left + 70, mid)),
        ),
        "=": glyph(
            hbar(design, left + 40, right - 40, 200, detail),
            hbar(design, left + 40, right - 40, 360, detail),
        ),
        ">": glyph(
            diagonal(design, (right - 70, mid), (left + 70, 560)),
            diagonal(design, (left + 70, 80), (right - 70, mid)),
        ),
        "?": glyph(
            hbar(design, left, right, cap - detail, detail),
            vbar(design, right - detail, 450, cap, detail),
            question_diagonal,
            vbar(
                design,
                center - detail / 2,
                detail + design.minimum_gap,
                mid + detail / 2,
                detail,
            ),
            _square(center, detail / 2, detail),
        ),
        "@": glyph(
            *_c_frame(design, left, baseline, right, cap, at_detail),
            *_frame(design, 180, 160, 380, 480, at_detail),
            hbar(design, 320, right, 160, at_detail),
        ),
        "[": glyph(*bracket),
        "\\": glyph(diagonal(design, (diagonal_left, cap), (diagonal_right, baseline))),
        "]": glyph(*_mirror(design, bracket)),
        "^": glyph(
            diagonal(design, (left + 80, x_height), (center, cap), detail),
            diagonal(design, (right - 80, x_height), (center, cap), detail),
        ),
        "_": glyph(hbar(design, left, right, -detail, detail)),
        "`": glyph(diagonal(design, (center - 100, cap), (center + 20, quote_y), detail)),
        "{": glyph(*brace),
        "|": glyph(vbar(design, center - detail / 2, -80, design.y("accent_height"), detail)),
        "}": glyph(*_mirror(design, brace)),
        "~": glyph(polygon(
            (left + 50, 340), (center - 40, 340), (center - 40, 300),
            (center + 40, 300), (center + 40, 340), (right - 50, 340),
            (right - 50, 260), (center + 40, 260), (center + 40, 220),
            (center - 40, 220), (center - 40, 260), (left + 50, 260),
        )),
    }
    recipes.update(punctuation)

    if set(recipes) != set(ASCII_CHARACTERS):
        missing = set(ASCII_CHARACTERS) - set(recipes)
        extra = set(recipes) - set(ASCII_CHARACTERS)
        raise AssertionError(f"ASCII recipe mismatch; missing={missing}, extra={extra}")
    for blueprint in recipes.values():
        validate_blueprint(blueprint)
    return recipes


for _weight in (80, 93, 107, 120):
    _design = Design(thickness=_weight)
    _ascii = ascii_glyphs(_design)
    for _char, _blueprint in _ascii.items():
        for _contour in (*_blueprint["ink"], *_blueprint["cuts"]):
            for _x, _y in _contour:
                assert 0 <= _x <= _design.advance and -_design.descent <= _y <= _design.ascent, (
                    _weight, _char, _x, _y
                )
