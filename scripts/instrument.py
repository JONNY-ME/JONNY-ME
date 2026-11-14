"""YM-01 Bench primitives: an original, fictional mixed-signal instrument drawn as plain SVG.

No scripts, bitmaps, external fonts, or network calls. Every visible string passes through escape().
"""
from html import escape

MONO = 'ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace'

# Shared with yohannesmelese.com: bezel, ink, muted, ch0 (accent), and ch1 (success) mirror the
# site's tokens. Dark is the instrument screen; light is chart paper. Geometry is identical.
PALETTES = {
    "dark": dict(bezel="#212722", edge="#3A453C", screen="#141915", grid="#262E28", grid_major="#3A463D",
                 ink="#F3F0E7", muted="#A4AD9E", ch0="#E89A7F", ch1="#A3C89E", ch2="#E3B866", ch3="#94B8C9"),
    "light": dict(bezel="#ECE8DE", edge="#CFC8B8", screen="#FCFAF5", grid="#EAE5D9", grid_major="#D3CBBB",
                  ink="#242823", muted="#5C6057", ch0="#9F452C", ch1="#31653F", ch2="#855F12", ch3="#2F5F78"),
}
TEXT_COLORS = ("ink", "muted", "ch0", "ch1", "ch2", "ch3")
SURFACES = ("bezel", "screen")


def num(value):
    """Short, deterministic coordinates."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class Drawing:
    """An SVG canvas whose colours always come from one palette."""

    def __init__(self, width, height, theme, title, description, css=""):
        self.w, self.h, self.c = width, height, PALETTES[theme]
        style = f"text {{font-family: {MONO};}}" + (f"\n{css.strip()}" if css else "")
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
            f"<style>\n{style}\n</style>",
        ]

    def paint(self, key):
        return "none" if key is None else self.c[key]

    def raw(self, markup):
        self.parts.append(markup)

    def path(self, d, stroke="muted", width=1.4, fill=None, join="round", extra=""):
        self.parts.append(f'<path d="{d}" fill="{self.paint(fill)}" stroke="{self.paint(stroke)}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="{join}"{_x(extra)}/>')

    def rect(self, x, y, w, h, fill="screen", stroke=None, radius=0, width=1, extra=""):
        stroke_attr = f' stroke="{self.paint(stroke)}" stroke-width="{width}"' if stroke else ""
        self.parts.append(f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" rx="{radius}" fill="{self.paint(fill)}"{stroke_attr}{_x(extra)}/>')

    def circle(self, x, y, r, fill="ch0", extra=""):
        self.parts.append(f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" fill="{self.paint(fill)}"{_x(extra)}/>')

    def text(self, x, y, value, size=10, color="muted", anchor="start", spacing=0, weight=None, extra=""):
        weight_attr = f' font-weight="{weight}"' if weight else ""
        spacing_attr = f' letter-spacing="{spacing}"' if spacing else ""
        anchor_attr = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.parts.append(f'<text x="{num(x)}" y="{num(y)}" fill="{self.paint(color)}" font-size="{size}"{anchor_attr}{spacing_attr}{weight_attr}{_x(extra)}>{escape(value)}</text>')

    def group(self, attrs):
        self.parts.append(f"<g {attrs}>")

    def end(self):
        self.parts.append("</g>")

    def finish(self):
        return "\n".join(self.parts + ["</svg>", ""])


def _x(extra):
    return f" {extra}" if extra else ""


# Signals ---------------------------------------------------------------------------------------

def uart_bits(text):
    """8N1 frames, least-significant bit first: start 0, eight data bits, stop 1. Idle is high."""
    bits = []
    for byte in text.encode("ascii"):
        bits += [0] + [(byte >> i) & 1 for i in range(8)] + [1]
    return bits


def digital_path(x0, x1, transitions, high, low, idle=1):
    """A square wave from x0 to x1. transitions: sorted (x, level) pairs; the level starts at idle."""
    y = {1: high, 0: low}
    level, d = idle, [f"M{num(x0)} {num(y[idle])}"]
    for x, new in transitions:
        if new != level:
            d.append(f"H{num(x)}V{num(y[new])}")
            level = new
    d.append(f"H{num(x1)}")
    return "".join(d)


def uart_transitions(bits, start, bit_width):
    return [(start + i * bit_width, bit) for i, bit in enumerate(bits)] + [(start + len(bits) * bit_width, 1)]


def clock_transitions(x0, x1, half_period, first=1):
    transitions, x, level = [], x0 + half_period, first
    while x < x1 - 0.01:
        transitions.append((x, level))
        x, level = x + half_period, 1 - level
    return transitions


def analog_path(x0, x1, fn, step=2.5):
    """Sample fn(x) -> y from x0 to x1 inclusive."""
    count = max(2, round((x1 - x0) / step))
    points = [(x0 + (x1 - x0) * i / count, None) for i in range(count + 1)]
    coords = [f"{num(x)} {num(fn(x))}" for x, _ in points]
    return "M" + coords[0] + "L" + " ".join(coords[1:])


# Instrument furniture ----------------------------------------------------------------------------

def bezel(d):
    d.rect(0.5, 0.5, d.w - 1, d.h - 1, fill="bezel", stroke="edge", radius=10)


def screen(d, x, y, w, h):
    d.rect(x, y, w, h, fill="screen", stroke="edge", radius=4)


def graticule(d, x0, x1, top, bottom, divisions=10, separators=(), span=None, ruler=False):
    """Painted over the traces, as on a real scope: faint divisions, row separators, a time ruler."""
    step = (x1 - x0) / divisions
    verticals = "".join(f"M{num(x0 + i * step)} {num(top)}V{num(bottom)}" for i in range(divisions + 1))
    d.path(verticals, "grid_major", 0.8, extra='stroke-dasharray="1.5 3.5"')
    if separators:
        sx0, sx1 = span or (x0, x1)
        d.path("".join(f"M{num(sx0)} {num(y)}H{num(sx1)}" for y in separators), "grid", 1)
    if ruler:
        ticks = "".join(f"M{num(x0 + i * step / 5)} {num(bottom - (6 if i % 5 == 0 else 3))}V{num(bottom)}"
                        for i in range(divisions * 5 + 1))
        d.path(ticks, "grid_major", 1, join="miter")


def channel_label(d, x, y, ident, name, color, size=10):
    """A colour tab and channel id, with an optional name underneath."""
    if name:
        d.rect(x - 9, y - 11, 3, 22, fill=color, radius=1)
        d.text(x, y - 2, ident, size, color, weight="700", spacing=0.8)
        d.text(x, y + 10, name, size - 1, "muted", spacing=0.6)
    else:
        d.rect(x - 9, y - 6, 3, 12, fill=color, radius=1)
        d.text(x, y + size * 0.36, ident, size, color, weight="700", spacing=0.8)


def bus(d, segments, top, bottom, size=10, extra=""):
    """segments: (x_start, x_end, label, colour). A colour of None draws an idle (high-Z) line."""
    mid = (top + bottom) / 2
    for xs, xe, label, color in segments:
        if color is None:
            d.path(f"M{num(xs)} {num(mid)}H{num(xe)}", "muted", 1, extra='stroke-dasharray="2 3"')
            continue
        s = min(4.5, (xe - xs) / 4)
        d.path(f"M{num(xs)} {num(mid)}L{num(xs + s)} {num(top)}H{num(xe - s)}L{num(xe)} {num(mid)}L{num(xe - s)} {num(bottom)}H{num(xs + s)}Z",
               color, 1.3, fill=color, extra='fill-opacity=".13"')
        if label:
            d.text((xs + xe) / 2, mid + size * 0.36, label, size, color, "middle", 0.8, "700", extra)


def check_mark(d, x, y, size, color, extra=""):
    d.path(f"M{num(x)} {num(y - size * 0.45)}l{num(size * 0.35)} {num(size * 0.4)}l{num(size * 0.65)} {num(-size * 0.8)}",
           color, 1.6, extra=extra)


def flag_mark(d, x, y, color, extra=""):
    """A drawn marker flag; glyph flags are missing from many monospace fonts."""
    d.path(f"M{num(x)} {num(y + 11)}V{num(y)}", color, 1.3, extra=extra)
    d.path(f"M{num(x)} {num(y)}H{num(x + 8)}L{num(x + 6)} {num(y + 2.75)}L{num(x + 8)} {num(y + 5.5)}H{num(x)}Z",
           color, 1, fill=color, extra=extra)


def cursor(d, x, top, bottom, label, color, extra=""):
    d.path(f"M{num(x)} {num(top)}V{num(bottom)}", color, 1, extra=f'stroke-dasharray="3 3" {extra}'.strip())
    d.rect(x - 6, bottom - 12, 12, 12, fill=color, radius=2, extra=extra)
    d.text(x, bottom - 3, label, 9, "screen", "middle", weight="700", extra=extra)


def led(d, x, y, color, square=False, extra=""):
    if square:
        d.rect(x - 3.5, y - 3.5, 7, 7, fill=color, radius=1, extra=extra)
    else:
        d.circle(x, y, 3.5, color, extra)
