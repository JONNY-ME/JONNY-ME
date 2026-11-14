# YM-01 Bench

The profile is one session on a fictional mixed-signal analyzer, the YM-01. Every image is a capture on that instrument: the hero decodes a name from a serial line, and each project is shown in the instrument view that best explains it. The theme comes from Yohannes's own path, from electronics into machine learning: turning raw signals into something that can be read and checked.

YM-01 is invented for this profile. It has no vendor name, logo, or interface copied from a real instrument.

## Captures

**001 · Hero.** A logic-analyzer screen with four channels. `D0 TX` carries a genuine 8N1 UART encoding of `YOHANNES` at 9600 baud: idle high, a start bit, eight data bits sent least-significant first, and a stop bit. The timebase is 1 ms per division, so the eight frames span a true 8.33 divisions, and the A/B cursors read Δt = 8.33 ms. Each frame carries a decode box with its character and byte (`Y 0x59`). `A1 LEARNING` is a deterministic analog trace that starts noisy and settles. `B2 SOFTWARE` is a bus stepping through parse, test, build, and ship. `D3 HARDWARE` is a clock. The status bar names Addis Ababa. A test decodes the waveform back to the name.

**002 · Probe view (document extraction).** A stylised tax page with four fields is probed like a circuit board. The leads run into channels that show the pipeline's logic: rules extract three fields, the LLM fallback fires only for the smudged one, the arithmetic check goes high when A + B = Σ, and the confidence trace dips under its 0.80 threshold at the smudged field, raising a review flag. The readout names the audit trail.

**003 · Timing view (FPGA ensemble).** A digital timing diagram with a clock, three model lanes, a vote bus, and a valid strobe. Each lane outputs a class per cycle; in two cycles one lane disagrees (shaded), and the vote, registered one clock later, records the 2-of-3 majority. A test checks that every vote is the majority of its lanes. The diagram makes no claims about bit-widths, clock rates, or accuracy.

**004 · Console view (zindi-cli).** A terminal session using real commands and JSON shapes from the [zindi-cli README](https://github.com/JONNY-ME/zindi-cli): `use`, `data download`, `submissions submit`, and `leaderboard --mine`, which fails with `AUTH_EXPIRED` on stderr. An exit-code channel steps from 0 to 3, matching the README's exit-code table. A test checks the code against that table.

**Section markers.** Each numbered README section is preceded by a decorative strip (`alt=""`): a marker flag, M1 to M5, and a short trace of a different signal type.

Projects 002 to 004 are labelled *illustrative* on the artwork. Their values show how each system behaves; they are not measurements. The same explanations are in the Markdown and alt text, so nothing depends on the images.

## Visual system

Every capture shares the same instrument chrome: a bezel, a status bar (`YM-01 · CAPTURE 00N · MODE`), a screen with a graticule painted over the traces as on a real scope, channel labels in a left gutter, and a readout bar. Dark mode is the instrument screen; light mode is chart paper. Both use the same geometry.

| Token | Dark | Light | Notes |
| --- | --- | --- | --- |
| bezel | `#212722` | `#ECE8DE` | portfolio surface |
| screen | `#141915` | `#FCFAF5` | portfolio elevated (light) |
| ink / muted | `#F3F0E7` / `#A4AD9E` | `#242823` / `#5C6057` | portfolio text |
| ch0 terracotta | `#E89A7F` | `#9F452C` | portfolio accent |
| ch1 sage | `#A3C89E` | `#31653F` | portfolio success |
| ch2 amber | `#E3B866` | `#855F12` | instrument only |
| ch3 steel | `#94B8C9` | `#2F5F78` | instrument only |

The palette is shared with yohannesmelese.com, so the profile and the site read as one brand. A test enforces WCAG contrast: text colours reach 4.5:1 on the bezel and the screen, flag labels reach 4.5:1 on their fills, and traces reach 3:1 against GitHub's own page backgrounds. Text uses the system monospace stack; there are no web fonts. Symbols that monospace fonts often lack (status LEDs, check marks, flags, the cursor) are drawn as shapes.

Sizes: hero 840 × 340, compact 360 × 330; captures 840 × 220, compact 360 × 176 to 280; markers 840 × 40, compact 360 × 36. Compact variants are separate compositions, not scaled copies, so text stays legible at phone widths.

## Motion

Only the hero moves, and only once (3.9 seconds in total):

1. The status reads ARMED and a trigger marker sits on the first start bit.
2. From 0.3 s to 3.3 s a playhead sweeps left to right. A screen-coloured shutter moves with it (a `transform` animation), revealing the traces exactly at the playhead's position.
3. Each decode box fades in as the playhead passes the end of its frame; Python computes each delay from the frame's position.
4. At 3.4 s the cursors, Δt, and decoded name appear and the status switches to STOP · SINGLE, as a single-shot capture would.

The settled frame is identical to the static hero. Under `prefers-reduced-motion: reduce`, the `<picture>` element selects `hero-static-*`, which has no animation rules; this does not rely on the media query reaching inside an embedded image. The animated SVG also carries its own reduced-motion CSS as a second safeguard. Nothing loops, and no content depends on animation. The artwork contains no scripts, embedded HTML, bitmaps, external fonts, or network calls.

## Content provenance

The implementation draws from the local portfolio's current About page, project metadata, skills, achievements, and project write-ups. Public destinations are listed below. The current About page takes precedence over the older CV for career status: Ethronics is described as a former leadership role. The README avoids inconsistent dates, unverified aggregate counts, and headline performance claims.

- [About and education](https://yohannesmelese.com/about): interdisciplinary education, Toptal, Ethronics, Turing, ASTU, and CSEC-ASTU.
- [Achievements](https://yohannesmelese.com/achievements): academic honors, UmojaHack, and EtCPC.
- [Document extraction](https://yohannesmelese.com/projects/tax-document-ocr): deterministic extraction, LLM fallback, validation, and traceability.
- [FPGA ensemble networks](https://yohannesmelese.com/projects/fpga-ensemble-networks): model parallelism, quantization, and voting.
- [Zindi CLI](https://github.com/JONNY-ME/zindi-cli): a public software example connecting the competition workflow; the console capture follows its README.
- [Research portfolio](https://yohannesmelese.com/research): speech recognition, multilingual QA, and historical handwriting; shown as research/experiments, not deployed services.

## References

[Simon Willison](https://github.com/simonw/simonw) demonstrates useful self-updating profile content, which the workbench log follows. Nothing is copied from it.

## Originality

The instrument, layouts, and code were created for this profile. They need no image or font attribution. Future factual edits should be reviewed against the linked sources, and new artwork should keep the light/dark and compact variants and stay within the instrument's vocabulary: channels, captures, decodes, and readouts.
