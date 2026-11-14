"""YM-01 Bench compositions: the hero capture, three project captures, and section markers.

YM-01 is a fictional instrument. The hero's UART waveform is a genuine 8N1 encoding of NAME; the
project captures are illustrative and say so on the artwork.
"""
from math import cos, exp, pi, sin

from instrument import (PALETTES, Drawing, analog_path, bezel, bus, channel_label, check_mark, clock_transitions,
                        cursor, digital_path, flag_mark, graticule, led, num, screen, uart_bits, uart_transitions)

NAME = "YOHANNES"
BAUD = 9600
# Seconds. The sweep reveals the capture once; the readout settles; nothing loops.
MOTION = {"start": 0.3, "sweep": 3.0, "settle": 3.4, "fade": 0.5}
MOTION_END = MOTION["settle"] + MOTION["fade"]

# Illustrative inference cycles: (M1, M2, M3) class predictions per cycle.
FPGA_CYCLES = [(3, 3, 3), (7, 1, 7), (2, 2, 5), (0, 0, 0)]

# Commands, JSON shapes, and exit codes follow the zindi-cli README's output contract.
CLI_SESSION = [
    dict(command="zindi use my-challenge", output='{"ok": true, …}', stream="stdout", exit=0),
    dict(command="zindi data download --output data/", output='{"ok": true, …}', stream="stdout", exit=0),
    dict(command='zindi submissions submit sub.csv --comment "baseline"', short="zindi submissions submit sub.csv",
         output='{"ok": true, "command": "submissions.submit", "data": {"status": "initial", …}}',
         short_output='{"ok": true, "command": "submissions.submit", …}', stream="stdout", exit=0),
    dict(command="zindi leaderboard --mine",
         output='{"ok": false, "error": {"code": "AUTH_EXPIRED", "message": "Run: zindi auth login", …}}',
         short_output='{"ok": false, "error": {"code": "AUTH_EXPIRED", …}}', stream="stderr", exit=3),
]
CLI_NEXT = "zindi auth login"


def majority(lanes):
    winner = max(sorted(set(lanes)), key=lanes.count)
    return winner, lanes.count(winner)


class Cue:
    """Animation hooks for the hero. Static renders get no classes, so they show the final frame."""

    def __init__(self, motion):
        self.motion = motion

    def reveal(self, delay):
        return f'class="reveal" style="animation-delay:{num(delay)}s"' if self.motion else ""

    def settle(self):
        return 'class="settle"' if self.motion else ""


def motion_css(travel):
    start, sweep, settle, fade = MOTION["start"], MOTION["sweep"], MOTION["settle"], MOTION["fade"]
    return f"""
.shutter {{animation: sweep {sweep}s linear {start}s 1 both;}}
.playhead {{animation: sweep {sweep}s linear {start}s 1 both, vanish .2s linear {num(start + sweep)}s 1 forwards;}}
.reveal {{opacity: 0; animation: reveal .25s ease-out 1 forwards;}}
.settle {{opacity: 0; animation: reveal {fade}s ease-out {settle}s 1 forwards;}}
.armed {{animation: vanish .15s linear {settle}s 1 forwards;}}
@keyframes sweep {{from {{transform: translateX(0);}} to {{transform: translateX({num(travel)}px);}}}}
@keyframes reveal {{to {{opacity: 1;}}}}
@keyframes vanish {{to {{opacity: 0;}}}}
@media (prefers-reduced-motion: reduce) {{
  .shutter, .playhead, .armed {{display: none;}}
  .reveal, .settle {{opacity: 1; animation: none;}}
}}"""


def grouped(d, attrs, draw):
    if attrs:
        d.group(attrs)
    draw()
    if attrs:
        d.end()


# Hero ----------------------------------------------------------------------------------------------

HERO = {
    False: dict(w=840, h=340, screen=(16, 34, 808, 262), x0=112, x1=812, status=22, decode=(46, 16),
                d0=(72, 98), a1=(122, 172), b2=(196, 216), d3=(240, 258), seps=(110, 184, 228),
                grid=(36, 294), cursor=(44, 288), labels=dict(d0=85, a1=147, b2=206, d3=249)),
    True: dict(w=360, h=330, screen=(8, 32, 344, 240), x0=20, x1=340, status=21, decode=(54, 14),
               d0=(76, 94), a1=(124, 156), b2=(186, 202), d3=(232, 248), seps=(104, 166, 212),
               grid=(34, 270), cursor=(54, 262), labels=dict(d0=48, a1=118, b2=180, d3=226)),
}


def hero(theme, compact=False, motion=True):
    L = HERO[compact]
    w, h, x0, x1 = L["w"], L["h"], L["x0"], L["x1"]
    div = (x1 - x0) / 10                       # 1 ms per division
    bit = div * 1000 / BAUD                     # pixels per UART bit
    trig = x0 + 0.6 * div
    bits = uart_bits(NAME)
    frames_end = trig + len(bits) * bit
    travel = x1 - x0 + 4
    duration = f"{len(bits) / BAUD * 1000:.2f} ms"
    cue = Cue(motion)
    d = Drawing(w, h, theme, "YM-01 Bench, capture 001: Yohannes Melese",
                f"A logic-analyzer capture. A UART signal ({BAUD} baud, 8N1) decodes byte by byte into {NAME}, "
                "above learning, software, and hardware channels. A conceptual illustration of interdisciplinary engineering.",
                css=motion_css(travel) if motion else "")

    # Bezel and status bar.
    bezel(d)
    sy, right = L["status"], w - (18 if compact else 28)
    left = 18 if compact else 30
    d.text(left, sy, "YM-01", 12, "ink", spacing=1.5, weight="700")
    d.text(left + 54, sy, "ADDIS ABABA" if compact else "MIXED-SIGNAL BENCH", 10, "muted", spacing=1.2)
    if not compact:
        d.text(w / 2 + 40, sy, "CAPTURE 001 · ADDIS ABABA", 10, "muted", "middle", 1.2)
    if motion:
        led(d, right - 44, sy - 3.5, "ch1", extra='class="armed"')
        d.text(right, sy, "ARMED", 10, "ch1", "end", 1.2, "700", 'class="armed"')
    led(d, right - 103, sy - 3.5, "ch0", square=True, extra=cue.settle())
    d.text(right, sy, "STOP · SINGLE", 10, "ch0", "end", 1.2, "700", cue.settle())
    screen(d, *L["screen"])

    # Traces: acquired under the shutter.
    hi, lo = L["d0"]
    d.path(digital_path(x0, x1, uart_transitions(bits, trig, bit), hi, lo), "ch0", 1.6, join="miter")
    if not compact:
        for i, value in enumerate(bits):
            d.circle(trig + (i + 0.5) * bit, hi if value else lo, 1.25, "ch0")

    top, bottom = L["a1"]

    def learn(x):
        t = max(0.0, (x - trig) / (x1 - x0))
        jitter = 0.10 * sin(2 * pi * x / 24) + 0.06 * sin(2 * pi * x / 13 + 1.1) + 0.035 * sin(2 * pi * x / 7 + 0.3)
        value = 0.1 + 0.76 * exp(-3.8 * t) + jitter * (0.2 + 0.8 * exp(-3.2 * t))
        return bottom - 2 - min(1, max(0, value)) * (bottom - top - 4)

    d.path(analog_path(x0, x1, learn, 1.6 if compact else 2.5), "ch1", 1.4)

    stages = ["PARSE", "TEST", "BUILD", "SHIP"]
    span = (frames_end - trig) / len(stages)
    bus(d, [(x0, trig, "", None)] + [(trig + i * span, trig + (i + 1) * span, s, "ch2") for i, s in enumerate(stages)]
        + [(frames_end, x1, "", None)], *L["b2"], size=9 if compact else 10)
    d.path(digital_path(x0, x1, clock_transitions(x0, x1, div / 4), *L["d3"], idle=0), "ch3", 1.4, join="miter")

    if motion:
        sx, sy0, sh = x0 - 1, L["screen"][1] + 1, L["screen"][3] - 2
        d.raw(f'<defs><clipPath id="acquire"><rect x="{num(sx)}" y="{num(sy0)}" width="{num(x1 - x0 + 3)}" height="{num(sh)}"/></clipPath></defs>')
        d.group('clip-path="url(#acquire)"')
        d.rect(sx, sy0, x1 - x0 + 3, sh, fill="screen", extra='class="shutter"')
        d.end()

    # Graticule over the traces, then labels and annotations.
    gx0 = L["screen"][0] + 1
    graticule(d, x0, x1, *L["grid"], separators=L["seps"], span=(gx0, x1), ruler=True)
    labels = L["labels"]
    channels = [("d0", "D0", "TX 9600" if not compact else "TX · UART 9600 8N1", "ch0"),
                ("a1", "A1", "LEARNING", "ch1"), ("b2", "B2", "SOFTWARE", "ch2"), ("d3", "D3", "HARDWARE", "ch3")]
    for key, ident, name, color in channels:
        if compact:
            d.rect(x0 - 2, labels[key] - 8.5, 26 + len(name) * 6, 11.5, fill="screen")
            d.text(x0, labels[key], ident, 9.5, color, spacing=0.8, weight="700")
            d.text(x0 + 23, labels[key], name, 9, "muted", spacing=0.6)
        else:
            channel_label(d, 34, labels[key], ident, name, color)
    gt = L["grid"][0]
    d.path(f"M{num(trig - 4)} {gt + 1}H{num(trig + 4)}L{num(trig)} {gt + 7}Z", "ch0", 1, fill="ch0")
    if not compact:
        d.text(trig - 7, gt + 7.5, "T", 8, "ch0", "end", weight="700")

    dy, dh = L["decode"]
    for i, char in enumerate(NAME):
        fx, fw = trig + i * 10 * bit, 10 * bit
        centre = fx + fw / 2
        delay = MOTION["start"] + (fx + fw - (x0 - 1)) / travel * MOTION["sweep"]

        def frame(fx=fx, fw=fw, centre=centre, char=char):
            d.rect(fx + 1.2, dy, fw - 2.4, dh, fill="ch0", stroke="ch0", radius=2, extra='fill-opacity=".14" stroke-opacity=".7"')
            if compact:
                d.text(centre, dy + dh - 3.5, char, 10.5, "ink", "middle", weight="700")
            else:
                d.text(centre - 13, dy + 12, char, 11, "ink", "middle", weight="700")
                d.text(centre + 10, dy + 11.5, f"0x{ord(char):02X}", 9, "ch0", "middle")
        grouped(d, cue.reveal(delay), frame)

    ctop, cbottom = L["cursor"]

    def readings():
        cursor(d, trig, ctop, cbottom, "A", "ink")
        cursor(d, frames_end, ctop, cbottom, "B", "ink")
        d.text(frames_end - 6 if compact else x1 - 4, top + (12 if compact else 18), "SETTLED", 8.5, "ch1", "end", 1, "700")
    grouped(d, cue.settle(), readings)

    if motion:
        d.group('clip-path="url(#acquire)"')
        d.raw(f'<g class="playhead"><rect x="{num(x0 - 4)}" y="{num(sy0)}" width="6" height="{num(sh)}" fill="{d.c["ink"]}" fill-opacity=".08"/>'
              f'<path d="M{num(x0 - 1)} {num(sy0)}V{num(sy0 + sh)}" stroke="{d.c["ink"]}" stroke-opacity=".6" stroke-width="1.2"/></g>')
        d.end()

    # Readout bar.
    if compact:
        d.text(18, 297, "DECODE", 10, "muted", spacing=1.5)
        d.text(342, 297, "1 ms/div", 9.5, "muted", "end")
        d.text(76, 298, NAME, 15, "ink", spacing=2.5, weight="700", extra=cue.settle())
        d.text(18, 318, "8N1 · 8 FRAMES · 0 ERRORS", 9.5, "muted", spacing=0.6, extra=cue.settle())
        d.text(342, 318, f"Δt A→B {duration}", 9.5, "ink", "end", extra=cue.settle())
    else:
        d.text(30, 323, "DECODE", 10, "muted", spacing=1.5)
        d.text(92, 324, NAME, 15, "ink", spacing=3, weight="700", extra=cue.settle())
        d.text(214, 323, "UART 8N1 · 8 FRAMES · 0 ERRORS", 10, "muted", spacing=0.8, extra=cue.settle())
        d.text(744, 323, f"Δt A→B = {duration}", 10, "ink", "end", extra=cue.settle())
        d.text(812, 323, "1 ms/div", 10, "muted", "end")
    return d.finish()


# Project captures ----------------------------------------------------------------------------------

def capture_frame(d, number, mode, note, compact, status_y, screen_box, centre=None):
    bezel(d)
    left, right = (18, d.w - 18) if compact else (26, d.w - 26)
    d.text(left, status_y, "YM-01", 11, "ink", spacing=1.4, weight="700")
    d.text(left + 50, status_y, f"{'' if compact else 'CAPTURE '}{number:03d} · {mode}", 9.5, "muted", spacing=1.2)
    if centre and not compact:
        d.text(d.w / 2 + 50, status_y, centre, 9.5, "muted", "middle", 1.2)
    d.text(right, status_y, note, 9, "muted", "end", 1.2)
    screen(d, *screen_box)


def readout(d, y, label, value, right_text=None, compact=False, label_color="muted"):
    x = 18 if compact else 26
    d.text(x, y, label, 9.5, label_color, spacing=1.2, weight="700" if label_color != "muted" else None)
    d.text(x + len(label) * (6.9 if compact else 7.1) + 8, y, value, 9.5 if compact else 10, "ink")
    if right_text and not compact:
        d.text(d.w - 26, y, right_text, 9.5, "muted", "end", 1)


FIELDS = [("A", "ch1", "field · rules"), ("B", "ch1", "field · rules"), ("?", "ch0", "smudged · llm"), ("Σ", "ch3", "total · check")]


def capture_documents(theme, compact=False):
    w, h = (360, 280) if compact else (840, 220)
    d = Drawing(w, h, theme, "Capture 002: probing a tax document",
                "Illustrative probe capture. Fields on a tax page feed rules, LLM fallback, arithmetic check, and confidence "
                "channels; a low-confidence field drops below the threshold and is flagged for review.")
    capture_frame(d, 2, "PROBE", "ILLUSTRATIVE" if compact else "ILLUSTRATIVE CAPTURE", compact,
                  19 if compact else 20, (8, 28, 344, 214) if compact else (12, 30, 816, 156))

    if compact:
        page, field_y, box, tag_x = (20, 38, 50, 72), [58, 72, 86, 102], (36, 28, 9), 25
        pod, pins = (90, 56, 12, 48), [64, 76, 88, 100]
        x0, x1, slot_y, rows = 72, 342, (118, 12), dict(RULES=(140, 152), LLM=(162, 174), CHECK=(184, 196))
        conf, label_x, edge = (208, 230), 18, 8
    else:
        page, field_y, box, tag_x = (30, 42, 104, 132), [82, 102, 122, 150], (78, 44, 12), 40
        pod, pins = (166, 84, 24, 52), [92, 104, 116, 128]
        x0, x1, slot_y, rows = 290, 812, (38, 14), dict(RULES=(62, 76), LLM=(88, 102), CHECK=(114, 128))
        conf, label_x, edge = (140, 170), 222, 14

    # The page, its fields, and probe leads.
    px, py, pw, ph = page
    fold = 8 if compact else 14
    d.path(f"M{px + 2} {py}H{px + pw - fold}L{px + pw} {py + fold}V{py + ph - 2}Q{px + pw} {py + ph} {px + pw - 2} {py + ph}"
           f"H{px + 2}Q{px} {py + ph} {px} {py + ph - 2}V{py + 2}Q{px} {py} {px + 2} {py}Z", "muted", 1, fill="bezel")
    d.path(f"M{px + pw - fold} {py}V{py + fold}H{px + pw}", "muted", 1)
    d.path(f"M{px + 6 if compact else px + 10} {py + 10 if compact else py + 12}H{px + pw - fold - 4}", "ink", 2, extra='stroke-opacity=".7"')
    if not compact:
        d.path(f"M{px + 10} {py + 20}H{px + 48}", "muted", 1)
    bx, bw, bh = box
    for (tag, color, _), y, pin in zip(FIELDS, field_y, pins):
        d.text(tag_x, y + 3, tag, 8.5 if compact else 9, color, "middle", weight="700")
        if not compact:
            d.path(f"M52 {y}H72", "muted", 1, extra='stroke-opacity=".6"')
        if tag == "Σ":
            d.path(f"M{bx} {y - bh + 1}H{bx + bw}", "muted", 1)
        d.rect(bx, y - bh / 2, bw, bh, fill=color, stroke=color, radius=1.5, extra='fill-opacity=".12"')
        if tag == "?":
            step = 4 if compact else 5
            d.path(f"M{bx + 3} {y}q{step / 2} -3.5 {step} 0" + f" t{step} 0" * int((bw - 8) / step - 1), "ch0", 1.1)
        else:
            d.path(f"M{bx + 4} {y}H{bx + bw - 9}", "ink", 1.6, extra='stroke-opacity=".75"')
        tip = bx + bw + 2
        d.circle(tip, y, 2 if compact else 2.4, color)
        mid = (tip + pod[0]) / 2
        d.path(f"M{tip} {y}C{num(mid)} {y} {num(mid)} {pin} {pod[0]} {pin}", color, 1.1)
    qx, qy, qw, qh = pod
    d.rect(qx, qy, qw, qh, fill="bezel", stroke="muted", radius=3)
    d.text(qx + qw / 2, qy - 6, "PROBE", 7.5 if compact else 8, "muted", "middle", 1)

    centres = {name: (a + b) / 2 for name, (a, b) in rows.items()}
    centres["CONF"] = sum(conf) / 2
    if compact:
        d.text(116, 64, "PROBE · 4 FIELDS", 10, "ink", spacing=0.8, weight="700")
        for i, line in enumerate(["deterministic rules first,", "LLM only on misses,", "every value checked."]):
            d.text(116, 81 + i * 13, line, 9, "muted")
    else:
        for pin, name in zip(pins, ["RULES", "LLM", "CHECK", "CONF"]):
            c = centres[name]
            d.path(f"M{qx + qw} {pin}C{qx + qw + 12} {pin} {qx + qw + 10} {num(c)} {label_x - 12} {num(c)}", "muted", 1, extra='stroke-opacity=".7"')

    # Channels: one time slot per probed field.
    slot = (x1 - x0) / 4
    slots = [(x0 + k * slot, x0 + (k + 1) * slot) for k in range(4)]
    colors = dict(RULES="ch1", LLM="ch2", CHECK="ch3", CONF="ch0")

    def pulses(name, ks, label=None, hold=False):
        hi, lo = rows[name]
        transitions = []
        for k in ks:
            xs, xe = slots[k]
            end = x1 if hold else xe - edge
            d.rect(xs + edge, hi, end - xs - edge, lo - hi, fill=colors[name], extra='fill-opacity=".12"')
            transitions += [(xs + edge, 1), (end, 0)] if not hold else [(xs + edge, 1)]
        d.path(digital_path(x0, x1, transitions, hi, lo, idle=0), colors[name], 1.5, join="miter")

    pulses("RULES", [0, 1, 3])
    pulses("LLM", [2])
    pulses("CHECK", [3], hold=True)

    ctop, cbottom = conf
    values = [0.96, 0.93, 0.58, 0.97]
    centres_x = [(a + b) / 2 for a, b in slots]

    def confidence(x):
        if x <= centres_x[0]:
            v = values[0]
        elif x >= centres_x[-1]:
            v = values[-1]
        else:
            k = int((x - centres_x[0]) // slot)
            t = (x - centres_x[k]) / slot
            v = values[k] + (values[k + 1] - values[k]) * (1 - cos(pi * t)) / 2
        v += 0.006 * sin(x / 5)
        return cbottom - (v - 0.5) / 0.5 * (cbottom - ctop)

    threshold = cbottom - 0.6 * (cbottom - ctop)
    d.path(f"M{x0} {num(threshold)}H{x1}", "ch0", 1, extra='stroke-dasharray="4 4" stroke-opacity=".55"')
    d.path(analog_path(x0, x1, confidence, 2), "ch0", 1.5)

    graticule(d, x0, x1, 30 if compact else 32, 240 if compact else 184, 8,
              separators=(135, 157, 179, 201) if compact else (57, 83, 109, 135), span=(edge if compact else label_x - 10, x1))

    for name, c in centres.items():
        channel_label(d, label_x, c, name, None, colors[name], 9 if compact else 10)

    sy, sh = slot_y
    for (tag, color, desc), (xs, xe) in zip(FIELDS, slots):
        d.rect(xs + 3, sy, slot - 6, sh, fill=color, stroke=color, radius=2, extra='fill-opacity=".12" stroke-opacity=".6"')
        if compact:
            d.text((xs + xe) / 2, sy + sh - 3, tag, 9.5, color, "middle", weight="700")
        else:
            d.text(xs + 13, sy + 10.5, tag, 10, color, "middle", weight="700")
            d.text(xs + 24, sy + 10, desc, 8.5, "muted", spacing=0.4)

    xs, xe = slots[2]
    hi, lo = rows["LLM"]
    d.text((xs + xe) / 2, lo - (3 if compact else 3.5), "FALLBACK", 8 if compact else 9, "ch2", "middle", 0.6, "700")
    xs, _ = slots[3]
    hi, lo = rows["CHECK"]
    label = "A+B=Σ" if compact else "A + B = Σ"
    d.text(xs + edge + 6, lo - 3, label, 8.5 if compact else 9.5, "ch3", spacing=0.4, weight="700")
    check_mark(d, xs + edge + 6 + len(label) * (5.4 if compact else 6.1) + 5, lo - 4, 6 if compact else 7, "ch3")
    d.text(x1 - 3, threshold + (10 if compact else 9), "0.80", 8, "muted", "end")
    c2 = centres_x[2]
    if compact:
        flag_mark(d, c2 - 22, ctop - 6, "ch0")
        d.text(c2 - 10, ctop + 2.5, "REVIEW", 8.5, "ch0", spacing=0.6, weight="700")
    else:
        flag_mark(d, c2 - 26, cbottom + 1, "ch0")
        d.text(c2 - 14, cbottom + 11, "REVIEW", 9, "ch0", spacing=0.8, weight="700")

    readout(d, 262 if compact else 207, "AUDIT" if compact else "AUDIT TRAIL", "value → page · rule · confidence",
            "READ · EXTRACT · VALIDATE · REVIEW", compact)
    return d.finish()


def capture_fpga(theme, compact=False):
    w, h = (360, 244) if compact else (840, 220)
    d = Drawing(w, h, theme, "Capture 003: an FPGA model ensemble",
                "Illustrative timing capture. Three parallel model lanes predict a class each cycle; a majority vote, "
                "registered on the next clock edge, resolves their disagreements.")
    capture_frame(d, 3, "TIMING", "ILLUSTRATIVE" if compact else "ILLUSTRATIVE CAPTURE", compact,
                  19 if compact else 20, (8, 28, 344, 180) if compact else (12, 30, 816, 156),
                  "PARALLEL LANES · QUANTIZED · MAJORITY VOTE")
    if compact:
        x0, x1, label_x = 52, 342, 18
        rows = dict(CLK=(38, 50), M1=(60, 76), M2=(86, 102), M3=(112, 128), VOTE=(140, 158), VALID=(170, 184))
        seps, grid = (55, 134, 164), (30, 206)
    else:
        x0, x1, label_x = 96, 812, 30
        rows = dict(CLK=(40, 52), M1=(60, 76), M2=(84, 100), M3=(108, 124), VOTE=(134, 152), VALID=(162, 176))
        seps, grid = (56, 129, 157), (32, 184)
    period = (x1 - x0) / 10
    rise = [x0 + period * (i + 0.5) for i in range(10)]
    votes = [majority(list(lanes)) for lanes in FPGA_CYCLES]

    for k, (lanes, (vote, agree)) in enumerate(zip(FPGA_CYCLES, votes)):
        if agree < 3:
            d.rect(rise[2 * k], rows["M1"][0] - 3, 2 * period, rows["M3"][1] - rows["M1"][0] + 6, fill="ch0", extra='fill-opacity=".07"')

    d.path(digital_path(x0, x1, clock_transitions(x0, x1, period / 2), *rows["CLK"], idle=0), "ch3", 1.4, join="miter")
    size = 9.5 if compact else 10
    for j, lane in enumerate(["M1", "M2", "M3"]):
        segments = [(x0, rise[0], "", None)]
        for k, (lanes, (vote, _)) in enumerate(zip(FPGA_CYCLES, votes)):
            segments.append((rise[2 * k], rise[2 * k + 2], str(lanes[j]), "ch1" if lanes[j] == vote else "ch0"))
        bus(d, segments + [(rise[8], x1, "", None)], *rows[lane], size=size)

    vt, vb = rows["VOTE"]
    bus(d, [(x0, rise[1], "", "muted")] + [(rise[2 * k + 1], rise[2 * k + 3], "", "ch0") for k in range(4)]
        + [(rise[9], x1, "", None)], vt, vb)
    for k, (vote, agree) in enumerate(votes):
        centre = (rise[2 * k + 1] + rise[2 * k + 3]) / 2
        d.text(centre - (7 if compact else 9), (vt + vb) / 2 + 4, str(vote), size + 1, "ink", "middle", weight="700")
        d.text(centre + (9 if compact else 11), (vt + vb) / 2 + 3.5, f"{agree}/3", 8 if compact else 9,
               "ch0" if agree < 3 else "muted", "middle", weight="700" if agree < 3 else None)
    valid = []
    for k in range(4):
        valid += [(rise[2 * k + 1], 1), (rise[2 * k + 2], 0)]
    d.path(digital_path(x0, x1, valid, *rows["VALID"], idle=0), "ch2", 1.4, join="miter")

    graticule(d, x0, x1, *grid, separators=seps, span=(label_x - 10, x1))
    colors = dict(CLK="ch3", M1="ch1", M2="ch1", M3="ch1", VOTE="ch0", VALID="ch2")
    for name, (a, b) in rows.items():
        channel_label(d, label_x, (a + b) / 2, name, None, colors[name], 9 if compact else 10)

    readout(d, 228 if compact else 207, "MAJORITY", "2 of 3 lanes decide" if compact else "2 of 3 lanes decide each output",
            "the vote registers on the next rising edge", compact)
    return d.finish()


def capture_cli(theme, compact=False):
    w, h = (360, 188) if compact else (840, 220)
    d = Drawing(w, h, theme, "Capture 004: a zindi-cli session",
                "Illustrative console capture. Each zindi-cli command returns one JSON document; an expired login "
                "returns a typed error on stderr and exits with code 3.")
    capture_frame(d, 4, "CONSOLE", "ILLUSTRATIVE" if compact else "ILLUSTRATIVE SESSION", compact,
                  19 if compact else 20, (8, 28, 344, 128) if compact else (12, 30, 816, 156))
    lines = []
    for entry in CLI_SESSION:
        lines.append(("cmd", entry.get("short", entry["command"]) if compact else entry["command"], None))
        if not compact or "short_output" in entry:
            lines.append(("out", entry.get("short_output", entry["output"]) if compact else entry["output"], entry))
    lines.append(("cmd", CLI_NEXT + " _", None))

    size, pitch, y0 = (9.5, 14, 58) if compact else (10, 14.5, 47)
    px, tx = (18, 28) if compact else (28, 40)
    level_x = lambda code: 676 + code * 10
    trace, previous = [], None
    for i, (kind, text, entry) in enumerate(lines):
        y = y0 + i * pitch
        if kind == "cmd":
            d.text(px, y, "$", size, "ch1", weight="700")
            d.text(tx, y, text, size, "ink")
            continue
        error = entry["stream"] == "stderr"
        d.text(px if compact else tx, y, text, size, "ch0" if error else "muted")
        if compact:
            d.text(342, y, str(entry["exit"]), size, "ch0" if error else "muted", "end", weight="700" if error else None)
        else:
            x = level_x(entry["exit"])
            if previous is not None and previous != x:
                trace.append(f"V{num(y - 9)}H{x}")
            previous = x
            d.circle(x, y - 3.5, 2.2, "ch2")
            d.text(x + 10, y, str(entry["exit"]), 9.5, "ch0" if error else "muted", weight="700" if error else None)
            d.text(744, y, entry["stream"], 9.5, "ch0" if error else "muted")
    if compact:
        d.text(342, y0 - pitch, "EXIT", 8, "ch2", "end", 1, "700")
    else:
        d.path("M650 34V182", "grid_major", 1)
        d.text(666, y0, "EXIT", 9.5, "ch2", spacing=1, weight="700")
        d.text(744, y0, "STREAM", 9, "muted", spacing=1)
        d.path(f"M{level_x(0)} {y0 + 7}" + "".join(trace) + f"V{num(y0 + (len(lines) - 1) * pitch)}", "ch2", 1.4, join="miter")

    readout(d, 174 if compact else 207, "EXIT 3", "= AUTH_REQUIRED | AUTH_EXPIRED", "one JSON document per command", compact, "ch0")
    return d.finish()


# Section markers -------------------------------------------------------------------------------------

MARKERS = {1: ("uart", "ch0"), 2: ("clock", "ch1"), 3: ("bus", "ch2"), 4: ("analog", "ch3"), 5: ("pulse", "ch0")}


def marker(n, theme, compact=False):
    w, h = (360, 36) if compact else (840, 40)
    kind, color = MARKERS[n]
    d = Drawing(w, h, theme, f"Section marker M{n}", "Decorative divider: a marker flag and a short signal trace.")
    mid, x0, x1 = h / 2, 58, w - 8
    hi, lo = mid - 7, mid + 7
    d.path(f"M10 3V{h - 3}", color, 1, extra='stroke-dasharray="2 3"')
    d.path(f"M10 {mid - 8}H40L46 {mid}L40 {mid + 8}H10Z", color, 1, fill=color)
    d.text(15, mid + 3.5, f"M{n}", 10, "screen", spacing=0.8, weight="700")
    style = 'stroke-opacity=".85"'
    if kind == "uart":
        path = digital_path(x0, x1, uart_transitions(uart_bits(str(n)), x0 + 40, 9), hi, lo)
        d.path(path, color, 1.4, join="miter", extra=style)
    elif kind == "clock":
        d.path(digital_path(x0, x1, clock_transitions(x0, x1, 12), hi, lo, idle=0), color, 1.4, join="miter", extra=style)
    elif kind == "bus":
        widths, segments, x = [90, 140, 70, 120, 100, 160, 80], [], x0
        while x < x1 - 20:
            nxt = min(x1, x + widths[len(segments) % len(widths)])
            segments.append((x, nxt, "", color))
            x = nxt
        bus(d, segments, hi, lo)
    elif kind == "analog":
        d.path(analog_path(x0, x1, lambda x: mid - 8 * exp(-(x - x0) / 220) * sin((x - x0) / 8), 2), color, 1.4, extra=style)
    else:
        d.path(digital_path(x0, x1, [(x0 + 70, 1), (x0 + 118, 0)], hi, lo, idle=0), color, 1.4, join="miter", extra=style)
    return d.finish()


def assets():
    result = {}
    for theme in PALETTES:
        for compact in [False, True]:
            suffix = f"{theme}{'-compact' if compact else ''}.svg"
            result[f"hero-{suffix}"] = hero(theme, compact)
            result[f"hero-static-{suffix}"] = hero(theme, compact, motion=False)
            result[f"documents-{suffix}"] = capture_documents(theme, compact)
            result[f"fpga-{suffix}"] = capture_fpga(theme, compact)
            result[f"cli-{suffix}"] = capture_cli(theme, compact)
            for n in MARKERS:
                result[f"marker-{n}-{suffix}"] = marker(n, theme, compact)
    return result
