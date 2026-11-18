# Jonny developer hub

A compact, visual GitHub profile for Yohannes Melese, branded **Jonny**. The focus is contribution activity, useful repositories, and tools. The earlier engineering-instrument artwork and long case-study sections have been replaced.

## Identity and composition

The Jonny wordmark is original vector lettering, drawn in `scripts/art.py`. It uses warm ivory over deep ink, with a copper terminal dot. The light version uses ink lettering on warm ivory. The companion colors are copper and teal, carried through the contribution field, streak panel, tool icons, and repository cards.

The identity and contribution calendar share a single hero. Below it: a short introduction and contact links, the GitHub statistics, tools and language composition, four linked repository cards, current research links, and a small invitation to connect. Career and education details are inside an expandable section.

Each diagram is an SVG with local geometry. The wordmark is independent of fonts; other labels use system fonts. Vendored Simple Icons paths are embedded into the tool strip. See `assets/icons/SOURCE.json` and the accompanying CC0 license for the exact upstream source. Brand names and logos belong to their respective owners.

## Real activity

The contribution grid represents exactly 365 dated counts. Tile intensity bins are 0, 1–4, 5–9, 10–19, and 20+ contributions. These are the same actual counts used in the contribution total and streak calculations; the visual is not synthetic activity. A copper scan passes over the field while tile fills remain unchanged.

The desktop loop is 18 seconds: approximately six seconds of motion and twelve seconds at rest. Narrow screens divide the calendar into two chronological panels. Separate static SVGs are selected under reduced motion; the animated SVG also has an internal media-query safeguard.

Current and longest streaks have large dedicated numbers. Contributions are labeled with their 365-day window. Stars and repository counts have distinct definitions; see the maintenance guide. Language composition keeps Jupyter Notebook as a category and measures repository bytes, separately from the curated tools strip.

## Responsive behavior

The wide hero is 840 × 368. The narrow hero is 360 × 460 with the wordmark, a smaller identity line, and two calendar panels. Statistics rearrange from five columns to readable rows. The tool strip uses four columns on mobile; language labels become a single column.

Repository cards are individual links, 404 pixels wide on desktop, and naturally wrap into one column when there is insufficient room. Compact assets use larger text and 360 × 172 compositions. No essential links live inside an embedded SVG.

All artwork has alt text and SVG titles/descriptions. The plain-text statistics disclosure repeats the numbers and definitions; normal Markdown contains identity, project destinations, and contact links. Themes and reduced motion use GitHub-supported picture sources.

## Sources

Identity, career, skills, and research interests were curated from Yohannes's existing portfolio. Project links lead to their public repositories or the existing portfolio case studies. GitHub numbers come from the updater's complete public snapshot.

The streak rules match the common daily-streak convention exemplified by [GitHub Readme Streak Stats](https://github.com/DenverCoder1/github-readme-streak-stats): consecutive positive-count days, with an unfinished current day allowed. No code or graphics from that project are copied. All data panels and the lettering are original to this profile.
