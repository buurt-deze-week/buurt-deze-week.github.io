#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

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


def email_item(item):
    style = item.get("label_style", "blue")
    palette = {
        "blue": ("#0d3f9b", "#eaf1ff"),
        "green": ("#2f7d59", "#edf7f1"),
        "orange": ("#b65f20", "#fff1e7"),
    }
    fg, bg = palette.get(style, palette["blue"])

    label = ""
    if item.get("label"):
        label = (
            f'<span style="display:inline-block;margin-top:9px;'
            f'font-size:11px;font-weight:900;text-transform:uppercase;'
            f'letter-spacing:.05em;color:{fg};background:{bg};'
            f'padding:5px 8px;border-radius:999px;">'
            f'{esc(item["label"])}</span>'
        )

    source = (
        f'<span style="font-size:12px;color:#6b7280;">'
        f'&nbsp;·&nbsp; {esc(item["source"])}</span>'
    )

    return f"""
      <tr>
        <td style="padding:0 0 20px 0;">
          <a href="{esc(item["url"])}"
             style="display:block;text-decoration:none;color:#132230;">
            <div style="font-family:Arial,Helvetica,sans-serif;
                        font-size:17px;line-height:1.28;font-weight:800;
                        letter-spacing:-.2px;margin:0 0 6px 0;">
              {esc(item["title"])}
              <span style="color:#155eef;">›</span>
            </div>
            <div style="font-family:Arial,Helvetica,sans-serif;
                        font-size:14px;line-height:1.5;color:#5a6570;
                        margin:0 0 2px 0;">
              {esc(item["summary"])}
            </div>
          </a>
          <div>{label}{source}</div>
        </td>
      </tr>
    """


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
        items_html = "".join(email_item(item) for item in section["items"])
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

    count_line = (
        f'Gratis &nbsp;·&nbsp; {len(sources)} lokale bronnen '
        f'&nbsp;·&nbsp; {len(items)} berichten'
    )

    return f"""<!-- buttondown-editor-mode: fancy -->
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
     style="display:inline-block;background:#155eef;color:#fff;text-decoration:none;
            font-size:14px;font-weight:800;padding:11px 16px;border-radius:11px;">
    Bekijk deze editie online
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
        "subject": f"Buurt deze week · {date_label}",
        "slug": slug,
        "body": build_body(data, parsed_date),
        "status": "draft",
        "canonical_url": SITE_URL,
        "description": data["edition"].get("intro", ""),
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
    response = requests.get(
        API_URL,
        headers=headers(api_key),
        params={
            "subject": payload["subject"],
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
    parser.add_argument("--edition", default="editie.json")
    parser.add_argument("--preview")
    args = parser.parse_args()

    data, parsed_date = load_edition(args.edition)
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
