#!/usr/bin/env python3
"""Generate the Jonny profile from a complete offline snapshot. --check never writes."""
import argparse
import json
import re
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

from art import assets
from github_data import metrics

ROOT = Path(__file__).resolve().parents[1]


def safe_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in {'https','mailto'} or any(c in value for c in '\n\r<>"'):
        raise ValueError('Invalid profile URL')
    if parsed.scheme == 'https' and (not parsed.hostname or parsed.username):
        raise ValueError('HTTPS URL must have a hostname and no credentials')
    return value


def md_text(value):
    return re.sub(r'([\\`*_{}\[\]()#+.!|~])',r'\\\1',escape(' '.join(value.split()),quote=False))


def link(label,url):return f'[{label}](<{safe_url(url)}>)'


def picture(name,alt,width=840):
    sources=[]
    if name=='hero':
        for compact in [True,False]:
            for theme in ['dark','light']:
                media=('(max-width: 600px) and ' if compact else '')+f'(prefers-reduced-motion: reduce) and (prefers-color-scheme: {theme})'
                sources.append((media,f"hero-static-{theme}{'-compact' if compact else ''}.svg"))
    for compact in [True,False]:
        for theme in ['dark','light']:
            media=('(max-width: 600px) and ' if compact else '')+f'(prefers-color-scheme: {theme})'
            sources.append((media,f"{name}-{theme}{'-compact' if compact else ''}.svg"))
    source_html='\n'.join(f'  <source media="{media}" srcset="assets/{filename}">' for media,filename in sources)
    fallback='hero-static' if name=='hero' else name
    return f'<picture>\n{source_html}\n  <img src="assets/{fallback}-light.svg" width="{width}" alt="{escape(alt,quote=True)}">\n</picture>'


def outputs(root=ROOT):
    profile=json.loads((root/'profile.json').read_text())
    snapshot=json.loads((root/'data/github.json').read_text())
    m=metrics(snapshot);links=profile['links']
    repos={r['name']:r for r in snapshot['repositories']}
    cards=[]
    for item in profile['projects']:
        repo=repos[item['repository']]
        alt=f"{item['title']}. {item['description']} {repo['stars']} stars. {repo['primary_language'] or 'Code'}."
        cards.append(f'<a href="{escape(safe_url(repo["url"]),quote=True)}">{picture("repo-"+item["id"],alt,404)}</a>')
    values=dict(profile)
    values.update(
        hero=picture('hero',f"Jonny — Yohannes Melese. AI, software, electronics. {m['contributions']:,} contributions in the last 365 days, updated {snapshot['as_of']}."),
        navigation=' &nbsp; / &nbsp; '.join([link('Portfolio ↗',links['portfolio']),link('Email ↗',links['email']),link('LinkedIn ↗',links['linkedin']),link('Toptal ↗',links['toptal'])]),
        stats=picture('stats',f"Current streak: {m['current']} days. Longest streak: {m['longest']} days. Contributions in the last 365 days: {m['contributions']:,}. Stars received: {m['stars']}. Public repositories: {m['repositories']}."),
        tools=picture('tools','Tools I work with: '+', '.join(t['label'] for t in profile['tools'])),
        languages=picture('languages','Public repository languages by bytes, excluding forks and this profile: '+(', '.join(f'{name} {100*size/m["language_total"]:.1f}%' for name,size in m['languages']) if m['language_total'] else 'No language data')),
        cards='<p>\n'+'\n'.join(cards)+'\n</p>',
        case_studies=' · '.join([link('Document AI',links['portfolio']+'/projects/tax-document-ocr'),link('FPGA research',links['portfolio']+'/projects/fpga-ensemble-networks'),link('All projects ↗',links['portfolio']+'/projects')]),
        research_links=', '.join(link(r['title'],r['url']) for r in profile['research']),
        foundations='\n\n'.join(profile['foundations']),
        contact=' · '.join(link(label,links[key]) for label,key in [('Email me ↗','email'),('Portfolio','portfolio'),('LinkedIn','linkedin'),('Toptal','toptal')]),
        stat_text=f"As of **{snapshot['as_of']}**: **{m['current']} days** current streak; **{m['longest']} days** longest streak; **{m['contributions']:,}** contributions in the last 365 days; **{m['stars']}** stars received; **{m['repositories']}** public repositories.",
    )
    generated={root/'README.md':Template((root/'templates/README.md.tmpl').read_text()).substitute(values)}
    generated.update({root/'assets'/name:value for name,value in assets(profile,snapshot,root).items()})
    return generated


def build(check=False,root=ROOT):
    generated=outputs(root);changed=[]
    # Only root-level SVGs are generated. Vendored icons live in assets/icons/.
    obsolete=set((root/'assets').glob('*.svg'))-set(generated)
    for path in sorted(obsolete):
        changed.append(str(path.relative_to(root)))
        if not check:path.unlink()
    for path,content in generated.items():
        if path.exists() and path.read_text()==content:continue
        changed.append(str(path.relative_to(root)))
        if not check:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content)
    if check and changed:raise SystemExit('Generated output differs: '+', '.join(changed))
    return changed


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    changed=build(args.check)
    print('Generated output is current.' if args.check else f'Updated {len(changed)} generated files.')
