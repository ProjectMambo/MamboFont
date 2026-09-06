"""Deterministic source geometry for Mambo Font.

Glyphs are straight centre-line paths.  The build script expands the same
paths at four stroke widths, which keeps the family related without keeping
four drawings in sync.
"""

from unicodedata import normalize

from sources.geometry import combine, glyph, loop, path, transform


L, R, C = 105, 395, 250
CAP, XH, MID, XMID, DESC = 640, 440, 320, 220, -140


def ring(left=L, right=R, bottom=0, top=CAP, cut=45):
    return loop(
        (left + cut, bottom),
        (right - cut, bottom),
        (right, bottom + cut),
        (right, top - cut),
        (right - cut, top),
        (left + cut, top),
        (left, top - cut),
        (left, bottom + cut),
    )


def c_shape(left=L, right=R, bottom=0, top=CAP, cut=45):
    return path(
        (right, top - cut),
        (right - cut, top),
        (left + cut, top),
        (left, top - cut),
        (left, bottom + cut),
        (left + cut, bottom),
        (right - cut, bottom),
        (right, bottom + cut),
    )


def bowl(left=L, right=R, bottom=0, top=XH, cut=35):
    return ring(left, right, bottom, top, cut)


# Base ASCII.  Repeated structures are intentional visual grammar, not copied
# outlines: changing a global metric or weight updates every instance.
GLYPHS = {
    " ": glyph(),
    "A": glyph(path((80, 0), (190, CAP), (310, CAP), (420, 0)), path((135, MID), (365, MID))),
    "B": glyph(
        path((L, 0), (L, CAP)),
        path((L, CAP), (345, CAP), (R, 595), (R, 365), (345, MID), (L, MID)),
        path((L, MID), (345, MID), (R, 275), (R, 45), (345, 0), (L, 0)),
    ),
    "C": glyph(c_shape()),
    "D": glyph(path((L, 0), (L, CAP)), path((L, CAP), (345, CAP), (R, 590), (R, 50), (345, 0), (L, 0))),
    "E": glyph(path((L, 0), (L, CAP)), path((L, CAP), (R, CAP)), path((L, MID), (350, MID)), path((L, 0), (R, 0))),
    "F": glyph(path((L, 0), (L, CAP)), path((L, CAP), (R, CAP)), path((L, MID), (350, MID))),
    "G": glyph(c_shape(), path((R, 260), (300, 260)), path((R, 260), (R, 0))),
    "H": glyph(path((L, 0), (L, CAP)), path((R, 0), (R, CAP)), path((L, MID), (R, MID))),
    "I": glyph(path((L, CAP), (R, CAP)), path((C, 0), (C, CAP)), path((L, 0), (R, 0))),
    "J": glyph(path((L, CAP), (R, CAP)), path((R, CAP), (R, 55), (350, 0), (155, 0), (L, 50), (L, 140))),
    "K": glyph(path((L, 0), (L, CAP)), path((R, CAP), (L, MID), (R, 0))),
    "L": glyph(path((L, CAP), (L, 0), (R, 0))),
    "M": glyph(path((L, 0), (L, CAP), (C, 330), (R, CAP), (R, 0))),
    "N": glyph(path((L, 0), (L, CAP), (R, 0), (R, CAP))),
    "O": glyph(ring()),
    "P": glyph(path((L, 0), (L, CAP)), path((L, CAP), (345, CAP), (R, 595), (R, 365), (345, MID), (L, MID))),
    "Q": glyph(ring(), path((285, 150), (420, -35))),
    "R": glyph(
        path((L, 0), (L, CAP)),
        path((L, CAP), (345, CAP), (R, 595), (R, 365), (345, MID), (L, MID)),
        path((290, MID), (410, 0)),
    ),
    "S": glyph(path((R, 590), (350, CAP), (150, CAP), (L, 590), (L, 370), (150, MID), (350, MID), (R, 270), (R, 50), (350, 0), (150, 0), (L, 50))),
    "T": glyph(path((70, CAP), (430, CAP)), path((C, CAP), (C, 0))),
    "U": glyph(path((L, CAP), (L, 50), (155, 0), (345, 0), (R, 50), (R, CAP))),
    "V": glyph(path((75, CAP), (205, 0), (295, 0), (425, CAP))),
    "W": glyph(path((65, CAP), (130, 0), (250, 260), (370, 0), (435, CAP))),
    "X": glyph(path((85, CAP), (415, 0)), path((415, CAP), (85, 0))),
    "Y": glyph(path((75, CAP), (C, MID), (425, CAP)), path((C, MID), (C, 0))),
    "Z": glyph(path((105, CAP), (395, CAP), (105, 0), (395, 0))),

    "a": glyph(bowl(top=XH), path((R, 0), (R, XH)), path((L, XMID), (R, XMID))),
    "b": glyph(path((L, 0), (L, CAP)), bowl(left=L, right=R, bottom=0, top=XH)),
    "c": glyph(c_shape(bottom=0, top=XH, cut=35)),
    "d": glyph(bowl(left=L, right=R, bottom=0, top=XH), path((R, 0), (R, CAP))),
    "e": glyph(c_shape(bottom=0, top=XH, cut=35), path((L, XMID), (R, XMID))),
    "f": glyph(path((150, 0), (150, 550), (195, CAP), (350, CAP), (R, 600)), path((70, XH), (330, XH))),
    "g": glyph(bowl(left=L, right=R, bottom=0, top=XH), path((R, XH), (R, -85), (350, DESC), (155, DESC), (L, -95))),
    "h": glyph(path((L, 0), (L, CAP)), path((L, XH), (150, XH), (R, 360), (R, 0))),
    "i": glyph(path((C, 0), (C, 330)), dots=((C, 415, 0.9),)),
    "j": glyph(path((R, 330), (R, -85), (350, DESC), (210, DESC), (165, -95)), dots=((R, 415, 0.9),)),
    "k": glyph(path((L, 0), (L, CAP)), path((R, XH), (L, XMID), (R, 0))),
    "l": glyph(path((C, CAP), (C, 45), (295, 0), (380, 0))),
    "m": glyph(path((70, 0), (70, XH), (105, XH), (180, 360), (180, 0)), path((180, 360), (250, XH), (320, 360), (320, 0)), path((320, 360), (395, XH), (430, 360), (430, 0))),
    "n": glyph(path((L, 0), (L, XH), (150, XH), (R, 360), (R, 0))),
    "o": glyph(bowl(top=XH)),
    "p": glyph(path((L, DESC), (L, XH)), bowl(left=L, right=R, bottom=0, top=XH)),
    "q": glyph(bowl(left=L, right=R, bottom=0, top=XH), path((R, XH), (R, DESC))),
    "r": glyph(path((L, 0), (L, XH), (150, XH), (R, 360), (R, 300))),
    "s": glyph(path((R, 400), (350, XH), (150, XH), (L, 400), (L, 260), (150, XMID), (350, XMID), (R, 180), (R, 40), (350, 0), (150, 0), (L, 40))),
    "t": glyph(path((C, 570), (C, 45), (295, 0), (380, 0)), path((90, XH), (360, XH))),
    "u": glyph(path((L, XH), (L, 50), (155, 0), (345, 0), (R, 50), (R, XH))),
    "v": glyph(path((85, XH), (205, 0), (295, 0), (415, XH))),
    "w": glyph(path((65, XH), (130, 0), (250, 185), (370, 0), (435, XH))),
    "x": glyph(path((90, XH), (410, 0)), path((410, XH), (90, 0))),
    "y": glyph(path((85, XH), (205, 0), (295, 0), (415, XH)), path((295, 0), (260, -90), (210, DESC), (140, DESC))),
    "z": glyph(path((90, XH), (410, XH), (90, 0), (410, 0))),

    "0": glyph(ring(), path((135, 80), (365, 560))),
    "1": glyph(path((150, 520), (C, CAP), (C, 0)), path((120, 0), (390, 0))),
    "2": glyph(path((L, 590), (155, CAP), (345, CAP), (R, 590), (R, 430), (L, 0), (R, 0))),
    "3": glyph(path((L, 590), (155, CAP), (345, CAP), (R, 590), (R, 370), (345, MID), (220, MID)), path((345, MID), (R, 270), (R, 50), (345, 0), (155, 0), (L, 50))),
    "4": glyph(path((350, 0), (350, CAP)), path((350, CAP), (80, 220), (420, 220))),
    "5": glyph(path((R, CAP), (L, CAP), (L, MID), (345, MID), (R, 275), (R, 50), (345, 0), (155, 0), (L, 50))),
    "6": glyph(path((R, 590), (345, CAP), (155, CAP), (L, 590), (L, 50), (155, 0), (345, 0), (R, 50), (R, 275), (345, MID), (L, MID))),
    "7": glyph(path((105, CAP), (395, CAP), (170, 0))),
    "8": glyph(ring(left=L, right=R, bottom=MID, top=CAP, cut=35), ring(left=L, right=R, bottom=0, top=MID, cut=35)),
    "9": glyph(path((L, 50), (155, 0), (345, 0), (R, 50), (R, 590), (345, CAP), (155, CAP), (L, 590), (L, 365), (155, MID), (R, MID))),

    "!": glyph(path((C, 220), (C, CAP)), dots=((C, 45, 1.0),)),
    '"': glyph(path((190, 500), (190, CAP)), path((310, 500), (310, CAP))),
    "#": glyph(path((175, 0), (205, CAP)), path((295, 0), (325, CAP)), path((90, 210), (410, 210)), path((90, 430), (410, 430))),
    "$": glyph(path((R, 590), (350, CAP), (150, CAP), (L, 590), (L, 370), (150, MID), (350, MID), (R, 270), (R, 50), (350, 0), (150, 0), (L, 50)), path((C, 700), (C, -60))),
    "%": glyph(ring(90, 210, 440, 620, 25), path((120, 0), (380, CAP)), ring(290, 410, 20, 200, 25)),
    "&": glyph(ring(120, 350, 310, CAP, 35), path((350, 470), (120, 60), (165, 0), (330, 0), (410, 100)), path((270, 220), (420, 0))),
    "'": glyph(path((C, 500), (C, CAP))),
    "(": glyph(path((340, CAP), (230, 540), (170, 380), (170, 260), (230, 100), (340, 0))),
    ")": glyph(path((160, CAP), (270, 540), (330, 380), (330, 260), (270, 100), (160, 0))),
    "*": glyph(path((C, 180), (C, 500)), path((110, 420), (390, 260)), path((390, 420), (110, 260))),
    "+": glyph(path((C, 120), (C, 520)), path((70, MID), (430, MID))),
    ",": glyph(path((C, 70), (C, -20), (205, -80))),
    "-": glyph(path((120, MID), (380, MID))),
    ".": glyph(dots=((C, 45, 1.0),)),
    "/": glyph(path((90, 0), (410, CAP))),
    ":": glyph(dots=((C, 105, 0.9), (C, 385, 0.9))),
    ";": glyph(path((C, 120), (C, 20), (205, -60)), dots=((C, 385, 0.9),)),
    "<": glyph(path((390, 560), (110, MID), (390, 80))),
    "=": glyph(path((100, 220), (400, 220)), path((100, 420), (400, 420))),
    ">": glyph(path((110, 560), (390, MID), (110, 80))),
    "?": glyph(path((L, 590), (155, CAP), (345, CAP), (R, 590), (R, 450), (C, MID), (C, 220)), dots=((C, 45, 1.0),)),
    "@": glyph(ring(70, 430, -20, 660, 55), ring(170, 340, 180, 460, 35), path((340, 180), (340, 460), (410, 460), (410, 130), (360, 80))),
    "[": glyph(path((340, CAP), (170, CAP), (170, 0), (340, 0))),
    "\\": glyph(path((90, CAP), (410, 0))),
    "]": glyph(path((160, CAP), (330, CAP), (330, 0), (160, 0))),
    "^": glyph(path((100, 400), (C, CAP), (400, 400))),
    "_": glyph(path((70, -50), (430, -50))),
    "`": glyph(path((C, 500), (190, CAP))),
    "{": glyph(path((350, CAP), (250, CAP), (210, 590), (210, 390), (160, MID), (210, 250), (210, 50), (250, 0), (350, 0))),
    "|": glyph(path((C, -80), (C, 700))),
    "}": glyph(path((150, CAP), (250, CAP), (290, 590), (290, 390), (340, MID), (290, 250), (290, 50), (250, 0), (150, 0))),
    "~": glyph(path((90, 260), (170, 350), (250, 290), (330, 350), (410, 260))),
}


# Internal reusable geometry for composed letters and compatibility symbols.
COMPONENTS = {
    ".dotlessi": glyph(path((C, 0), (C, 330))),
    ".grave": glyph(path((280, 0), (210, 70))),
    ".acute": glyph(path((220, 0), (290, 70))),
    ".circumflex": glyph(path((175, 0), (C, 70)), path((C, 70), (325, 0))),
    ".tilde": glyph(path((150, 10), (205, 65)), path((205, 65), (295, 15)), path((295, 15), (350, 70))),
    ".dieresis": glyph(dots=((195, 35, 0.72), (305, 35, 0.72))),
    ".ring": glyph(ring(180, 320, 0, 90, 20)),
    ".caron": glyph(path((175, 70), (C, 0)), path((C, 0), (325, 70))),
    ".cedilla": glyph(path((C, 0), (C, -65), (205, -110))),
    ".macron": glyph(path((160, 35), (340, 35))),
}


COMBINING_MARKS = {
    "\u0300": ".grave",
    "\u0301": ".acute",
    "\u0302": ".circumflex",
    "\u0303": ".tilde",
    "\u0308": ".dieresis",
    "\u030a": ".ring",
    "\u030c": ".caron",
    "\u0327": ".cedilla",
}


# Bespoke Latin letters: these share the global grid and stroke, but need
# their own joins instead of mechanically overlapping two finished glyphs.
GLYPHS.update({
    "µ": glyph(path((L, XH), (L, -120)), path((L, 50), (155, 0), (345, 0), (R, 50), (R, XH)), path((R, 50), (430, -100))),
    "Æ": combine(transform(GLYPHS["A"], 0.72, 1, 5, 0), transform(GLYPHS["E"], 0.68, 1, 165, 0)),
    "Ð": combine(GLYPHS["D"], glyph(path((55, MID), (265, MID)))),
    "Ø": combine(GLYPHS["O"], glyph(path((75, -25), (425, 665)))),
    "Þ": glyph(path((L, 0), (L, CAP)), path((L, 520), (345, 520), (R, 475), (R, 255), (345, 210), (L, 210))),
    "ß": glyph(path((L, 0), (L, 540), (155, CAP), (320, CAP), (R, 570), (R, 390), (320, 330), (240, 330)), path((240, 330), (350, 300), (R, 240), (R, 50), (345, 0), (250, 0))),
    "æ": combine(transform(GLYPHS["a"], 0.72, 1, -10, 0), transform(GLYPHS["e"], 0.68, 1, 165, 0)),
    "ð": combine(GLYPHS["o"], glyph(path((C, XH), (C, 610), (340, CAP)), path((155, 540), (345, 600)))),
    "ø": combine(GLYPHS["o"], glyph(path((80, -25), (420, 465)))),
    "þ": glyph(path((L, DESC), (L, CAP)), bowl(left=L, right=R, bottom=0, top=XH)),
    "ƒ": glyph(path((150, DESC), (185, -95), (310, 530), (350, CAP), (420, CAP)), path((90, XMID), (350, XMID))),
    "Œ": combine(transform(GLYPHS["O"], 0.70, 1, 0, 0), transform(GLYPHS["E"], 0.68, 1, 165, 0)),
    "œ": combine(transform(GLYPHS["o"], 0.70, 1, 0, 0), transform(GLYPHS["e"], 0.68, 1, 165, 0)),
})


# Direct symbols that benefit from the same primitives but are not letters.
GLYPHS.update({
    "¡": glyph(path((C, 0), (C, 420)), dots=((C, 595, 1.0),)),
    "¿": glyph(path((R, 50), (345, 0), (155, 0), (L, 50), (L, 190), (C, MID), (C, 420)), dots=((C, 595, 1.0),)),
    "¢": combine(glyph(c_shape(bottom=80, top=560, cut=35)), glyph(path((C, -40), (C, CAP)))),
    "£": glyph(path((360, 590), (320, CAP), (210, CAP), (165, 590), (165, 80), (120, 0), (405, 0)), path((80, 300), (330, 300))),
    "¤": glyph(ring(155, 345, 180, 460, 35), path((90, 540), (155, 460)), path((345, 180), (410, 100)), path((410, 540), (345, 460)), path((155, 180), (90, 100))),
    "¥": combine(GLYPHS["Y"], glyph(path((120, 230), (380, 230)), path((120, 120), (380, 120)))),
    "¦": glyph(path((C, -50), (C, 220)), path((C, 420), (C, 690))),
    "§": glyph(path((360, 590), (320, CAP), (170, CAP), (130, 590), (130, 450), (370, 190), (370, 50), (330, 0), (180, 0), (140, 50)), path((340, 480), (130, 250), (130, 140), (170, 90))),
    "¬": glyph(path((90, MID), (410, MID), (410, 150))),
    "¶": glyph(path((390, CAP), (180, CAP), (110,570), (110,390), (180, MID), (C, MID)), path((C, CAP), (C, 0)), path((360, CAP), (360, 0))),
    "×": glyph(path((110, 500), (390, 140)), path((390, 500), (110, 140))),
    "÷": glyph(path((100, MID), (400, MID)), dots=((C, 520, 0.82), (C, 120, 0.82))),
    "€": combine(glyph(c_shape(bottom=0, top=CAP, cut=45)), glyph(path((80, 230), (340, 230)), path((80, 410), (340, 410)))),
    "°": glyph(ring(180, 320, 430, 590, 28)),
    "±": glyph(path((C, 220), (C, 580)), path((80, 400), (420, 400)), path((80, 80), (420, 80))),
    "·": glyph(dots=((C, MID, 1.0),)),
    "«": glyph(path((260, 520), (90, MID), (260, 120)), path((410, 520), (240, MID), (410, 120))),
    "»": glyph(path((90, 520), (260, MID), (90, 120)), path((240, 520), (410, MID), (240, 120))),
    "‹": glyph(path((340, 520), (150, MID), (340, 120))),
    "›": glyph(path((160, 520), (350, MID), (160, 120))),
    "–": glyph(path((80, MID), (420, MID))),
    "—": glyph(path((20, MID), (480, MID))),
    "‘": glyph(path((280, CAP), (220, 560), (220, 470))),
    "’": glyph(path((220, 470), (280, 550), (280, CAP))),
    "‚": glyph(path((280, 100), (220, 20), (220, -70))),
    "“": glyph(path((210, CAP), (150, 560), (150, 470)), path((350, CAP), (290, 560), (290, 470))),
    "”": glyph(path((150, 470), (210, 550), (210, CAP)), path((290, 470), (350, 550), (350, CAP))),
    "„": glyph(path((210, 100), (150, 20), (150, -70)), path((350, 100), (290, 20), (290, -70))),
    "†": glyph(path((C, -20), (C, CAP)), path((90, 430), (410, 430))),
    "‡": glyph(path((C, -20), (C, CAP)), path((90, 450), (410, 450)), path((90, 170), (410, 170))),
    "•": glyph(dots=((C, MID, 1.8),)),
    "…": glyph(dots=((105, 45, 0.75), (C, 45, 0.75), (395, 45, 0.75))),
    "‰": glyph(ring(65, 165, 455, 595, 20), path((105, 40), (395, 600)), ring(235, 335, 45, 185, 20), ring(340, 440, 45, 185, 20)),
})


IDENTITY = (1, 0, 0, 1, 0, 0)


def ref(name, xx=1, yy=1, dx=0, dy=0):
    return (name, (xx, 0, 0, yy, dx, dy))


# References scale completed glyphs, so small text also gets proportionally
# smaller strokes rather than cramped full-weight counters.
REFERENCES = {
    "\u00a0": (),
    "\u00ad": (ref("-"),),
    "©": (ref("O", 0.90, 0.90, 25, 30), ref("C", 0.38, 0.38, 155, 205)),
    "®": (ref("O", 0.90, 0.90, 25, 30), ref("R", 0.38, 0.38, 155, 205)),
    "ª": (ref("a", 0.55, 0.55, 112, 330),),
    "º": (ref("o", 0.55, 0.55, 112, 330),),
    "²": (ref("2", 0.55, 0.55, 112, 285),),
    "³": (ref("3", 0.55, 0.55, 112, 285),),
    "¹": (ref("1", 0.55, 0.55, 112, 285),),
    "¼": (ref("1", 0.42, 0.42, 35, 350), ref("/", 0.78, 0.78, 55, 70), ref("4", 0.42, 0.42, 260, -10)),
    "½": (ref("1", 0.42, 0.42, 35, 350), ref("/", 0.78, 0.78, 55, 70), ref("2", 0.42, 0.42, 260, -10)),
    "¾": (ref("3", 0.42, 0.42, 35, 350), ref("/", 0.78, 0.78, 55, 70), ref("4", 0.42, 0.42, 260, -10)),
    "™": (ref("T", 0.42, 0.42, 15, 360), ref("M", 0.42, 0.42, 270, 360)),
    "ˆ": (ref(".circumflex", dy=530),),
    "˜": (ref(".tilde", dy=530),),
    "¨": (ref(".dieresis", dy=530),),
    "¯": (ref(".macron", dy=530),),
    "´": (ref(".acute", dy=530),),
    "¸": (ref(".cedilla"),),
}


CP1252_EXTRA = "€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ"
TARGET_CODEPOINTS = tuple(sorted({*range(0x20, 0x7F), *range(0xA0, 0x100), *map(ord, CP1252_EXTRA)}))


def decomposition(char):
    """Return (base, mark) for the supported canonical Latin composites."""
    parts = normalize("NFD", char)
    if len(parts) == 2 and parts[1] in COMBINING_MARKS and ord(parts[0]) < 0x80:
        return (".dotlessi" if parts[0] == "i" else parts[0], COMBINING_MARKS[parts[1]])
    return None


assert len(TARGET_CODEPOINTS) == 218
assert set(map(chr, range(0x20, 0x7F))) <= GLYPHS.keys()
