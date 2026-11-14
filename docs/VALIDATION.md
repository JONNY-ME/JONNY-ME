# Implementation review

Reviewed on 14 November 2026, using the feature branch rendered by GitHub in Chrome 156. The live profile remains on `main` until the pull request is merged.

## Rendered previews

| View | Dark | Light |
| --- | --- | --- |
| Desktop, 1280px viewport | [Preview](previews/desktop-dark.png) | [Preview](previews/desktop-light.png) |
| Mobile, 390px viewport | [Preview](previews/mobile-dark.png) | [Preview](previews/mobile-light.png) |

Screenshots capture GitHub's rendered README, cropped to the article. Sticky repository navigation was hidden during capture so it does not cover the article. Reduced motion was enabled to show the settled artwork.

## Browser checks

- Light and dark modes at 320, 390, 768, and 1280px: all four images load, correct theme and compact/wide variants are selected, no document-level horizontal overflow.
- Reduced motion: the README selects static hero assets. The animated SVG's own reduced-motion CSS also disables animation when opened directly.
- Animation: the original SVG uses one 4.5-second trace animation and settles at stroke offset zero; the junction pulse ends at 4.8 seconds.
- The selected-work anchor resolves, and the background disclosure opens and exposes its project-index links.
- Name, role, prose, project destinations, and email link remain available independently of images.
- Each view loads approximately 13–16 KB of vector artwork, below the 300 KB target. Preview PNGs are review artifacts and do not load in the profile.

## Code and data checks

`python3 -m unittest discover -s tests -v` passes all 13 tests. `python3 scripts/build.py --check` confirms the committed output matches the source. The GitHub Actions check runs the same commands.

Public activity was fetched from all three configured repositories. Tests cover failed/partial refreshes retaining the last snapshot, private and empty repositories, escaped remote titles, unchanged content leaving file timestamps intact, valid SVG output, and deterministic generation. The scheduled publishing workflow activates after merge to `main`; it has not been run as a scheduled production job before publication.

The portfolio homepage, About, Achievements, project/research indexes, and every featured case-study destination returned HTTP 200. The multilingual QA repository resolved. The Zindi competition profile redirects successfully to `zindi.world`. LinkedIn returned 999 and Toptal returned 403 to automated requests; those two destinations were retained from the existing portfolio and are not claimed as independently verified.
