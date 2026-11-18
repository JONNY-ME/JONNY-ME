#!/usr/bin/env python3
"""Refresh publicly visible GitHub data atomically; never fetch private repository details."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from github_data import dates_between, parse_calendar, validate

ROOT = Path(__file__).resolve().parents[1]
REPOS = '''query($cursor:String) { user(login:"JONNY-ME") { createdAt repositories(first:100,after:$cursor,privacy:PUBLIC,ownerAffiliations:[OWNER],orderBy:{field:NAME,direction:ASC}) { nodes { name url isFork isPrivate stargazerCount primaryLanguage { name } languages(first:100,orderBy:{field:SIZE,direction:DESC}) { edges { size node { name } } pageInfo { hasNextPage endCursor } } } pageInfo { hasNextPage endCursor } } } }'''
LANGUAGES = '''query($name:String!,$cursor:String) { repository(owner:"JONNY-ME",name:$name) { isPrivate languages(first:100,after:$cursor,orderBy:{field:SIZE,direction:DESC}) { edges { size node { name } } pageInfo { hasNextPage endCursor } } } }'''


def request_text(request):
    for attempt in range(3):
        try:
            with urlopen(request, timeout=25) as response:
                return response.read().decode('utf-8')
        except (HTTPError, URLError, TimeoutError) as error:
            if isinstance(error, HTTPError) and error.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def graphql(query, variables):
    body = json.dumps({'query': query, 'variables': variables})
    if token := os.environ.get('GITHUB_TOKEN'):
        request = Request('https://api.github.com/graphql', data=body.encode(), headers={
            'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
            'User-Agent': 'jonny-developer-hub'})
        result = json.loads(request_text(request))
    else:
        # Local gh credentials stay in gh; their token is never read or printed.
        proc = subprocess.run(['gh', 'api', 'graphql', '--input', '-'], input=body,
                              text=True, capture_output=True, timeout=60)
        if proc.returncode:
            raise RuntimeError('GitHub metadata request failed. Check gh authentication or GITHUB_TOKEN.')
        result = json.loads(proc.stdout)
    if result.get('errors') or not result.get('data'):
        raise ValueError('GitHub returned an incomplete GraphQL response')
    return result['data']


def next_cursor(page, seen):
    if not page['hasNextPage']:
        return None
    cursor = page.get('endCursor')
    if not cursor or cursor in seen:
        raise ValueError('Incomplete or looping GitHub pagination')
    seen.add(cursor)
    return cursor


def collect_repositories(api=graphql):
    repos, seen, cursor, created = [], set(), None, None
    while True:
        user = api(REPOS, {'cursor': cursor})['user']
        created = user['createdAt']
        connection = user['repositories']
        for node in connection['nodes']:
            if node['isPrivate']:
                raise ValueError('Private repository returned in public query')
            lang = node['languages']
            languages = {edge['node']['name']: edge['size'] for edge in lang['edges']}
            visited = set()
            after = next_cursor(lang['pageInfo'], visited)
            while after:
                extra = api(LANGUAGES, {'name': node['name'], 'cursor': after})['repository']
                if extra['isPrivate']:
                    raise ValueError('Repository visibility changed during refresh')
                lang = extra['languages']
                for edge in lang['edges']:
                    if edge['node']['name'] in languages:
                        raise ValueError('Duplicate language in paginated response')
                    languages[edge['node']['name']] = edge['size']
                after = next_cursor(lang['pageInfo'], visited)
            repos.append(dict(name=node['name'], url=node['url'], fork=node['isFork'],
                              stars=node['stargazerCount'], primary_language=(node['primaryLanguage'] or {}).get('name'),
                              languages=dict(sorted(languages.items()))))
        cursor = next_cursor(connection['pageInfo'], seen)
        if cursor is None:
            break
    return created, sorted(repos, key=lambda r: r['name'].lower())


def public_calendar(year):
    # Deliberately unauthenticated: only counts visible on the public profile.
    url = f'https://github.com/users/JONNY-ME/contributions?from={year}-01-01&to={year}-12-31'
    html = request_text(Request(url, headers={'User-Agent': 'jonny-developer-hub', 'Accept-Language': 'en-US,en;q=0.9'}))
    return parse_calendar(html, year)


def collect(as_of, api=graphql, calendar_fetch=public_calendar):
    created, repos = collect_repositories(api)
    first = date.fromisoformat(created[:10])
    years = range(first.year, as_of.year+1)
    history = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for days in pool.map(calendar_fetch, years):
            history.update(days)
    expected = [d.isoformat() for d in dates_between(first, as_of)]
    if not all(day in history for day in expected):
        raise ValueError('Incomplete public contribution history')
    return validate(dict(schema_version=1, as_of=as_of.isoformat(), created_at=created,
                         contributions={d: history[d] for d in expected}, repositories=repos))


def refresh(root=ROOT, as_of=None, api=graphql, calendar_fetch=public_calendar, dry_run=False):
    snapshot = collect(as_of or datetime.now(timezone.utc).date(), api, calendar_fetch)
    profile = json.loads((root / 'profile.json').read_text())
    available = {r['name'] for r in snapshot['repositories']}
    if any(p['repository'] not in available for p in profile['projects']):
        raise ValueError('A featured repository is no longer public or is missing')
    if dry_run:
        return False
    content = json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n'
    path = root / 'data/github.json'
    if path.exists() and path.read_text() == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(content)
    temporary.replace(path)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', type=date.fromisoformat, help='UTC date; defaults to today')
    parser.add_argument('--dry-run', action='store_true', help='Fetch and validate without writing')
    args = parser.parse_args()
    try:
        changed = refresh(as_of=args.as_of, dry_run=args.dry_run)
        print('Public GitHub data validated; no files written.' if args.dry_run else
              'GitHub snapshot updated.' if changed else 'No GitHub data changes.')
    except Exception as error:
        print(f'Refresh failed; previous snapshot retained: {error}', file=sys.stderr)
        sys.exit(1)
