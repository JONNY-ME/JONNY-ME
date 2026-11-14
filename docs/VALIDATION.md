# Implementation review

Reviewed on 14 November 2026, using the `feat/bench-instrument-profile` branch rendered by GitHub in Chrome 156. The live profile remains on `main` until the pull request is merged.

## Rendered previews

| View | Dark | Light |
| --- | --- | --- |
| Desktop, 1280px viewport | [Preview](previews/desktop-dark.png) | [Preview](previews/desktop-light.png) |
| Mobile, 390px viewport | [Preview](previews/mobile-dark.png) | [Preview](previews/mobile-light.png) |

Screenshots capture GitHub's rendered README, cropped to the article. Sticky repository navigation was hidden during capture so it does not cover the article. Reduced motion was enabled to show the settled artwork.

## Browser checks

- Light and dark modes at 320, 390, 768, and 1280px: all nine images (hero, three captures, five section markers) load. Each view selects the correct theme and its compact or wide variant, with no document-level horizontal overflow.
- Reduced motion: the README selects the static hero. The animated SVG's own reduced-motion CSS also hides the shutter and stops the reveals when it is opened directly.
- Animation: the hero's sweep runs once; after it ends, the shutter has left the screen and the readout is fully visible. Locally, the settled frame matched the static hero to within one anti-aliased pixel. The animated SVG opened with reduced motion rendered identically to the static asset.
- The selected-work anchor resolves, and the background disclosure opens and exposes its project-index links.
- Name, role, prose, project destinations, and email link remain available with every image hidden.
- Each view loads about 53 KB of vector artwork on desktop and 40 KB on mobile (the static hero plus three captures and five markers), below the 300 KB target. The animated hero adds 19 KB on desktop or 13 KB on mobile in place of the static one. Preview PNGs are review artifacts and do not load in the profile.

## Code and data checks

`python3 -m unittest discover -s tests -v` passes all 19 tests. `python3 scripts/build.py --check` confirms the committed output matches the source. The GitHub Actions check runs the same commands.

New tests check the artwork's claims. The hero's UART waveform decodes back to `YOHANNES` with valid 8N1 framing, and the Δt readout matches the frame count and baud rate. Every illustrated vote is the 2-of-3 majority of its lanes. The console's exit codes match zindi-cli's documented contract. Both palettes meet the WCAG contrast thresholds set out in [the design notes](DESIGN.md). No asset loops its animation.

Profile prose, claims, and destinations are unchanged from the previous review. Only alt text and the footer changed. The research intro and activity rows also no longer use em dashes.
