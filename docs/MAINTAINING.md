# Maintaining Jonny's profile

The README and SVGs are generated from curated profile content and a complete, dated GitHub snapshot. Python 3.12+ is sufficient for offline generation; no packages or image services are required.

## Edit and build

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py --check
```

Edit `profile.json` for identity, selected repositories, tool labels, and contact links. Edit the template for structure and `scripts/art.py` for vector artwork. Commit source and generated output together. The builder removes obsolete generated SVGs at the root of `assets/`; vendored icons under `assets/icons/` are preserved. `--check` never writes or deletes files.

## Refresh public GitHub data

```sh
python3 scripts/update_activity.py
python3 scripts/build.py
```

Locally, the updater uses the authenticated `gh` CLI for public repository metadata, unless `GITHUB_TOKEN` is supplied. It never reads or prints the CLI's token. In Actions it uses the built-in token. `--dry-run` fetches and validates without writing; `--as-of YYYY-MM-DD` can freeze a UTC reporting date for reproducibility.

Repository metadata comes from GitHub GraphQL, explicitly filtered to public repositories owned by JONNY-ME. Repository and language connections are fully paginated. No private repository names, descriptions, code, or commit messages are requested or saved.

Contribution counts come from the **unauthenticated public GitHub contribution calendar**, one calendar year at a time, starting with the account's creation year. This deliberately uses the same visibility as a signed-out visitor. Anonymous counts from private work appear only when GitHub already displays them publicly. The parser joins dated calendar cells to their count tooltips and requires every day of each year, including leap days. Missing counts, changed markup, incomplete responses, and HTTP/GraphQL errors fail the refresh; they never turn missing data into zero activity.

The full snapshot is validated before its atomic replacement. If a featured repository is absent or no longer public, the refresh fails for review rather than publishing a broken card. The previous published README and images remain available on every failure. Identical same-date snapshots leave the file unchanged.

## Metric definitions

- **Current streak:** consecutive calendar days with a positive contribution count ending today or yesterday. No weekend exclusions. The reporting date is UTC, and the dated calendar cells are used as GitHub publishes them.
- **Longest streak:** the longest consecutive run across all available years, including year boundaries. This is not restricted to the visible calendar.
- **Contributions:** the sum from reporting date minus 364 days through reporting date, inclusive.
- **Stars received:** sum of stars on owned public repositories, excluding forks.
- **Public repos:** all owned public repositories, including forks.
- **Languages:** GitHub-reported bytes in owned public repositories, excluding forks and this profile repository. Show the top six and combine the rest into Other. Notebook bytes remain Jupyter Notebook; this is repository composition, not an estimate of language proficiency.

`data/github.json` contains only the snapshot date, account creation date, public daily counts, and necessary public repository/language metadata. It is the single source for the README, graphs, cards, and accessible text.

## Automation and publication

The refresh runs at **09:17 Africa/Addis_Ababa (06:17 UTC)** daily and can be triggered from **Actions → Refresh Jonny GitHub profile → Run workflow** on `main`. A reporting-date change is meaningful even when activity does not change: streak grace and the 365-day window must advance. Generated commits use `github-actions[bot]`, not the profile owner's identity.

Only the publishing job has `contents: write`; it commits the snapshot, README, and generated SVGs together. There are no force pushes. A concurrent main-branch change may cause a safe push failure; rerun the workflow. If branch protection prohibits bot writes, retain the protection and refresh through a normal pull request.

CI checks offline generation and unit tests. On source pushes, a separate read-only job also exercises the public fetch with the Actions token, without publishing or changing files. A failed live check reports a source/API problem; the offline checks remain separately visible.

GitHub may delay schedules and [disable them after 60 days of repository inactivity](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule). Re-enable in Actions if needed; inspect run history for failures. The contribution parser intentionally fails closed when GitHub changes its HTML markup, so update it and its fixtures if required.

Review a branch's actual GitHub README in both themes and on narrow screens before merging. Merge to `main` publishes the profile. Reverting the merge restores the earlier version. See [rendered previews and validation](VALIDATION.md).
