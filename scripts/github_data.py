"""Public GitHub data, calendar validation, and deterministic profile metrics."""
from datetime import date, timedelta
from html.parser import HTMLParser
import calendar
import re


def dates_between(start, end):
    while start <= end:
        yield start
        start += timedelta(days=1)


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.tips = {}, {}
        self.tip_id, self.parts = None, []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'td' and 'data-date' in attrs:
            key = attrs.get('id')
            if not key or key in self.cells:
                raise ValueError('Missing or duplicate calendar cell ID')
            self.cells[key] = attrs['data-date']
        if tag == 'tool-tip':
            self.tip_id, self.parts = attrs.get('for'), []

    def handle_data(self, value):
        if self.tip_id:
            self.parts.append(value)

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tip_id:
            self.tips[self.tip_id] = ' '.join(''.join(self.parts).split())
            self.tip_id = None


def parse_calendar(html, year):
    parser = CalendarParser()
    parser.feed(html)
    days = {}
    for cell, day in parser.cells.items():
        parsed = date.fromisoformat(day)
        if parsed.year != year:
            continue
        if day in days:
            raise ValueError('Duplicate contribution date')
        text = parser.tips.get(cell, '')
        match = re.match(r'^(No|[\d,]+) contributions? on ', text)
        if not match:
            raise ValueError(f'Missing or unrecognized count for {day}')
        days[day] = 0 if match[1] == 'No' else int(match[1].replace(',', ''))
    expected = 366 if calendar.isleap(year) else 365
    if len(days) != expected:
        raise ValueError(f'Incomplete calendar for {year}: {len(days)}/{expected} days')
    return days


def validate(snapshot):
    if snapshot['schema_version'] != 1:
        raise ValueError('Unsupported snapshot version')
    today = date.fromisoformat(snapshot['as_of'])
    first = date.fromisoformat(snapshot['created_at'][:10])
    if today < first:
        raise ValueError('Snapshot predates the account')
    days = snapshot['contributions']
    expected = {d.isoformat() for d in dates_between(first, today)}
    if set(days) != expected:
        raise ValueError('Contribution history has missing or future dates')
    if any(type(n) is not int or n < 0 for n in days.values()):
        raise ValueError('Contribution counts must be nonnegative integers')
    names = set()
    for repo in snapshot['repositories']:
        name = repo['name']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or name in names:
            raise ValueError('Invalid or duplicate repository name')
        names.add(name)
        if repo['url'] != f'https://github.com/JONNY-ME/{name}':
            raise ValueError('Unexpected repository destination')
        if type(repo['stars']) is not int or repo['stars'] < 0 or type(repo['fork']) is not bool:
            raise ValueError('Invalid repository metadata')
        if any(type(n) is not int or n < 0 for n in repo['languages'].values()):
            raise ValueError('Invalid language bytes')
    return snapshot


def metrics(snapshot):
    validate(snapshot)
    today = date.fromisoformat(snapshot['as_of'])
    days = snapshot['contributions']
    ordered = sorted(days)
    longest = run = 0
    for day in ordered:
        run = run + 1 if days[day] else 0
        longest = max(longest, run)
    end = today if days.get(today.isoformat(), 0) else today - timedelta(days=1)
    current = 0
    while days.get(end.isoformat(), 0):
        current += 1
        end -= timedelta(days=1)
    recent = [(d.isoformat(), days.get(d.isoformat(), 0)) for d in dates_between(today-timedelta(days=364), today)]
    repos = snapshot['repositories']
    languages = {}
    for repo in repos:
        if repo['fork'] or repo['name'].lower() == 'jonny-me':
            continue
        for name, count in repo['languages'].items():
            languages[name] = languages.get(name, 0) + count
    ranked = sorted(languages.items(), key=lambda pair: (-pair[1], pair[0]))
    top = ranked[:6]
    if len(ranked) > 6:
        top.append(('Other', sum(count for _, count in ranked[6:])))
    return dict(current=current, longest=longest, contributions=sum(n for _, n in recent),
                stars=sum(r['stars'] for r in repos if not r['fork']), repositories=len(repos),
                recent=recent, languages=top, language_total=sum(languages.values()))
