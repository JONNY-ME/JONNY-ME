import calendar
from datetime import date, timedelta
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import art
import build
import github_data as data
import update_activity as updater


def repo(name='zindi-cli',fork=False,stars=2,languages=None):
    return dict(name=name,url='https://github.com/JONNY-ME/'+name,fork=fork,stars=stars,
                primary_language='Python',languages=languages or {'Python':100})


def snapshot(start='2024-01-01',end='2024-01-04',counts=None,repos=None):
    days={d.isoformat():0 for d in data.dates_between(date.fromisoformat(start),date.fromisoformat(end))}
    days.update(counts or {})
    return dict(schema_version=1,created_at=start+'T12:00:00Z',as_of=end,contributions=days,
                repositories=repos if repos is not None else [repo()])


def calendar_html(year):
    return ''.join(f'<td id="d{i}" data-date="{day}"></td><tool-tip for="d{i}">{"1,234 contributions" if i==0 else "1 contribution" if i==1 else "No contributions"} on a date.</tool-tip>'
                   for i,day in enumerate(data.dates_between(date(year,1,1),date(year,12,31))))


def api_node(name='zindi-cli',private=False,more_languages=False):
    return dict(name=name,url=f'https://github.com/JONNY-ME/{name}',isFork=False,isPrivate=private,
                stargazerCount=2,primaryLanguage={'name':'Python'},languages={
                'edges':[{'size':100,'node':{'name':'Python'}}],
                'pageInfo':{'hasNextPage':more_languages,'endCursor':'lang1' if more_languages else None}})


def fake_api(query,variables):
    return {'user':{'createdAt':'2024-01-01T00:00:00Z','repositories':{'nodes':[api_node()],
            'pageInfo':{'hasNextPage':False,'endCursor':None}}}}


class MetricTests(unittest.TestCase):
    def test_today_and_yesterday_grace(self):
        s=snapshot(counts={'2024-01-02':2,'2024-01-03':1})
        self.assertEqual(data.metrics(s)['current'],2)
        s['contributions']['2024-01-04']=3
        self.assertEqual(data.metrics(s)['current'],3)

    def test_gap_breaks_current_and_preserves_longest(self):
        m=data.metrics(snapshot(counts={'2024-01-01':1,'2024-01-02':4}))
        self.assertEqual((m['current'],m['longest']),(0,2))

    def test_year_boundary_and_leap_day(self):
        s=snapshot('2023-12-30','2024-03-01')
        s['contributions']={day:1 for day in s['contributions']}
        m=data.metrics(s)
        self.assertEqual(m['current'],63)
        self.assertEqual(m['longest'],63)

    def test_zero_history(self):
        m=data.metrics(snapshot(repos=[]))
        self.assertEqual((m['current'],m['longest'],m['stars'],m['repositories']),(0,0,0,0))
        self.assertEqual(m['languages'],[])

    def test_longest_is_not_limited_to_display_year(self):
        s=snapshot('2020-01-01','2024-01-04')
        for i in range(80):s['contributions'][(date(2020,1,1)+timedelta(days=i)).isoformat()]=1
        m=data.metrics(s)
        self.assertEqual(m['longest'],80)
        self.assertEqual(m['contributions'],0)
        self.assertEqual(len(m['recent']),365)

    def test_language_denominator_and_fork_exclusions(self):
        s=snapshot(repos=[repo(languages={'Jupyter Notebook':90,'Python':10}),repo('fork',True,50,{'Java':1000}),repo('JONNY-ME',False,3,{'Python':500})])
        m=data.metrics(s)
        self.assertEqual(m['language_total'],100)
        self.assertEqual(m['languages'],[('Jupyter Notebook',90),('Python',10)])
        self.assertEqual((m['stars'],m['repositories']),(5,3))

    def test_top_six_and_other_preserve_total(self):
        s=snapshot(repos=[repo(languages={f'L{i}':i for i in range(1,9)})])
        m=data.metrics(s)
        self.assertEqual(m['languages'][-1],('Other',3))
        self.assertEqual(sum(v for _,v in m['languages']),m['language_total'])

    def test_missing_future_and_negative_data_are_rejected(self):
        for change in ['missing','future','negative']:
            with self.subTest(change=change):
                s=snapshot()
                if change=='missing':del s['contributions']['2024-01-02']
                elif change=='future':s['contributions']['2024-01-05']=1
                else:s['contributions']['2024-01-02']=-1
                with self.assertRaises(ValueError):data.validate(s)


class CalendarTests(unittest.TestCase):
    def test_full_leap_calendar_and_comma_counts(self):
        days=data.parse_calendar(calendar_html(2024),2024)
        self.assertEqual(len(days),366)
        self.assertEqual(days['2024-01-01'],1234)
        self.assertEqual(days['2024-01-02'],1)
        self.assertEqual(days['2024-02-29'],0)

    def test_partial_calendar_rejected(self):
        with self.assertRaises(ValueError):data.parse_calendar('',2024)

    def test_missing_tooltip_is_not_zero(self):
        html=calendar_html(2024).replace('for="d3"','for="missing"')
        with self.assertRaises(ValueError):data.parse_calendar(html,2024)

    def test_duplicate_dates_and_changed_markup_rejected(self):
        for html in [calendar_html(2024).replace('2024-01-02','2024-01-01'),calendar_html(2024).replace('No contributions','Unknown')]:
            with self.assertRaises(ValueError):data.parse_calendar(html,2024)


class RefreshTests(unittest.TestCase):
    def test_repository_and_language_pagination(self):
        calls=[]
        def api(query,v):
            calls.append(v)
            if query==updater.LANGUAGES:
                return {'repository':{'isPrivate':False,'languages':{'edges':[{'size':30,'node':{'name':'HTML'}}],'pageInfo':{'hasNextPage':False,'endCursor':None}}}}
            first=v['cursor'] is None
            return {'user':{'createdAt':'2024-01-01T00:00:00Z','repositories':{'nodes':[api_node('one' if first else 'two',more_languages=first)],'pageInfo':{'hasNextPage':first,'endCursor':'repo1' if first else None}}}}
        _,repos=updater.collect_repositories(api)
        self.assertEqual(len(repos),2)
        self.assertEqual(repos[0]['languages'],{'HTML':30,'Python':100})
        self.assertEqual(len(calls),3)

    def test_private_repo_rejected(self):
        def api(q,v):
            result=fake_api(q,v);result['user']['repositories']['nodes'][0]['isPrivate']=True;return result
        with self.assertRaises(ValueError):updater.collect_repositories(api)

    def test_looping_pagination_rejected(self):
        def api(q,v):
            result=fake_api(q,v);result['user']['repositories']['pageInfo']={'hasNextPage':True,'endCursor':'same'};return result
        with self.assertRaises(ValueError):updater.collect_repositories(api)

    def test_http_200_graphql_errors_rejected(self):
        result=subprocess.CompletedProcess([],0,stdout=json.dumps({'data':{},'errors':[{'message':'No'}]}))
        with patch.dict(os.environ,{},clear=True),patch.object(subprocess,'run',return_value=result):
            with self.assertRaises(ValueError):updater.graphql('query {}',{})

    def test_snapshot_atomicity_failure_and_unchanged_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'profile.json').write_text(json.dumps({'projects':[{'repository':'zindi-cli'}]}))
            calendar_fetch=lambda year:data.parse_calendar(calendar_html(year),year)
            args=dict(root=root,as_of=date(2024,1,4),api=fake_api,calendar_fetch=calendar_fetch)
            self.assertTrue(updater.refresh(**args))
            path=root/'data/github.json';old=path.read_bytes();mtime=path.stat().st_mtime_ns
            self.assertFalse(updater.refresh(**args))
            self.assertEqual(path.stat().st_mtime_ns,mtime)
            args['calendar_fetch']=lambda year: (_ for _ in ()).throw(TimeoutError())
            with self.assertRaises(TimeoutError):updater.refresh(**args)
            self.assertEqual(path.read_bytes(),old)
            self.assertFalse(path.with_suffix('.tmp').exists())

    def test_missing_featured_repo_preserves_old_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();path=root/'data/github.json';path.write_text('old')
            (root/'profile.json').write_text(json.dumps({'projects':[{'repository':'missing'}]}))
            with self.assertRaises(ValueError):updater.refresh(root,date(2024,1,4),fake_api,lambda y:data.parse_calendar(calendar_html(y),y))
            self.assertEqual(path.read_text(),'old')


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated=build.outputs()

    def test_deterministic_and_asset_references(self):
        self.assertEqual(self.generated,build.outputs())
        readme=self.generated[build.ROOT/'README.md']
        for name in re.findall(r'(?:src|srcset)="(assets/[^"]+)"',readme):self.assertIn(build.ROOT/name,self.generated)
        self.assertNotIn('YM-01',readme)
        self.assertNotIn('Selected systems',readme)

    def test_valid_self_contained_svg_and_size(self):
        for path,svg in self.generated.items():
            if path.suffix!='.svg':continue
            with self.subTest(path=path.name):
                ET.fromstring(svg)
                self.assertNotRegex(svg,r'<(?:script|foreignObject|image)\b')
                self.assertNotIn('https://',svg)
                if 'static' in path.name:self.assertNotIn('@keyframes',svg)
                if '@keyframes' in svg:self.assertIn('prefers-reduced-motion',svg)
        for theme in ['dark','light']:
            total=sum(len(v.encode()) for p,v in self.generated.items() if f'-{theme}' in p.name and '-compact' not in p.name and 'static' not in p.name)
            self.assertLess(total,300_000)

    def test_calendar_encodes_exactly_365_real_dates(self):
        snapshot=json.loads((build.ROOT/'data/github.json').read_text())
        expected=dict(data.metrics(snapshot)['recent'])
        for name in ['hero-dark.svg','hero-light-compact.svg']:
            svg=self.generated[build.ROOT/'assets'/name]
            actual=dict((d,int(n)) for d,n in re.findall(r'data-date="([^"]+)" data-count="(\d+)"',svg))
            self.assertEqual(actual,expected)

    def test_untrusted_text_is_escaped(self):
        d=art.Drawing(200,100,'dark','<script>','& test')
        d.text(10,30,'<img onerror="bad">')
        self.assertNotIn('<img',d.finish())
        self.assertIn('&lt;img',d.finish())
        self.assertIn(r'\[click\]',build.md_text('[click](javascript:alert(1))'))

    def test_check_never_writes_or_deletes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'assets').mkdir();old=root/'assets/old.svg';old.write_text('old')
            with patch.object(build,'outputs',return_value={root/'README.md':'new'}):
                with self.assertRaises(SystemExit):build.build(True,root)
                self.assertEqual(old.read_text(),'old');self.assertFalse((root/'README.md').exists())

    def test_invalid_destinations(self):
        for url in ['javascript:alert(1)','https://','https://a\nb','https://user:pass@example.org']:
            with self.assertRaises(ValueError):build.safe_url(url)


if __name__=='__main__':unittest.main()
