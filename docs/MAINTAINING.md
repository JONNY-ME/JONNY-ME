# Maintaining the Signal Foundry

This repository is Yohannes Melese's GitHub profile. Its artwork is generated locally, and the rendered README has no external widget or font dependencies.

## Edit and build

Python 3.12 or newer is sufficient; no packages need to be installed.

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py --check
```

Edit `profile.json` for identity, project descriptions, credentials, destinations, and the public repository allowlist. Edit `templates/README.md.tmpl` for section structure. Edit `scripts/art.py` for original geometry, palettes, and motion. Commit the generated README and SVGs together with source changes. The builder is deterministic and works offline from the committed activity snapshot; `--check` never rewrites files.

The content was curated from Yohannes's portfolio. This repository has no dependency on that site's source checkout. See [content provenance and design decisions](DESIGN.md) when updating claims or project status.

## Refresh the workbench

```sh
python3 scripts/update_activity.py
python3 scripts/build.py
```

The updater requests public repository metadata and the latest default-branch commit for each explicitly configured repository. It stores only the repository name, SHA, commit date, and first line of the commit message. `GITHUB_TOKEN` is optional locally and is supplied automatically by Actions; do not put a token in a file or commit it.

The workflow runs daily at 09:17 Africa/Addis_Ababa (06:17 UTC) after it reaches `main`. GitHub schedules may be delayed. You can also run **Actions → Refresh public workbench → Run workflow** against `main`. Refreshing a feature branch is deliberately disabled.

An API error, private repository, or malformed response fails the whole refresh before replacing the snapshot. The existing profile remains visible. A genuinely empty public repository is omitted. Identical results do not write files or create commits. Remote titles are escaped before entering Markdown. The published log records commit dates, not an artificial "last active" status.

The publishing job alone has `contents: write`. It commits only the README and activity snapshot. There is no force push; if a concurrent change prevents the push, rerun the workflow. If branch protection disallows bot commits, keep the protection and use the local refresh commands on a pull request instead.

GitHub [disables scheduled workflows after 60 days of repository inactivity](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule). Re-enable the workflow in Actions if that occurs. There are no artificial keep-alive commits. Check the Actions run history for refresh failures.

## Visual review and publication

Inspect the README on its GitHub branch in both light and dark themes, at desktop and mobile widths. Confirm the browser selects compact artwork below 600px. Reduced motion should show the complete static hero. The animation runs once; project diagrams stay still. Check image-free readability, anchor links, and every public destination.

Changes to `main` are displayed on the GitHub profile. Review through a pull request first. Reverting the merge restores the prior README and artwork. Preview screenshots in this repository document the initial review; regenerate them when changing the visual design.

## Checks

The tests cover generation integrity, complete asset references, SVG validity and size, remote-content escaping, URL rejection, empty/private repositories, failed/partial refreshes, and no-change updates. They use fake API responses and never require a token. CI also checks that committed output matches the source.
