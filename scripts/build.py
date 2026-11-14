#!/usr/bin/env python3
"""Deterministically generate the profile; --check never writes files."""
import argparse
import json
import re
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

from art import assets

ROOT = Path(__file__).resolve().parents[1]


def safe_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in {"https", "mailto"} or any(c in value for c in '\n\r<>"'):
        raise ValueError(f"Invalid profile URL: {value!r}")
    if parsed.scheme == "https" and (not parsed.hostname or parsed.username):
        raise ValueError("HTTPS URL must have a hostname and no credentials")
    return value


def md_text(value):
    # Remote commit titles are untrusted data, never Markdown/HTML instructions.
    value = " ".join(value.split())
    value = escape(value, quote=False)
    return re.sub(r'([\\`*_{}\[\]()#+.!|~])', r'\\\1', value)


def link(label, url):
    return f"[{label}](<{safe_url(url)}>)"


def picture(name, alt):
    reduced = ""
    if name == "hero":
        for compact in [True, False]:
            width_query = "(max-width: 600px) and " if compact else ""
            suffix = "-compact" if compact else ""
            for theme in ["dark", "light"]:
                reduced += f'  <source media="{width_query}(prefers-reduced-motion: reduce) and (prefers-color-scheme: {theme})" srcset="assets/hero-static-{theme}{suffix}.svg">\n'
    fallback = "hero-static" if name == "hero" else name
    return f'''<picture>
{reduced}  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/{name}-dark-compact.svg">
  <source media="(max-width: 600px) and (prefers-color-scheme: light)" srcset="assets/{name}-light-compact.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/{name}-light.svg">
  <img src="assets/{fallback}-light.svg" width="840" alt="{escape(alt, quote=True)}">
</picture>'''


def activity_markdown(snapshot, repositories):
    items = snapshot["entries"]
    if not items:
        return "Public repository updates will appear after the first successful refresh."
    rows = []
    for item in items:
        if item["repository"] not in repositories:
            raise ValueError("Activity repository is not allowlisted")
        if not re.fullmatch(r"[0-9a-f]{40,64}", item["sha"]):
            raise ValueError("Invalid commit SHA")
        date = item["date"][:10]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            raise ValueError("Invalid commit date")
        repo = item["repository"]
        url = f"https://github.com/{repo}/commit/{item['sha']}"
        rows.append(f"- **{date}** · {link(md_text(repo.split('/')[1]), 'https://github.com/' + repo)} · {link(md_text(item['title']), url)}")
    return "\n".join(rows)


def outputs(root=ROOT):
    profile = json.loads((root / "profile.json").read_text())
    snapshot = json.loads((root / "data/activity.json").read_text())
    links = profile["links"]
    projects = []
    for item in profile["projects"]:
        destinations = [link("Read the case study ↗", item["url"])]
        if item.get("repository"):
            destinations.insert(0, link("Explore the code ↗", item["repository"]))
        projects.append(f"### {item['title']}\n\n{picture(item['id'], item['alt'])}\n\n**{item['name']}**\n\n{item['description']}\n\n`{item['stack']}`\n\n" + " · ".join(destinations))
    values = dict(profile)
    values.update(
        navigation=f"{link('Portfolio ↗', links['portfolio'])} · [Selected work ↓](#01--selected-systems) · {link('Contact ↗', links['email'])}",
        hero=picture("hero", "YM-01 Bench capture: a UART signal decodes byte by byte into YOHANNES, above learning, software, and hardware channels. A conceptual illustration of my engineering practice."),
        projects="\n\n".join(projects),
        research="\n\n".join(f"**{link(r['title'], r['url'])}**  \n{r['description']}" for r in profile["research"]),
        foundations="\n\n".join(profile["foundations"]),
        index_links=" · ".join([link("All projects", links['portfolio'] + '/projects'), link("Research", links['portfolio'] + '/research'), link("About & experience", links['portfolio'] + '/about'), link("Competition portfolio", links['zindi'])]),
        activity=activity_markdown(snapshot, profile["activity_repositories"]),
        contact=" · ".join(link(label, links[key]) for label, key in [("Email me ↗", "email"), ("Portfolio", "portfolio"), ("LinkedIn", "linkedin"), ("Toptal", "toptal")]),
        **{f"marker_{n}": picture(f"marker-{n}", "") for n in range(1, 6)},
    )
    readme = Template((root / "templates/README.md.tmpl").read_text()).substitute(values)
    generated = {root / "README.md": readme}
    generated.update({root / "assets" / name: content for name, content in assets().items()})
    return generated


def build(check=False, root=ROOT):
    stale = []
    for path, content in outputs(root).items():
        if path.exists() and path.read_text() == content:
            continue
        stale.append(str(path.relative_to(root)))
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    if check and stale:
        raise SystemExit("Generated files need updating: " + ", ".join(stale))
    return stale


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = build(args.check)
    print("Generated output is current." if args.check else f"Updated {len(changed)} files.")
