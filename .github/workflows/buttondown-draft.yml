#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl, urljoin

import requests

API_URL = "https://api.buttondown.com/v1/emails"
API_VERSION = "2026-04-01"
SITE_URL = "https://www.buurtdezeweek.nl/"

MONTHS = [
    "januari","februari","maart","april","mei","juni",
    "juli","augustus","september","oktober","november","december"
]
DAYS = [
    "maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"
]


def load_edition(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    edition = data.get("edition") or {}
    sections = data.get("sections")

    raw_date = edition.get("date", "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_date):
        raise ValueError("edition.date ontbreekt of is ongeldig")

    if not isinstance(sections, list) or not sections:
        raise ValueError("sections ontbreekt of is leeg")

    parsed = date.fromisoformat(raw_date)

    for section in sections:
        if not section.get("id") or not section.get("title"):
            raise ValueError("Elke sectie moet id en title hebben")
        if not isinstance(section.get("items"), list):
            raise ValueError("Elke sectie moet items bevatten")
        for item in section["items"]:
            for field in ("title", "summary", "source", "url"):
                if not (item.get(field) or "").strip():
                    raise ValueError(f"Item mist verplicht veld: {field}")

    return data, parsed


def dutch_date(d):
    return f"{DAYS[d.weekday()].capitalize()} {d.day} {MONTHS[d.month - 1]} {d.year}"


def slugify(text):
    text = str(text or "").lower().strip()
    replacements = {
        "à":"a", "á":"a", "ä":"a", "â":"a",
        "è":"e", "é":"e", "ë":"e", "ê":"e",
        "ì":"i", "í":"i", "ï":"i", "î":"i",
        "ò":"o", "ó":"o", "ö":"o", "ô":"o",
        "ù":"u", "ú":"u", "ü":"u", "û":"u",
        "ç":"c", "ñ":"n", "’":"", "‘":"", "'":"",
        "&":" en "
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def absolute_url(value):
    value = str(value or "").strip()
    if not value:
        return ""
    resolved = urljoin(SITE_URL, value)
    if urlsplit(resolved).scheme not in {"https", "http"}:
        raise ValueError("Alle nieuwsbriefafbeeldingen en links moeten HTTP(S)-URLs zijn")
    return resolved


def article_url(item, edition_date):
    page_url = (item.get("page_url") or "").strip()
    if not page_url:
        slug = (item.get("slug") or slugify(item.get("title"))).strip()
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
        page_url = f"berichten/{edition_date.isoformat()}-{slug}/index.html"
    return absolute_url(page_url)


def add_utm(url, campaign):
    p = urlsplit(url)
    q = dict(parse_qsl(p.query, keep_blank_values=True))
    q.update({
        "utm_source": "buttondown",
        "utm_medium": "email",
        "utm_campaign": campaign,
    })
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))


def esc(value):
    return html.escape(str(value or ""), quote=True)


def email_item(item, parsed_date):
    url = esc(article_url(item, parsed_date))
    image_url = absolute_url(item.get("image_url"))
    image_html = ""
    if image_url:
        image_html = (
            '<td class="email-thumb" width="150" valign="top" style="width:150px;padding-left:18px;">'
            '<a href="' + url + '" style="text-decoration:none;">'
            '<img src="' + esc(image_url) + '" alt="' + esc(item.get("image_alt") or "Illustratief beeld bij: " + item["title"]) +
            '" width="150" border="0" style="display:block;width:150px;max-width:150px;height:auto;border-radius:10px;">'
            '</a></td>'
        )
    label = esc(item.get("display_date") or item.get("label"))
    return (
        '<tr><td style="padding:17px 0;border-bottom:1px solid #ddd9cd;">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border-collapse:collapse;">'
        '<tr><td class="email-copy" valign="top" style="font-family:Arial,Helvetica,sans-serif;">'
        '<div style="font-size:11px;line-height:1.4;font-weight:700;color:#155eef;margin-bottom:6px;">' + label + '</div>'
        '<a href="' + url + '" style="text-decoration:none;color:#132230;">'
        '<div style="font-family:Georgia,Times New Roman,serif;font-size:22px;line-height:1.2;font-weight:700;color:#132230;margin-bottom:8px;">' + esc(item["title"]) + '</div></a>'
        '<div style="font-size:14px;line-height:1.5;color:#5a6570;margin-bottom:8px;">' + esc(item["summary"]) + '</div>'
        '<a href="' + url + '" style="font-size:13px;font-weight:700;color:#155eef;text-decoration:none;">Lees meer →</a>'
        '<div style="font-size:11px;line-height:1.4;color:#6b736e;margin-top:8px;">Bron: ' + esc(item["source"]) + '</div>'
        '</td>' + image_html + '</tr></table></td></tr>'
    )


def build_body(data, parsed_date):
    edition = data["edition"]
    sections = data["sections"]

    items = [item for section in sections for item in section.get("items", [])]
    sources = {
        (item.get("source") or "").strip()
        for item in items
        if (item.get("source") or "").strip()
    }

    sections_html = []
    for section in sections:
        items_html = "".join(email_item(item, parsed_date) for item in section["items"])
        sections_html.append(f"""
          <tr>
            <td style="padding:18px 0 12px 0;">
              <div style="font-family:Arial,Helvetica,sans-serif;
                          font-size:12px;line-height:1;font-weight:900;
                          letter-spacing:.06em;text-transform:uppercase;
                          color:#155eef;">
                {esc(section["title"])}
              </div>
            </td>
          </tr>
          {items_html}
        """)

    campaign = f"editie_{parsed_date:%Y_%m_%d}"
    online_url = add_utm(SITE_URL, campaign)

    header_url = absolute_url(edition.get("header_image_url") or "assets/enschede-hero-staand.png")
    header_html = (
        '<tr><td align="center" style="padding:0 0 24px 0;">'
        '<img src="' + esc(header_url) + '" alt="Illustratie van Enschede en Zuidoost-Enschede" width="280" border="0" '
        'style="display:block;width:280px;max-width:100%;height:auto;border-radius:0 0 0 32px;">'
        '</td></tr>'
    )

    count_line = (
        f'Gratis &nbsp;·&nbsp; {len(sources)} lokale bronnen '
        f'&nbsp;·&nbsp; {len(items)} berichten'
    )

    return f"""<!-- buttondown-editor-mode: fancy -->
<style>@media only screen and (max-width:520px){{.email-copy,.email-thumb{{display:block!important;width:100%!important}}.email-thumb{{padding:12px 0 0!important}}.email-thumb img{{width:100%!important;max-width:320px!important}}}}</style>
<div style="margin:0;padding:0;background:#f6f2e9;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
       style="width:100%;background:#f6f2e9;border-collapse:collapse;">
<tr>
<td align="center" style="padding:30px 16px 44px 16px;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
       style="width:100%;max-width:680px;border-collapse:collapse;">

<tr>
<td style="font-family:Arial,Helvetica,sans-serif;padding-bottom:26px;">
  <div style="font-size:14px;color:#21483b;margin-bottom:18px;">
    {esc(dutch_date(parsed_date))}
  </div>
  <div style="font-size:12px;font-weight:800;color:#0d3f9b;margin-bottom:10px;">
    {esc(edition.get("brand", "Buurt deze week · Zuidoost-Enschede"))}
  </div>
  <div style="font-family:Georgia,'Times New Roman',serif;
              font-size:40px;line-height:1.02;font-weight:700;
              letter-spacing:-1.4px;color:#111714;margin-bottom:20px;">
    {esc(edition.get("title", "Dit speelt er deze week in jouw buurt"))}<span style="color:#155eef;">.</span>
  </div>
  <div style="font-size:18px;line-height:1.5;color:#37413c;margin-bottom:24px;">
    {esc(edition.get("intro", ""))}
  </div>
  <div style="border-top:1px solid #bfc7c1;padding-top:14px;
              font-size:12px;line-height:1.5;color:#6b736e;">
    {count_line}
  </div>
</td>
</tr>

{header_html}

<tr>
<td style="background:#fffdf8;border-radius:14px;padding:10px 22px 4px 22px;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
       style="width:100%;border-collapse:collapse;">
{''.join(sections_html)}
</table>
</td>
</tr>

<tr>
<td style="font-family:Arial,Helvetica,sans-serif;padding-top:28px;">
  <div style="background:#f3f6f4;border-radius:14px;padding:18px 18px 17px 18px;">
    <div style="font-size:17px;font-weight:800;color:#132230;margin-bottom:6px;">
      Doorgestuurd gekregen?
    </div>
    <div style="font-size:14px;line-height:1.55;color:#59635d;margin-bottom:14px;">
      Krijg Buurt deze week iedere donderdag gratis in je inbox.
    </div>
    <a href="https://www.buurtdezeweek.nl/"
       style="display:inline-block;background:#155eef;color:#ffffff !important;
              -webkit-text-fill-color:#ffffff;text-decoration:none;
              font-size:14px;font-weight:800;padding:10px 15px;border-radius:10px;">
      <span style="color:#ffffff !important;-webkit-text-fill-color:#ffffff;">
        Schrijf je gratis in
      </span>
    </a>
  </div>
</td>
</tr>

<tr>
<td style="font-family:Arial,Helvetica,sans-serif;padding-top:28px;">
  <div style="font-size:19px;font-weight:800;color:#132230;margin-bottom:7px;">
    Hebben we iets gemist?
  </div>
  <div style="font-size:14px;line-height:1.55;color:#59635d;margin-bottom:18px;">
    Organiseer je iets, verandert er iets in je straat of speelt er iets dat
    buurtgenoten moeten weten? Mail je tip naar
    <a href="mailto:buurtdezeweek@buttondown.email"
       style="color:#155eef;">buurtdezeweek@buttondown.email</a>.
  </div>
  <a href="{esc(online_url)}"
     style="display:inline-block;background:#155eef;color:#ffffff !important;
            -webkit-text-fill-color:#ffffff;text-decoration:none;
            font-size:14px;font-weight:800;padding:11px 16px;border-radius:11px;">
    <span style="color:#ffffff !important;-webkit-text-fill-color:#ffffff;">
      Bekijk deze editie online
    </span>
  </a>
</td>
</tr>

<tr>
<td style="font-family:Arial,Helvetica,sans-serif;padding-top:32px;
           font-size:11px;line-height:1.5;color:#7a817d;">
  Buurt deze week · pilot Zuidoost-Enschede
</td>
</tr>

</table>
</td>
</tr>
</table>
</div>"""


def make_payload(data, parsed_date):
    date_label = f"{parsed_date.day} {MONTHS[parsed_date.month - 1]} {parsed_date.year}"
    slug = f"buurt-deze-week-{parsed_date:%Y-%m-%d}"
    return {
        "subject": data["edition"].get("email_subject") or f"Buurt deze week · {date_label}",
        "slug": slug,
        "body": build_body(data, parsed_date),
        "status": "draft",
        "canonical_url": SITE_URL,
        "description": data["edition"].get("email_preheader") or data["edition"].get("intro", ""),
        "metadata": {
            "generator": "buurtdezeweek-github",
            "edition_date": parsed_date.isoformat(),
        },
    }


def headers(api_key):
    return {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "X-API-Version": API_VERSION,
    }


def find_existing(api_key, payload):
    # The subject can change while editing an edition, so use the stable
    # edition slug to find the existing Buttondown draft.
    response = requests.get(
        API_URL,
        headers=headers(api_key),
        params={
            "status": "draft",
            "ordering": "-modification_date",
            "page_size": 100,
        },
        timeout=30,
    )
    response.raise_for_status()

    for email in response.json().get("results", []):
        if email.get("slug") == payload["slug"]:
            return email
    return None


def create_or_update(api_key, payload):
    existing = find_existing(api_key, payload)

    if existing:
        if existing.get("status") != "draft":
            print(
                f"Editie bestaat al in Buttondown met status "
                f"{existing.get('status')!r}; niets overschreven."
            )
            return

        response = requests.patch(
            f"{API_URL}/{existing['id']}",
            headers=headers(api_key),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        print(f"Buttondown-draft bijgewerkt: {payload['subject']}")
        return

    response = requests.post(
        API_URL,
        headers=headers(api_key),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    print(f"Buttondown-draft aangemaakt: {payload['subject']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--edition", default="editie-site.json")
    parser.add_argument("--source-edition")
    parser.add_argument("--preview")
    args = parser.parse_args()

    data, parsed_date = load_edition(args.edition)
    if args.source_edition:
        source, source_date = load_edition(args.source_edition)
        generated_items = [(s["id"], i["title"], i["summary"], i["url"]) for s in data["sections"] for i in s["items"]]
        source_items = [(s["id"], i["title"], i["summary"], i["url"]) for s in source["sections"] for i in s["items"]]
        if source_date != parsed_date or generated_items != source_items:
            raise ValueError("editie-site.json hoort niet bij de huidige editie.json. Bouw eerst de site.")
    payload = make_payload(data, parsed_date)

    if args.preview:
        body = payload["body"].replace(
            "<!-- buttondown-editor-mode: fancy -->", "", 1
        )
        Path(args.preview).write_text(body, encoding="utf-8")
        print(f"Preview geschreven naar {args.preview}")
        return

    api_key = os.environ.get("BUTTONDOWN_API_KEY")
    if not api_key:
        print("BUTTONDOWN_API_KEY ontbreekt.", file=sys.stderr)
        sys.exit(2)

    create_or_update(api_key, payload)


if __name__ == "__main__":
    main()
