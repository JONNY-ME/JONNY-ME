"""Original Signal Foundry vector drawings. No external assets or runtime dependencies."""
from html import escape

PALETTES = {
    "dark": dict(bg="#101820", panel="#15212A", ink="#F4EFE6", muted="#A9B6BA",
                 copper="#D99A63", teal="#75C4BC", line="#35454E", grid="#21303A"),
    "light": dict(bg="#F4EFE6", panel="#EAE5DB", ink="#182A33", muted="#54656B",
                  copper="#8D4C27", teal="#236B66", line="#B9BEB7", grid="#DEDCD3"),
}


class Drawing:
    def __init__(self, width, height, theme, title, description, motion=False):
        self.w, self.h, self.c = width, height, PALETTES[theme]
        motion_css = '''
.trace {stroke-dasharray: 1400; stroke-dashoffset: 0; animation: draw 4.5s ease-out 1;}
.pulse {opacity: 0; animation: pulse 4.8s ease-in-out 1;}
@keyframes draw {from {stroke-dashoffset:1400;} to {stroke-dashoffset:0;}}
@keyframes pulse {0%,100% {opacity:0;} 30%,65% {opacity:.8;}}
@media (prefers-reduced-motion: reduce) {.trace,.pulse {animation:none;} .pulse {display:none;}}
''' if motion else '.pulse {display:none;}'
        self.parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<style>
text {{font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;}}
{motion_css}
</style>
<defs><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".65" fill="{self.c['grid']}"/></pattern></defs>
<rect width="{width}" height="{height}" rx="4" fill="{self.c['bg']}"/>
<rect width="{width}" height="{height}" fill="url(#grid)"/>''']

    def path(self, d, color="line", width=1.4, extra=""):
        self.parts.append(f'<path d="{d}" fill="none" stroke="{self.c[color]}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" {extra}/>')

    def rect(self, x, y, w, h, fill="panel", stroke="line", radius=2):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{self.c[fill]}" stroke="{self.c[stroke]}"/>')

    def dot(self, x, y, r=3, color="copper", fill=True):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{self.c[color] if fill else self.c["bg"]}" stroke="{self.c[color]}" stroke-width="1.3"/>')

    def text(self, x, y, value, size=12, color="muted", anchor="start", spacing=0):
        self.parts.append(f'<text x="{x}" y="{y}" fill="{self.c[color]}" font-size="{size}" text-anchor="{anchor}" letter-spacing="{spacing}">{escape(value)}</text>')

    def group(self, transform):
        self.parts.append(f'<g transform="{transform}">')

    def endgroup(self):
        self.parts.append('</g>')

    def finish(self):
        return "\n".join(self.parts + ['</svg>', ''])


def monogram(d):
    """A single routed circuit: Y on the left, M on the right."""
    d.path("M-76 -44 L-40 -8 L-4 -44 M-40 -8 V48 M20 48 V-44 L56 -8 L92 -44 V48", "line", 10)
    d.path("M-76 -44 L-40 -8 L-4 -44 M-40 -8 V48 M20 48 V-44 L56 -8 L92 -44 V48", "copper", 2.4, 'class="trace"')
    for x, y in [(-76, -44), (-4, -44), (-40, 48), (20, 48), (92, 48)]:
        d.dot(x, y, 4, fill=False)
    d.dot(56, -8, 3, "teal")


def network(d, x, y):
    for a in [-12, 12]:
        for b in [-20, 0, 20]:
            d.path(f"M{x-24} {y+a} L{x} {y+b} L{x+24} {y+a}", "line", 1)
    for col, ys in [(-24, [-12, 12]), (0, [-20, 0, 20]), (24, [-12, 12])]:
        for row in ys:
            d.dot(x+col, y+row, 2.6, "teal", fill=False)


def chip(d, x, y):
    d.rect(x-17, y-17, 34, 34)
    d.rect(x-8, y-8, 16, 16, stroke="copper")
    for a in [-10, 0, 10]:
        d.path(f"M{x+a} {y-24} V{y-17} M{x+a} {y+17} V{y+24} M{x-24} {y+a} H{x-17} M{x+17} {y+a} H{x+24}", "copper", 1)


def hero(theme, compact=False, motion=True):
    width, height = (360, 300) if compact else (840, 310)
    d = Drawing(width, height, theme, "The Signal Foundry — Yohannes Melese",
                "An input signal traces a YM monogram, then branches into learning, software, and hardware. A conceptual illustration of interdisciplinary engineering.", motion=motion)
    d.text(24, 31, "THE SIGNAL FOUNDRY", 12, "copper", spacing=1.7)
    if compact:
        d.text(336, 31, "YM / 01", 10, anchor="end")
        d.path("M24 132 H40 L45 119 L51 145 L57 132 H76", "teal")
        d.group("translate(167 128) scale(.82)")
        monogram(d)
        d.endgroup()
        d.path("M76 132 H89 V92 H105 M134 167 V188 H183 V167 M243 167 H271 V93 H324", "copper", 1.5, 'class="trace"')
        d.path("M271 132 H324 M271 171 H324", "copper", 1.5, 'class="trace"')
        for y in [93, 132, 171]:
            d.dot(324, y, 3, "teal")
        d.path("M24 221 H336")
        for x, text in [(24, "LEARN"), (137, "BUILD"), (262, "RUN")]:
            d.text(x, 251, text, 18, "ink", spacing=1)
        d.text(24, 279, "AI / SOFTWARE / ELECTRONICS", 11)
    else:
        d.text(816, 31, "ADDIS ABABA  /  ETHIOPIA", 11, anchor="end", spacing=1)
        d.text(32, 113, "INPUT", 11, spacing=1.8)
        d.path("M32 151 H57 L64 132 L74 174 L85 140 L92 151 H132 L153 130 H206", "teal", 1.8)
        d.group("translate(282 174)")
        monogram(d)
        d.endgroup()
        d.path("M242 222 V238 H302 V222 M374 222 H430 V94 H528 M430 158 H528 M430 222 H528", "line", 2)
        d.path("M242 222 V238 H302 V222 M374 222 H430 V94 H528 M430 158 H528 M430 222 H528", "copper", 1.5, 'class="trace"')
        for y in [94, 158, 222]:
            d.dot(430, y, 3, "copper", False)
            d.path(f"M588 {y} H633", "line")
            d.dot(633, y, 2.6, "teal")
        network(d, 558, 94)
        d.path("M548 140 L536 158 L548 176 M568 140 L580 158 L568 176 M563 143 L553 173", "teal", 1.7)
        chip(d, 558, 222)
        for y, num, label in [(94, "01", "LEARNING"), (158, "02", "SOFTWARE"), (222, "03", "HARDWARE")]:
            d.text(656, y-5, num, 10, "copper")
            d.text(656, y+16, label, 16, "ink", spacing=1.1)
        d.text(206, 255, "RESEARCH → REAL SYSTEMS", 10, spacing=1)
        d.path("M24 278 H816", "line", .7)
        d.text(24, 297, "FIG. 01", 10)
        d.text(816, 297, "THREE DISCIPLINES. ONE ENGINEERING PRACTICE.", 10, anchor="end")
        d.parts.append(f'<circle class="pulse" cx="430" cy="158" r="8" fill="{d.c["copper"]}"/>')
    return d.finish()


def project(kind, theme, compact=False):
    width, height = (360, 180) if compact else (840, 190)
    titles = {"documents": "READ / EXTRACT / VALIDATE", "fpga": "PARALLEL / VOTE / INFER", "cli": "DISCOVER / SUBMIT / INSPECT"}
    d = Drawing(width, height, theme, titles[kind], "Simplified project schematic; explanatory illustration, not a measurement or live system.")
    d.text(20 if compact else 28, 27, titles[kind], 11, "copper", spacing=1)
    d.text(width-20, height-14, "SCHEMATIC", 9, anchor="end", spacing=1)
    if kind == "documents":
        xs = [45, 173, 300] if compact else [110, 402, 702]
        a, b, c = xs
        for off in [-8, 0, 8]:
            d.rect(a-20+off, 63+off, 38, 51)
        for yy in [85, 93, 101]:
            d.path(f"M{a-4} {yy} H{a+17}", "muted", 1)
        d.path(f"M{a+38} 94 H{b-32} M{b+32} 94 H{c-35}", "copper")
        d.rect(b-27, 65, 54, 58, stroke="copper")
        for yy in [78, 94, 110]:
            d.path(f"M{b-17} {yy} H{b-4}", "muted", 1)
            d.path(f"M{b+5} {yy} l4 4 l7 -8", "teal", 1.6)
        d.rect(c-29, 64, 58, 59)
        for yy in [78, 93, 108]:
            d.path(f"M{c-29} {yy} H{c+29}", "line", 1)
        d.path(f"M{c-10} 64 V123 M{c+10} 64 V123", "line", 1)
        d.rect(c+11, 94, 17, 13, fill="teal", stroke="teal", radius=0)
        labels = ["PAGES", "CHECKS", "WORKBOOK"]
    elif kind == "fpga":
        xs = [70, 193, 300] if compact else [180, 465, 710]
        a, b, c = xs
        for yy in [62, 94, 126]:
            d.rect(a-24, yy-10, 48, 20)
            d.path(f"M{a-42} 94 V{yy} H{a-24} M{a+24} {yy} H{b-40} V94 H{b-19}", "copper", 1)
            d.path(f"M{a-12} {yy} h24", "teal", 2)
        d.path(f"M{b} 75 L{b+19} 94 L{b} 113 L{b-19} 94 Z", "teal", 1.6)
        d.path(f"M{b+19} 94 H{c-25}", "copper")
        chip(d, c, 94)
        labels = ["MODELS", "VOTE", "INFER"]
    else:
        xs = [50, 175, 303] if compact else [126, 413, 704]
        a, b, c = xs
        d.rect(a-29, 65, 58, 56)
        d.path(f"M{a-29} 78 H{a+29}", "line", 1)
        d.dot(a-20, 72, 1.5)
        d.path(f"M{a-17} 90 l8 7 l-8 7 M{a-2} 105 h17", "teal", 1.7)
        d.path(f"M{a+29} 94 H{b-28} M{b+28} 94 H{c-26}", "copper")
        for yy in [73, 88, 103]:
            d.rect(b-24, yy, 48, 11, stroke="copper")
        d.path(f"M{c-24} 69 V119 H{c+27}", "muted", 1)
        for x, h in [(c-14, 19), (c, 35), (c+14, 28)]:
            d.rect(x, 116-h, 7, h, fill="teal", stroke="teal", radius=0)
        labels = ["CLI", "DATA", "RESULTS"]
    for x, label in zip(xs, labels):
        d.text(x, 153, label, 17 if compact else 12, "ink", anchor="middle", spacing=1)
    return d.finish()


def assets():
    result = {}
    for theme in PALETTES:
        for compact in [False, True]:
            suffix = f"{theme}{'-compact' if compact else ''}.svg"
            result[f"hero-{suffix}"] = hero(theme, compact)
            result[f"hero-static-{suffix}"] = hero(theme, compact, motion=False)
            for kind in ["documents", "fpga", "cli"]:
                result[f"{kind}-{suffix}"] = project(kind, theme, compact)
    return result
