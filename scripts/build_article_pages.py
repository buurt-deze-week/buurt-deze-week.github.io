#!/usr/bin/env python3
import copy
import datetime as dt
import html
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "editie.json"
OUTPUT_FILE = ROOT / "editie-site.json"
ARTICLES_DIR = ROOT / "berichten"
IMAGES_DIR = ROOT / "assets" / "berichten"
SITE_URL = "https://www.buurtdezeweek.nl"

MONTHS = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december"
]
DAYS = [
    "maandag", "dinsdag", "woensdag", "donderdag",
    "vrijdag", "zaterdag", "zondag"
]


def esc(value):
    return html.escape(str(value or ""), quote=True)


def slugify(text):
    text = str(text or "").lower().strip()
    replacements = {
        "à": "a", "á": "a", "ä": "a", "â": "a",
        "è": "e", "é": "e", "ë": "e", "ê": "e",
        "ì": "i", "í": "i", "ï": "i", "î": "i",
        "ò": "o", "ó": "o", "ö": "o", "ô": "o",
        "ù": "u", "ú": "u", "ü": "u", "û": "u",
        "ç": "c", "ñ": "n", "’": "", "‘": "", "'": "",
        "&": " en "
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def human_date(date_string):
    day = dt.date.fromisoformat(date_string)
    return f"{DAYS[day.weekday()].capitalize()} {day.day} {MONTHS[day.month - 1]} {day.year}"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )


def request_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BuurtDezeWeek/1.0 (+https://www.buurtdezeweek.nl/)"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url, destination):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BuurtDezeWeek/1.0 (+https://www.buurtdezeweek.nl/)"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        destination.write_bytes(response.read())


def normalize_query(item, section_title):
    custom = (item.get("pixabay_query") or "").strip()
    if custom:
        return custom[:100]

    title = (item.get("title") or "").lower()
    label = (item.get("label") or "").lower()
    text = f"{title} {label}"

    mappings = [
        (("wegwerk", "verkeer", "asfalt", "straat"), "road construction neighborhood"),
        (("woning", "wonen", "huur", "nieuwbouw"), "housing neighborhood homes"),
        (("vrijwill",), "community volunteers helping"),
        (("film",), "cinema film audience"),
        (("jongeren", "huiskamer"), "young people community center"),
        (("wijkwijzer", "geld", "regelzaken"), "community help advice"),
        (("bodemdier", "regenworm", "pissebed"), "soil earthworm nature"),
        (("speeltuin", "kinderen"), "playground children neighborhood"),
        (("park", "wooldrik"), "city park trees neighborhood"),
        (("sport", "voetbal", "tennis"), "community sports field"),
        (("moskee", "islamitisch"), "mosque architecture"),
        (("school",), "school building education"),
        (("wijkbudget", "bewonersinitiatief"), "neighbors community meeting"),
    ]
    for needles, query in mappings:
        if any(needle in text for needle in needles):
            return query

    compact_title = re.sub(r"[^a-zA-ZÀ-ÿ0-9 ]+", " ", item.get("title") or "")
    compact_title = re.sub(r"\s+", " ", compact_title).strip()
    if compact_title:
        return (compact_title + " neighborhood community")[:100]
    return (section_title + " neighborhood community")[:100]


def old_item_map():
    if not OUTPUT_FILE.exists():
        return {}
    try:
        old = read_json(OUTPUT_FILE)
    except Exception:
        return {}

    result = {}
    for section in old.get("sections", []):
        for item in section.get("items", []):
            key = (item.get("url") or item.get("title") or "").strip()
            if key:
                result[key] = item
    return result


def get_pixabay_image(item, section_title, edition_date, slug, existing_item=None):
    if existing_item:
        image_url = (existing_item.get("image_url") or "").strip()
        image_path = (existing_item.get("image_path") or "").strip()
        if image_path and (ROOT / image_path).exists():
            return {
                "image_url": image_url or f"/{image_path}",
                "image_path": image_path,
                "image_credit": existing_item.get("image_credit", ""),
                "image_page_url": existing_item.get("image_page_url", ""),
                "pixabay_query": existing_item.get("pixabay_query") or normalize_query(item, section_title),
            }

    manual_url = (item.get("image_url") or "").strip()
    if manual_url:
        return {
            "image_url": manual_url,
            "image_path": item.get("image_path", ""),
            "image_credit": item.get("image_credit", ""),
            "image_page_url": item.get("image_page_url", ""),
            "pixabay_query": item.get("pixabay_query") or normalize_query(item, section_title),
        }

    api_key = os.getenv("PIXABAY_API_KEY", "").strip()
    query = normalize_query(item, section_title)
    if not api_key:
        print(f"Geen PIXABAY_API_KEY: geen afbeelding voor {item.get('title')}")
        return {"pixabay_query": query}

    params = {
        "key": api_key,
        "q": query,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "per_page": 20,
        "min_width": 800,
    }
    api_url = "https://pixabay.com/api/?" + urllib.parse.urlencode(params)

    try:
        data = request_json(api_url)
    except Exception as exc:
        print(f"Pixabay-fout voor '{item.get('title')}': {exc}")
        return {"pixabay_query": query}

    hits = data.get("hits") or []
    if not hits:
        print(f"Geen Pixabay-resultaat voor '{query}'")
        return {"pixabay_query": query}

    hit = max(
        hits,
        key=lambda value: (
            int(value.get("webformatWidth") or 0),
            int(value.get("likes") or 0),
            int(value.get("downloads") or 0),
        )
    )

    source_url = hit.get("webformatURL") or hit.get("largeImageURL")
    if not source_url:
        return {"pixabay_query": query}

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{edition_date}-{slug}.jpg"
    destination = IMAGES_DIR / filename

    try:
        download_file(source_url, destination)
    except Exception as exc:
        print(f"Downloadfout Pixabay voor '{item.get('title')}': {exc}")
        return {
            "image_url": source_url,
            "pixabay_query": query,
            "image_credit": hit.get("user", ""),
            "image_page_url": hit.get("pageURL", ""),
        }

    relative_path = destination.relative_to(ROOT).as_posix()
    return {
        "image_url": f"/{relative_path}",
        "image_path": relative_path,
        "image_credit": hit.get("user", ""),
        "image_page_url": hit.get("pageURL", ""),
        "pixabay_query": query,
    }


def text_to_paragraphs(value):
    raw = str(value or "").strip()
    if not raw:
        return ""
    parts = [part.strip() for part in re.split(r"\n\s*\n", raw) if part.strip()]
    if not parts:
        parts = [raw]
    return "".join(f"<p>{esc(part)}</p>" for part in parts)


def build_article_page(edition, section, item):
    title = esc(item.get("title"))
    short_summary = esc(item.get("summary"))
    page_summary = item.get("page_summary") or item.get("summary") or ""
    label = esc(item.get("label"))
    source = esc(item.get("source"))
    source_url = esc(item.get("url"))
    image_url = esc(item.get("image_url"))
    image_credit = esc(item.get("image_credit"))
    image_page_url = esc(item.get("image_page_url"))
    brand = esc(edition.get("brand", "Buurt deze week · Zuidoost-Enschede"))
    display_date = esc(human_date(edition["date"]))
    section_title = esc(section.get("title"))

    image_html = ""
    if image_url:
        credit_html = ""
        if image_credit:
            if image_page_url:
                credit_html = (
                    f'<div class="credit">Foto: <a href="{image_page_url}" target="_blank" rel="noopener">'
                    f'{image_credit} / Pixabay</a></div>'
                )
            else:
                credit_html = f'<div class="credit">Foto: {image_credit} / Pixabay</div>'
        image_html = (
            f'<figure class="hero-image">'
            f'<img src="{image_url}" alt="Illustratie bij: {title}">'
            f'{credit_html}'
            f'</figure>'
        )

    label_class = item.get("label_style") if item.get("label_style") in {"green", "orange"} else "blue"
    label_html = f'<span class="label {label_class}">{label}</span>' if label else ""

    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | Buurt deze week</title>
  <meta name="description" content="{short_summary}">
  <link rel="canonical" href="{SITE_URL}/{esc(item.get('page_url'))}">
  <style>
    :root{{--bg:#f5f1e8;--paper:#fffdf8;--text:#18212b;--muted:#66707a;--line:#ded8cb;--blue:#155eef;--blue-dark:#0b3fa8;--soft-blue:#eaf1ff;--green:#1f7a53;--soft-green:#eaf6ef;--orange:#b65b12;--soft-orange:#fff1e6;--radius:22px;--shadow:0 10px 30px rgba(23,32,42,.07);--max:860px}}
    *{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.62}}a{{color:inherit}}.wrap{{width:min(100% - 28px,var(--max));margin:0 auto}}.top{{padding:24px 0 8px;font-size:.92rem}}.top a{{color:var(--blue-dark);font-weight:800;text-decoration:none}}.top a:hover{{text-decoration:underline}}main{{padding:18px 0 54px}}.brand{{font-size:.84rem;font-weight:900;color:var(--blue-dark);margin-bottom:12px}}.date{{color:var(--muted);font-size:.92rem;margin-bottom:18px}}h1{{font-family:Georgia,'Times New Roman',serif;font-size:clamp(2.2rem,7vw,4.7rem);line-height:1;letter-spacing:-.045em;margin:0 0 18px}}.lead{{font-size:1.17rem;line-height:1.55;color:#45515b;margin:0 0 25px;max-width:760px}}.hero-image{{margin:0 0 27px}}.hero-image img{{display:block;width:100%;max-height:460px;object-fit:cover;border-radius:var(--radius);box-shadow:var(--shadow)}}.credit{{margin-top:7px;font-size:.76rem;color:var(--muted)}}.credit a{{color:inherit}}.article-card{{background:var(--paper);border:1px solid rgba(88,78,54,.12);border-radius:var(--radius);padding:28px;box-shadow:0 4px 16px rgba(23,32,42,.035)}}.eyebrow{{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:18px}}.section-name{{font-size:.76rem;font-weight:900;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}.label{{display:inline-block;font-size:.73rem;font-weight:900;text-transform:uppercase;letter-spacing:.05em;border-radius:999px;padding:6px 9px}}.label.blue{{color:var(--blue-dark);background:var(--soft-blue)}}.label.green{{color:var(--green);background:var(--soft-green)}}.label.orange{{color:var(--orange);background:var(--soft-orange)}}.story{{font-size:1.04rem;color:#35424c}}.story p{{margin:0 0 1.15em}}.story p:last-child{{margin-bottom:0}}.source-box{{margin-top:26px;padding-top:22px;border-top:1px solid var(--line)}}.source-box p{{margin:0 0 13px;color:var(--muted);font-size:.9rem}}.button{{display:inline-flex;align-items:center;justify-content:center;background:var(--blue);color:white;text-decoration:none;font-weight:850;border-radius:12px;padding:13px 16px}}.button:hover{{background:#0c50da}}.back{{margin-top:24px;font-size:.91rem;color:var(--muted)}}.back a{{color:var(--blue-dark);font-weight:800;text-decoration:none}}.back a:hover{{text-decoration:underline}}@media(max-width:640px){{.wrap{{width:min(100% - 22px,var(--max))}}.article-card{{padding:21px}}}}
  </style>
</head>
<body>
  <div class="wrap top"><a href="/">← Terug naar Buurt deze week</a></div>
  <main class="wrap">
    <div class="brand">{brand}</div>
    <div class="date">{display_date}</div>
    <h1>{title}</h1>
    <p class="lead">{short_summary}</p>
    {image_html}
    <article class="article-card">
      <div class="eyebrow">
        <span class="section-name">{section_title}</span>
        {label_html}
      </div>
      <div class="story">{text_to_paragraphs(page_summary)}</div>
      <div class="source-box">
        <p>Bron: {source}</p>
        <a class="button" href="{source_url}" target="_blank" rel="noopener">Bekijk de originele bron ↗</a>
      </div>
    </article>
    <div class="back"><a href="/">← Terug naar de volledige editie</a></div>
  </main>
  <script async src="https://scripts.simpleanalyticscdn.com/latest.js"></script>
</body>
</html>'''


def build_articles_index(edition, sections):
    cards = []
    for section in sections:
        for item in section.get("items", []):
            image = ""
            if item.get("image_url"):
                image = f'<img src="{esc(item["image_url"])}" alt="" loading="lazy">'
            cards.append(f'''<article class="card">
              <a href="/{esc(item['page_url'])}">
                {image}
                <div class="body">
                  <div class="category">{esc(section.get('title'))}</div>
                  <h2>{esc(item.get('title'))}</h2>
                  <p>{esc(item.get('summary'))}</p>
                </div>
              </a>
            </article>''')

    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Berichten | Buurt deze week</title>
  <meta name="description" content="Alle berichten uit de editie van {esc(human_date(edition['date']))}.">
  <style>
    :root{{--bg:#f5f1e8;--paper:#fffdf8;--text:#18212b;--muted:#66707a;--line:#ded8cb;--blue:#155eef;--blue-dark:#0b3fa8;--radius:20px;--max:960px}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55}}.wrap{{width:min(100% - 28px,var(--max));margin:0 auto;padding:28px 0 56px}}a{{color:inherit}}.back{{color:var(--blue-dark);font-weight:800;text-decoration:none}}h1{{font-family:Georgia,'Times New Roman',serif;font-size:clamp(2.4rem,7vw,4.8rem);line-height:1;letter-spacing:-.05em;margin:40px 0 10px}}.intro{{margin:0 0 28px;color:var(--muted);font-size:1.08rem}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}.card{{background:var(--paper);border:1px solid rgba(88,78,54,.12);border-radius:var(--radius);overflow:hidden}}.card>a{{display:block;text-decoration:none;height:100%}}.card img{{display:block;width:100%;height:190px;object-fit:cover}}.body{{padding:20px}}.category{{font-size:.73rem;font-weight:900;text-transform:uppercase;letter-spacing:.06em;color:var(--blue);margin-bottom:8px}}h2{{font-size:1.28rem;line-height:1.15;letter-spacing:-.025em;margin:0 0 8px}}p{{margin:0;color:#4b5660}}@media(max-width:680px){{.grid{{grid-template-columns:1fr}}}}
  </style>
</head>
<body><main class="wrap"><a class="back" href="/">← Terug naar de editie</a><h1>Alle berichten</h1><p class="intro">{esc(human_date(edition['date']))} · {len(cards)} berichten</p><div class="grid">{''.join(cards)}</div></main><script async src="https://scripts.simpleanalyticscdn.com/latest.js"></script></body></html>'''


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError("editie.json staat niet in de root van de repository")

    source = read_json(INPUT_FILE)
    if not source.get("edition", {}).get("date") or not isinstance(source.get("sections"), list):
        raise ValueError("editie.json heeft niet de verwachte structuur")

    edition = source["edition"]
    date_string = edition["date"]
    public = copy.deepcopy(source)
    previous = old_item_map()

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    for path in ARTICLES_DIR.glob(f"{date_string}-*.html"):
        path.unlink()
    for path in IMAGES_DIR.glob(f"{date_string}-*"):
        path.unlink()

    total = 0
    for section in public["sections"]:
        for item in section.get("items", []):
            total += 1
            slug = (item.get("slug") or slugify(item.get("title"))).strip()
            if not slug:
                raise ValueError(f"Kon geen slug maken voor: {item.get('title')}")

            filename = f"{date_string}-{slug}.html"
            item["slug"] = slug
            item["page_url"] = f"berichten/{filename}"
            item["page_summary"] = (item.get("page_summary") or item.get("summary") or "").strip()

            key = (item.get("url") or item.get("title") or "").strip()
            image_data = get_pixabay_image(
                item,
                section.get("title", ""),
                date_string,
                slug,
                previous.get(key)
            )
            item.update({key: value for key, value in image_data.items() if value})

            page = build_article_page(edition, section, item)
            (ARTICLES_DIR / filename).write_text(page, encoding="utf-8")

    (ARTICLES_DIR / "index.html").write_text(
        build_articles_index(edition, public["sections"]),
        encoding="utf-8"
    )
    write_json(OUTPUT_FILE, public)

    print(f"V1 gebouwd: {total} tussenpagina's")
    print("- editie-site.json")
    print("- berichten/index.html")
    print("- berichten/YYYY-MM-DD-*.html")
    print("- assets/berichten/*")


if __name__ == "__main__":
    main()
