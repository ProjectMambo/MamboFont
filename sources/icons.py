"""One-weight, fixed-codepoint source geometry for Mambo Icons."""

from sources.geometry import combine, glyph, loop, path


STROKE = 60


def rectangle(left, bottom, right, top):
    return ((left, bottom), (left, top), (right, top), (right, bottom))


def chamfered_box(left, bottom, right, top, cut=60):
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


def indicators(level):
    count = level // 25
    return tuple(rectangle(350 + index * 80, 160, 410 + index * 80, 240) for index in range(count))


def battery(level):
    shell = glyph(
        chamfered_box(140, 140, 800, 560),
        path((800, 280), (880, 280), (880, 420), (800, 420)),
    )
    cells = tuple(rectangle(210 + index * 140, 230, 310 + index * 140, 470) for index in range(level // 25))
    return combine(shell, glyph(fills=cells))


def audio(level):
    result = glyph(loop((140, 250), (280, 250), (480, 100), (480, 600), (280, 450), (140, 450)))
    waves = (
        path((540, 260), (600, 320), (600, 380), (540, 440)),
        path((620, 180), (700, 270), (700, 430), (620, 520)),
        path((700, 100), (800, 220), (800, 480), (700, 600)),
        path((780, 20), (900, 170), (900, 530), (780, 680)),
    )
    return combine(result, glyph(*waves[: level // 25]))


def headphones(level):
    return glyph(
        path((180, 220), (180, 460), (240, 600), (360, 680), (640, 680), (760, 600), (820, 460), (820, 220)),
        chamfered_box(120, 80, 280, 300, 40),
        chamfered_box(720, 80, 880, 300, 40),
        fills=indicators(level),
    )


def light(level):
    cells = tuple(rectangle(300 + index * 100, 270, 370 + index * 100, 350) for index in range(level // 25))
    return glyph(
        chamfered_box(240, 180, 760, 680),
        path((360, 180), (360, 20), (640, 20), (640, 180)),
        path((360, -80), (640, -80)),
        fills=cells,
    )


def camera(off=False):
    paths = [chamfered_box(120, 80, 880, 580), chamfered_box(370, 220, 630, 480, 50), path((260, 580), (340, 680), (520, 680), (600, 580))]
    if off:
        paths.append(path((120, 680), (880, -80)))
    return glyph(*paths)


def coffee(full=False):
    return glyph(
        chamfered_box(180, 80, 700, 560),
        path((700, 460), (840, 460), (880, 420), (880, 220), (840, 180), (700, 180)),
        path((140, -20), (760, -20)),
        fills=(rectangle(240, 140, 640, 360),) if full else (),
    )


def state(on=False):
    return glyph(
        chamfered_box(180, 20, 820, 660),
        chamfered_box(300, 140, 700, 540),
        fills=(rectangle(360, 200, 640, 480),) if on else (),
    )


def lock(opened=False):
    shackle = path((300 if opened else 260, 360), (300 if opened else 260, 560), (360, 680), (620, 680), (740, 560), (740, 480))
    if not opened:
        shackle = path((260, 360), (260, 560), (360, 680), (640, 680), (740, 560), (740, 360))
    return glyph(chamfered_box(180, -40, 820, 380), shackle, path((500, 230), (500, 80)), dots=((500, 250, 1.0),))


def cpu():
    pins = []
    for value in (240, 400, 560, 720):
        pins.extend((path((value, 80), (value, -80)), path((value, 600), (value, 680))))
    for value in (160, 320, 480):
        pins.extend((path((120, value), (60, value)), path((880, value), (940, value))))
    return glyph(chamfered_box(120, 80, 880, 600), chamfered_box(300, 220, 700, 460), *pins)


def disk():
    return glyph(
        chamfered_box(160, -40, 840, 680),
        chamfered_box(300, 400, 700, 680, 40),
        chamfered_box(280, 40, 720, 300, 40),
        path((600, 680), (600, 480)),
    )


# Existing v0.2 values are frozen.  Retired brand artwork leaves permanent
# holes so an old icon can never silently become a different one.
ICON_CODEPOINTS = {
    "audio-0": 0xE000,
    "audio-100": 0xE001,
    "audio-25": 0xE002,
    "audio-50": 0xE003,
    "audio-75": 0xE004,
    "battery-0": 0xE005,
    "battery-100": 0xE006,
    "battery-25": 0xE007,
    "battery-50": 0xE008,
    "battery-75": 0xE009,
    "camera-off": 0xE00A,
    "camera-on": 0xE00B,
    "coconut": 0xE00C,
    "cod": 0xE00D,
    "coffee-empty": 0xE00E,
    "coffee-full": 0xE00F,
    "cpu": 0xE010,
    "disk": 0xE011,
    "headphones-0": 0xE012,
    "headphones-100": 0xE013,
    "headphones-25": 0xE014,
    "headphones-50": 0xE015,
    "headphones-75": 0xE016,
    "light-0": 0xE017,
    "light-100": 0xE018,
    "light-25": 0xE019,
    "light-50": 0xE01A,
    "light-75": 0xE01B,
    "lock": 0xE01C,
    "mambo": 0xE01D,
    "off": 0xE01E,
    "on": 0xE01F,
    "unlock": 0xE020,
}

RETIRED = {"coconut", "cod", "mambo"}
NEXT_ICON_CODEPOINT = 0xE100

ICONS = {
    "audio-0": audio(0),
    "audio-25": audio(25),
    "audio-50": audio(50),
    "audio-75": audio(75),
    "audio-100": audio(100),
    "battery-0": battery(0),
    "battery-25": battery(25),
    "battery-50": battery(50),
    "battery-75": battery(75),
    "battery-100": battery(100),
    "camera-off": camera(True),
    "camera-on": camera(),
    "coffee-empty": coffee(),
    "coffee-full": coffee(True),
    "cpu": cpu(),
    "disk": disk(),
    "headphones-0": headphones(0),
    "headphones-25": headphones(25),
    "headphones-50": headphones(50),
    "headphones-75": headphones(75),
    "headphones-100": headphones(100),
    "light-0": light(0),
    "light-25": light(25),
    "light-50": light(50),
    "light-75": light(75),
    "light-100": light(100),
    "lock": lock(),
    "off": state(),
    "on": state(True),
    "unlock": lock(True),
}

assert ICONS.keys() == ICON_CODEPOINTS.keys() - RETIRED
assert len(set(ICON_CODEPOINTS.values())) == len(ICON_CODEPOINTS)
