"""Original Jonny wordmark and data-driven vector artwork; no browser dependencies."""
from datetime import date, timedelta
from html import escape
from pathlib import Path
import textwrap
import xml.etree.ElementTree as ET

from github_data import metrics

PALETTES = {
 'dark':dict(bg='#101820',panel='#17232D',ink='#F4EFE6',muted='#A6B6BF',copper='#D99A63',teal='#75C4BC',line='#30434F',tile0='#23333E',tile1='#285650',tile2='#3E8479',tile3='#63B0A1',tile4='#9ED9C4'),
 'light':dict(bg='#F4EFE6',panel='#EAE4D8',ink='#182A33',muted='#52636B',copper='#8D4C27',teal='#236B66',line='#C9C8BD',tile0='#DEDCD2',tile1='#A7C7B8',tile2='#729F89',tile3='#437A62',tile4='#23553F'),
}


class Drawing:
 def __init__(self,w,h,theme,title,description):
  self.w,self.h,self.c=w,h,PALETTES[theme]
  self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
   '<style>text{font-family:Inter,Arial,Helvetica,sans-serif}.mono{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}</style>']
  self.rect(0,0,w,h,'bg',radius=18)
 def color(self,c):return self.c.get(c,c)
 def rect(self,x,y,w,h,fill='panel',stroke=None,radius=0,extra=''):
  border=f' stroke="{self.color(stroke)}"' if stroke else ''
  self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{self.color(fill)}"{border} {extra}/>')
 def text(self,x,y,value,size=14,color='ink',weight=400,anchor='start',mono=False,spacing=0):
  self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{self.color(color)}" font-weight="{weight}" text-anchor="{anchor}" letter-spacing="{spacing}"'+(' class="mono"' if mono else '')+f'>{escape(str(value))}</text>')
 def path(self,path,color='line',width=1.5,fill='none',extra=''):
  self.parts.append(f'<path d="{path}" stroke="{self.color(color)}" stroke-width="{width}" fill="{self.color(fill)}" stroke-linecap="round" stroke-linejoin="round" {extra}/>')
 def circle(self,x,y,r,color='teal',extra=''):
  self.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{self.color(color)}" {extra}/>')
 def group(self,transform):self.parts.append(f'<g transform="{transform}">')
 def end(self):self.parts.append('</g>')
 def finish(self):return '\n'.join(self.parts+['</svg>',''])


def wordmark(d,x,y,scale=1):
 """Hand-drawn Jonny lettering; the wordmark remains editable vector geometry."""
 d.group(f'translate({x} {y}) scale({scale})')
 for path in ['M0 5 H43 V53 Q43 77 21 77 Q0 77 0 56',
              'M94 29 C62 29 62 77 94 77 C126 77 126 29 94 29',
              'M135 75 V31 M135 51 C135 22 174 22 174 51 V75',
              'M194 75 V31 M194 51 C194 22 233 22 233 51 V75',
              'M253 31 L276 76 M299 31 L271 91 Q261 108 249 101']:
  d.path(path,'ink',10)
 d.circle(320,75,6,'copper')
 d.end()


def grid_geometry(recent):
 start=date.fromisoformat(recent[0][0])
 sunday=start-timedelta(days=(start.weekday()+1)%7)
 cells=[]
 for day,count in recent:
  elapsed=(date.fromisoformat(day)-sunday).days
  cells.append((day,count,elapsed//7,elapsed%7))
 return cells


def calendar_panel(d,cells,x,y,step,size,motion,part=0):
 lo=min(c[2] for c in cells)
 hi=max(c[2] for c in cells)
 month_seen=set()
 for day,count,col,row in cells:
  dt=date.fromisoformat(day)
  if dt.day<=7 and dt.month not in month_seen:
   d.text(x+(col-lo)*step,y-10,dt.strftime('%b'),11 if d.w>400 else 12,'muted')
   month_seen.add(dt.month)
  level=0 if count==0 else 1 if count<5 else 2 if count<10 else 3 if count<20 else 4
  cx,cy=x+(col-lo)*step,y+row*step
  d.rect(cx,cy,size,size,f'tile{level}',radius=2,extra=f'data-date="{day}" data-count="{count}"')
 # The moving outline is separate from the count-encoded tile fills.
 if motion:
  width=(hi-lo)*step+size
  d.parts.append(f'<g class="scan scan-{part}" style="--travel:{width}px">')
  d.rect(x,y-3,2,7*step,'copper',radius=1)
  d.circle(x+1,y-5,3,'copper')
  d.parts.append('</g>')


def hero(profile,snapshot,theme,compact=False,motion=True):
 w,h=(360,460) if compact else (840,368)
 m=metrics(snapshot)
 d=Drawing(w,h,theme,'Jonny — Yohannes Melese',f"AI, software, and electronics. {m['contributions']:,} publicly visible contributions in the last 365 days, as of {snapshot['as_of']}.")
 if motion:
  d.parts.append('''<style>.scan{opacity:0;animation:scan 18s linear infinite}.scan-1{animation-delay:3s}@keyframes scan{0%{opacity:0;transform:translateX(0)}2%{opacity:.85}31%{opacity:.85}33%{opacity:0;transform:translateX(var(--travel))}100%{opacity:0;transform:translateX(var(--travel))}}@media(prefers-reduced-motion:reduce){.scan{animation:none;display:none}}</style>''')
 if compact:
  d.text(24,30,'AI / SOFTWARE / ELECTRONICS',11,'teal',mono=True,spacing=.7)
  wordmark(d,26,47,.91)
  d.text(24,169,'Yohannes Melese · Addis Ababa',13,'muted')
  d.text(24,202,'A year of showing up.',19,'ink',600)
  cells=grid_geometry(m['recent'])
  for part in range(2):
   section=[c for c in cells if (c[2]<27)==(part==0)]
   if section:calendar_panel(d,section,24,237+part*98,11,8,motion,part)
  d.text(24,425,'Less',10,'muted')
  for i in range(5):d.rect(51+i*14,417,9,9,f'tile{i}',radius=2)
  d.text(128,425,'More',10,'muted')
  d.text(24,440,snapshot['as_of'],11,'muted',mono=True)
  d.text(336,440,f"{m['contributions']:,} contributions",12,'teal',600,anchor='end')
 else:
  d.text(34,31,'AI / SOFTWARE / ELECTRONICS',12,'teal',mono=True,spacing=1.2)
  wordmark(d,40,53,1.05)
  d.text(40,187,'Yohannes Melese · Addis Ababa, Ethiopia',14,'muted')
  d.text(528,87,'From curiosity',30,'ink',600)
  d.text(528,125,'to working code.',30,'copper',600)
  d.path('M468 52 V184','line')
  d.text(40,224,'A YEAR OF SHOWING UP',11,'muted',mono=True,spacing=1.2)
  d.text(800,224,f"{m['contributions']:,} contributions",13,'teal',600,anchor='end')
  calendar_panel(d,grid_geometry(m['recent']),40,250,14,10,motion)
  d.text(40,356,f"LAST 365 DAYS  /  UPDATED {snapshot['as_of']}",10,'muted',mono=True)
  d.text(663,356,'Less',10,'muted')
  for i in range(5):d.rect(692+i*15,348,10,10,f'tile{i}',radius=2)
  d.text(800,356,'More',10,'muted',anchor='end')
 return d.finish()


def flame(d,x,y,scale=1):
 d.group(f'translate({x} {y}) scale({scale})')
 d.path('M14 0 C16 10 4 13 5 23 C-5 11 0 35 14 35 C30 35 34 17 24 10 C25 22 15 20 14 0 Z','copper',1,'copper')
 d.path('M14 18 C16 25 9 27 13 32 C22 32 22 24 19 22 C19 28 14 26 14 18 Z','bg',1,'bg')
 d.end()


def stats(snapshot,theme,compact=False):
 m=metrics(snapshot)
 w,h=(360,290) if compact else (840,140)
 d=Drawing(w,h,theme,'GitHub activity',f"Current streak {m['current']} days; longest streak {m['longest']} days; {m['contributions']} contributions in the last 365 days; {m['stars']} stars; {m['repositories']} public repositories.")
 if compact:
  positions=[(24,35,'Current streak',m['current'],'copper'),(196,35,'Longest streak',m['longest'],'ink'),(24,127,'Contributions · last 365 days',m['contributions'],'teal'),(24,219,'Stars received',m['stars'],'ink'),(196,219,'Public repos',m['repositories'],'ink')]
  d.path('M24 103 H336 M24 195 H336','line',1)
  for x,y,label,value,color in positions:
   d.text(x,y,label,17,'muted');d.text(x,y+43,f'{value:,}',39,color,600)
  flame(d,310,119,.7)
 else:
  positions=[(28,'Current streak',m['current'],'copper'),(206,'Longest streak',m['longest'],'ink'),(384,'Contributions',m['contributions'],'teal'),(584,'Stars received',m['stars'],'ink'),(722,'Public repos',m['repositories'],'ink')]
  for x,label,value,color in positions:
   d.text(x,34,label,13,'muted');d.text(x,85,f'{value:,}',44,color,600)
  d.text(28,112,'days',11,'muted');d.text(206,112,'days · all time',11,'muted');d.text(384,112,'last 365 days',11,'muted')
  for x in [184,362,562,700]:d.path(f'M{x} 26 V115','line',1)
  flame(d,134,51,.8)
 return d.finish()


def tools_strip(profile,theme,root,compact=False):
 d=Drawing(360 if compact else 840,242 if compact else 98,theme,'Tools I work with',', '.join(t['label'] for t in profile['tools']))
 for i,tool in enumerate(profile['tools']):
  x=(135 if i>=8 else 45)+(i%4)*90 if compact else 42+i*84
  y=18+(i//4)*76 if compact else 20
  node=ET.fromstring((root/'assets/icons'/f"{tool['id']}.svg").read_text())
  d.group(f'translate({x-13} {y}) scale(1.08)')
  for path in node.findall('{http://www.w3.org/2000/svg}path'):
   d.path(path.attrib['d'],'teal' if i%2 else 'copper',0,'teal' if i%2 else 'copper')
  d.end()
  label=tool['label']
  if compact and label=='Hugging Face':
   d.text(x,y+44,'Hugging',16,'ink',anchor='middle');d.text(x,y+62,'Face',16,'ink',anchor='middle')
  else:d.text(x,y+46,label,16 if compact else 12,'ink',anchor='middle')
 return d.finish()


def languages(snapshot,theme,compact=False):
 m=metrics(snapshot);items=m['languages'];total=m['language_total']
 w,h=(360,262) if compact else (840,108)
 d=Drawing(w,h,theme,'Public repository languages','Language composition by GitHub-reported bytes, excluding forks and this profile repository. '+', '.join(f'{n}: {100*v/total:.1f}%' for n,v in items) if total else 'No public language data')
 colors=['teal','copper','#809CBA','#B49ACA','#A9B68A','#CFA59A','muted']
 d.text(24,25,'PUBLIC CODE MIX',11,'muted',mono=True,spacing=1)
 d.text(w-24,25,'by bytes',11,'muted',anchor='end')
 x=24
 for i,(name,size) in enumerate(items):
  length=(w-48)*size/total if total else 0
  d.rect(x,39,length,10,colors[i]);x+=length
 for i,(name,size) in enumerate(items):
  col,row=(0,i) if compact else (i%4,i//4)
  x=24+col*202;y=76+row*(28 if compact else 25)
  label=name
  d.circle(x+3,y-4,3,colors[i])
  d.text(x+13,y,label,17 if compact else 12,'ink')
  d.text(x+(312 if compact else 180),y,f'{100*size/total:.1f}%',16 if compact else 11,'muted',anchor='end')
 if not items:d.text(24,79,'No language data available yet.',14,'muted')
 return d.finish()


def repo_card(item,repo,theme,compact=False):
 w,h=(360,172) if compact else (404,142)
 d=Drawing(w,h,theme,item['title'],f"{item['description']} {repo['stars']} stars. {repo['primary_language'] or 'Code'}.")
 d.rect(0,0,4,h,item['accent'])
 d.text(22,30,item['title'],20 if compact else 19,'ink',600)
 # Small arrow outside the title keeps the entire card's link affordance visible.
 d.path(f'M{w-32} 20 h10 v10 M{w-32} 30 l10 -10',item['accent'],1.6)
 for i,line in enumerate(textwrap.wrap(item['description'],width=35 if compact else 48)):
  d.text(22,59+i*22,line,17 if compact else 14,'muted')
 d.text(22,h-22,item['tags'],14 if compact else 12,item['accent'])
 d.text(w-20,h-22,f"{repo['stars']} stars",14 if compact else 12,'muted',anchor='end')
 return d.finish()


def assets(profile,snapshot,root):
 result={};repos={r['name']:r for r in snapshot['repositories']}
 for theme in PALETTES:
  for compact in [False,True]:
   suffix=f"{theme}{'-compact' if compact else ''}.svg"
   result[f'hero-{suffix}']=hero(profile,snapshot,theme,compact)
   result[f'hero-static-{suffix}']=hero(profile,snapshot,theme,compact,motion=False)
   result[f'stats-{suffix}']=stats(snapshot,theme,compact)
   result[f'tools-{suffix}']=tools_strip(profile,theme,root,compact)
   result[f'languages-{suffix}']=languages(snapshot,theme,compact)
   for item in profile['projects']:
    result[f"repo-{item['id']}-{suffix}"]=repo_card(item,repos[item['repository']],theme,compact)
 return result
