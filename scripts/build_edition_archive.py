#!/usr/bin/env python3
"""Build permanent, static edition pages from saved snapshots."""
import copy
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from build_article_pages import DETAIL_CSS, ORNAMENTS, build_article_page, esc, human_date, slugify

ROOT = Path(__file__).resolve().parents[1]

def absolute(value):
    value = str(value or '')
    return value if urlsplit(value).scheme or value.startswith('/') else '/' + value

def page(title, body):
    return ('<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>'+esc(title)+' | Buurt deze week</title><style>'+DETAIL_CSS+
        '.archive-nav{display:flex;flex-wrap:wrap;justify-content:space-between;gap:16px;padding:22px 0;border-top:3px double #929e93}.archive-nav a{font-size:14px;font-weight:700}.archive-note{font-size:13px;color:#536359;padding:12px 0}.archive-list{padding:18px 0;border-bottom:1px solid #cbd3c9}.archive-list h2{margin:8px 0;font-family:Georgia,serif}.archive-list a{text-decoration:none}.jump button[aria-pressed="true"]{background:#155eef;color:white}[hidden]{display:none!important}</style></head><body>'+ORNAMENTS+
        '<header><nav><a class="brand" href="/">Buurt deze week.</a><a class="topnav" href="/edities/">Alle edities</a><a class="topnav" href="/#inschrijven">In je mailbox →</a></nav></header><main>'+body+
        '<footer>Buurt deze week · Zuidoost-Enschede · <a href="/">Nieuwste editie</a> · <a href="/#tip">Tip de buurt</a></footer></main><script async src="https://scripts.simpleanalyticscdn.com/latest.js"></script></body></html>')

def build(root=ROOT):
    archive=root/'edities'; archive.mkdir(exist_ok=True)
    generated=root/'editie-site.json'
    if generated.exists():
        current=json.loads(generated.read_text())
        date=current['edition']['date']
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date): raise ValueError('Ongeldige editiedatum')
        (archive/(date+'.json')).write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
    editions=[]
    for path in archive.glob('????-??-??.json'):
        data=json.loads(path.read_text())
        if path.stem != data['edition']['date']: raise ValueError('Datum en bestandsnaam verschillen: '+path.name)
        editions.append(data)
    editions.sort(key=lambda d:d['edition']['date'],reverse=True)
    entries=[]
    for n,data in enumerate(editions):
        edition=data['edition']; date=edition['date']; sections=data['sections']; cards=[]; count=0
        for section in sections:
            stories=[]
            for original in section.get('items',[]):
                item=copy.deepcopy(original)
                slug=re.sub(r'^\d{4}-\d{2}-\d{2}-','',slugify(item.get('slug') or item['title']))
                item['page_url']=f'berichten/{date}-{slug}/index.html'
                if item.get('image_url'): item['image_url']=absolute(item['image_url'])
                destination=root/item['page_url']; destination.parent.mkdir(parents=True,exist_ok=True)
                detail=build_article_page(edition,section,item).replace('href="/">← Terug naar de editie','href="/edities/'+date+'/">← Terug naar de editie').replace('href="/">Terug naar de editie','href="/edities/'+date+'/">Terug naar de editie')
                destination.write_text(detail)
                image=('<a class="card-image" href="/'+esc(item['page_url'])+'"><img class="thumb" src="'+esc(item['image_url'])+'" alt="'+esc(item.get('image_alt') or 'Illustratief beeld')+'" loading="lazy"></a>') if item.get('image_url') else ''
                stories.append('<article class="public-story"><div class="card-copy"><div class="tag">'+esc(item.get('display_date') or item.get('label'))+'</div><h2><a href="/'+esc(item['page_url'])+'">'+esc(item['title'])+'</a></h2><p class="card-summary">'+esc(item['summary'])+'</p><div class="card-bottom"><a class="read-more" href="/'+esc(item['page_url'])+'">Lees meer →</a><span class="card-source">Bron: '+esc(item.get('source'))+'</span></div></div>'+image+'</article>'); count+=1
            cards.append('<section data-category="'+esc(section['id'])+'"><h2 class="section-heading">'+esc(section['title'])+'</h2>'+''.join(stories)+'</section>')
        neighbors=[]
        if n+1<len(editions): neighbors.append('<a href="/edities/'+editions[n+1]['edition']['date']+'/">← Vorige editie</a>')
        neighbors.append('<a href="/edities/">Alle edities</a>')
        if n>0: neighbors.append('<a href="/edities/'+editions[n-1]['edition']['date']+'/">Volgende editie →</a>')
        nav='<nav class="archive-nav" aria-label="Edities">'+''.join(neighbors)+'</nav>'
        buttons='<button type="button" data-filter="all" aria-pressed="true">Alles</button>'+''.join('<button type="button" data-filter="'+esc(s['id'])+'" aria-pressed="false">'+esc(s['title'])+'</button>' for s in sections)
        body=nav+'<section class="hero"><div class="edition-strip"><span>Bewaar-editie</span><span>'+esc(human_date(date))+'</span><span>Zuidoost-Enschede</span></div><div class="newspaper-hero"><div><h1>'+esc(edition.get('title'))+'</h1><p class="intro">'+esc(edition.get('intro'))+'</p><div class="meta">'+str(count)+' berichten · '+esc(human_date(date))+'</div></div><figure class="edition-picture"><img src="/assets/enschede-hero-staand.png" alt="Illustratie van Enschede"></figure></div></section><p class="archive-note">Deze editie is bewaard zoals gepubliceerd. Data, activiteiten en bekendmakingen kunnen inmiddels achterhaald zijn. Controleer de bron voor actuele informatie.</p><div class="jump" role="group" aria-label="Filter berichten">'+buttons+'</div>'+''.join(cards)+nav
        body+='<script>document.querySelectorAll("[data-filter]").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll("[data-filter]").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));document.querySelectorAll("[data-category]").forEach(s=>s.hidden=b.dataset.filter!=="all"&&s.dataset.category!==b.dataset.filter);}));</script>'
        folder=archive/date; folder.mkdir(exist_ok=True); (folder/'index.html').write_text(page(edition.get('title'),body))
        entries.append({'date':date,'title':edition.get('title'),'stories':count,'sources':len({i.get('source') for s in sections for i in s.get('items',[])}),'file':f'edities/{date}.json','page_url':f'edities/{date}/'})
    overview='<a class="detail-back" href="/">← Nieuwste editie</a><h1 class="detail-title">Alle edities</h1><p>Blader door eerdere edities van Buurt deze week. Elke editie heeft een eigen vaste pagina.</p>'
    for e in entries: overview+='<article class="archive-list"><div class="meta">'+esc(human_date(e['date']))+' · '+str(e['stories'])+' berichten</div><h2><a href="/'+e['page_url']+'">'+esc(e['title'])+'</a></h2><a class="read-more" href="/'+e['page_url']+'">Lees deze editie →</a></article>'
    (archive/'index.html').write_text(page('Alle edities',overview))
    (archive/'index.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(entries)} editiepagina’s gebouwd; historische snapshots blijven bewaard.')

if __name__=='__main__': build()
