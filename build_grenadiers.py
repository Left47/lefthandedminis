#!/usr/bin/env python3
"""Build the Holy Hand Grenadiers Blood Bowl match report section.

Kept separate from the Instagram gallery (build.py): its own data, pages and
nav. Reads grenadiers/season<N>.json and writes:
  grenadiers/index.html              season landing page
  grenadiers/s<N>/md<M>/index.html   one shareable page per match

Run after adding or editing a match:  python3 build_grenadiers.py
Photos for a match go in grenadiers/s<N>/md<M>/ and are listed in the JSON.
"""
import glob, html, json, os, re
from PIL import Image

SITE_URL = "https://left47.github.io/lefthandedminis/"
ROOT = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.join(ROOT, 'grenadiers')
E = lambda s: html.escape(str(s), quote=True)
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Anton&family=Lato:wght@400;700;900&display=swap" rel="stylesheet">')


def md(s):
    """Tiny inline markdown: **bold** and *italic*, HTML-escaped."""
    s = E(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)


def result(m):
    return 'W' if m['for'] > m['against'] else 'L' if m['for'] < m['against'] else 'D'


def size(path):
    try:
        return Image.open(path).size
    except Exception:
        return ('', '')


def head(title, desc, url, rel, image, image_size):
    w, h = image_size
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(url)}">
<meta property="og:site_name" content="Holy Hand Grenadiers · Blood Bowl">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(url)}">
<meta property="og:type" content="article">
<meta property="og:image" content="{E(image)}">
{f'<meta property="og:image:width" content="{w}"><meta property="og:image:height" content="{h}">' if w else ''}
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#BA1B2B">
<link rel="icon" type="image/png" href="{rel}assets/favicon.png">
{FONTS}
<link rel="stylesheet" href="{rel}assets/site.css">
<link rel="stylesheet" href="{rel}grenadiers/grenadiers.css">
</head>
<body class="hhg">
<nav class="topnav hhg-nav" aria-label="Section">
  <div class="wrap">
    <a class="brand" href="{rel}grenadiers/"><span class="crest" aria-hidden="true">⚜</span><span>Holy Hand Grenadiers</span></a>
    <a class="home-link" href="{rel}">Left-Handed Minis ↗</a>
  </div>
</nav>
'''


def foot(rel, data):
    return f'''<footer>
  <div class="wrap">
    <span>Coach {E(data['coach'])} · {E(data['league'])}, Season {data['season']} · <a href="{E(data['tourplay'])}" rel="noopener">TourPlay roster</a></span>
    <span>Painted and played by <a href="{rel}">Left-Handed Minis</a></span>
  </div>
</footer>
</body>
</html>
'''


def fig(src, alt, w, h, lazy=True):
    load = ' loading="lazy"' if lazy else ' fetchpriority="high"'
    return f'<figure><img src="{E(src)}" alt="{E(alt)}" width="{w}" height="{h}"{load}></figure>'


def build_match(data, m, prev, nxt):
    s = data['season']
    rel = '../../../'
    folder = f"grenadiers/s{s}/md{m['md']}"
    url = f"{SITE_URL}{folder}/"
    r = result(m)
    score = f"{m['for']}–{m['against']}"
    title = f"MD{m['md']}: Grenadiers {score} {m['opponent']} | Blood Bowl match report"
    photos = m.get('photos') or []
    if photos:
        cover = m.get('cover', photos[0]['file'])
        lead_src, lead_path = cover, os.path.join(ROOT, folder, cover)
        og = url + cover
    else:
        lead_src, lead_path = f'{rel}grenadiers/assets/team.jpg', os.path.join(SEC, 'assets/team.jpg')
        og = SITE_URL + 'grenadiers/assets/team.jpg'
    lead_size = size(lead_path)
    desc = f"{data['league']} S{s}, Matchday {m['md']}: {data['team']} {score} {m['opponent']} ({m['race']}). {m['summary']}"

    booth = '\n'.join(
        f'<p class="line {spk.lower()}"><span class="spk">{E(spk)}</span><span class="said">{md(txt)}</span></p>'
        for spk, txt in m['broadcast'])

    if photos:
        tiles = ''.join(
            f'<a class="tile{" big" if p["file"] == lead_src else ""}" href="{E(p["file"])}"><img src="{E(p["file"])}" alt="{E(p["alt"])}"'
            + (' fetchpriority="high"' if p['file'] == lead_src else ' loading="lazy"') + '></a>'
            for p in sorted(photos, key=lambda p: p['file'] != lead_src))
        collage = f'<section class="wrap collage-wrap"><div class="collage n{min(len(photos), 7)}">{tiles}</div></section>'
    else:
        collage = ('<section class="wrap collage-wrap"><div class="collage n1">'
                   f'<span class="tile big"><img src="{lead_src}" alt="The Holy Hand Grenadiers knights on their bases" fetchpriority="high"></span></div>'
                   '<p class="no-photos">No match photos from this one. Here\'s the squad instead.</p></section>')

    spp = ''.join(f'<tr><td>{md(n)}</td><td>{md(ev)}</td><td class="num">{f"+{v}" if v else "0"}</td></tr>' for n, ev, v in m['spp'])
    blocks = [f'<div class="box"><h2>Scoring &amp; SPP</h2><table><thead><tr><th>Player</th><th>Events</th><th class="num">SPP</th></tr></thead><tbody>{spp}</tbody></table>'
              + (''.join(f'<p class="skill">⭐ {md(x)}</p>' for x in m.get('skills', []))) + '</div>']
    if m.get('timeline'):
        rows = ''.join(f'<tr><td class="t">{E(t)}</td><td>{md(ev)}</td><td class="num">{E(sc)}</td></tr>' for t, ev, sc in m['timeline'])
        note = f'<p class="small">{E(m["timeline_note"])}</p>' if m.get('timeline_note') else ''
        blocks.append(f'<div class="box wide"><h2>Timeline</h2><table><thead><tr><th>{E(m.get("timeline_label", "Turn"))}</th><th>Event</th><th class="num">HG–Opp</th></tr></thead><tbody>{rows}</tbody></table>{note}</div>')
    inj = ''.join(f'<li>{md(x)}</li>' for x in m.get('injuries', []))
    cas = f'<p class="small">Casualties: {E(m["casualties"])}</p>' if m.get('casualties') else ''
    blocks.append(f'<div class="box"><h2>The infirmary</h2><ul>{inj}</ul>{cas}</div>')
    if m.get('standouts'):
        blocks.append('<div class="box"><h2>Credit where it\'s due</h2><ul>' + ''.join(f'<li>{md(x)}</li>' for x in m['standouts']) + '</ul></div>')
    blocks.append('<div class="box"><h2>On TourPlay</h2><ul>'
                  f'<li><a href="{E(m["tourplay_match"])}" rel="noopener">Full match record ↗</a></li>'
                  f'<li><a href="{E(m["opponent_url"])}" rel="noopener">{E(m["opponent"])} team page ↗</a></li>'
                  f'<li><a href="{E(data["tourplay"])}" rel="noopener">{E(data["team"])} team page ↗</a></li>'
                  f'<li><a href="{E(data["league_url"])}" rel="noopener">{E(data["league"])} S{s} ↗</a></li></ul></div>')
    if m.get('facts'):
        blocks.append('<div class="box"><h2>Match facts</h2><dl>' + ''.join(f'<dt>{E(k)}</dt><dd>{E(v)}</dd>' for k, v in m['facts']) + '</dl></div>')

    pn = '<nav class="wrap pn" aria-label="Other matches">' + \
         (f'<a href="../md{prev["md"]}/">← MD{prev["md"]} vs {E(prev["opponent"])}</a>' if prev else '<span></span>') + \
         f'<a href="../../">Season {s}</a>' + \
         (f'<a href="../md{nxt["md"]}/">MD{nxt["md"]} vs {E(nxt["opponent"])} →</a>' if nxt else '<span></span>') + '</nav>'

    body = f'''<header class="hhg-hero">
  <div class="wrap">
    <p class="kicker">{E(data['league'])} · Season {s} · Matchday {m['md']}</p>
    <div class="board">
      <div class="side us"><a class="name" href="{E(data['tourplay'])}" rel="noopener">{E(data['team'])}</a><span class="race">{E(data['race'])}</span></div>
      <div class="score"><span>{m['for']}</span><i>–</i><span>{m['against']}</span></div>
      <div class="side them"><a class="name" href="{E(m['opponent_url'])}" rel="noopener">{E(m['opponent'])}</a><span class="race">{E(m['race'])}</span></div>
    </div>
    <p class="meta"><span class="res {r}">{'Win' if r == 'W' else 'Loss' if r == 'L' else 'Draw'}</span> {E(m['venue'])} · {E(m['weather'])} <a class="tp" href="{E(m['tourplay_match'])}" rel="noopener">Match on TourPlay ↗</a></p>
  </div>
</header>
<main>
{collage}
<section class="wrap lead"><p class="summary">{E(m['summary'])}</p></section>
<section class="wrap booth">
  <h2><span class="onair">On air</span> Cabalvision match report</h2>
  <p class="callers">With Jim Johnson and Bob Bifford</p>
  {booth}
</section>
<section class="wrap boxes">{''.join(blocks)}</section>
</main>
{pn}
'''
    out = os.path.join(ROOT, folder, 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(head(title, desc, url, rel, og, lead_size) + body + foot(rel, data))


def build_index(data):
    s = data['season']
    rel = '../'
    ms = data['matches']
    w = sum(result(m) == 'W' for m in ms); l = sum(result(m) == 'L' for m in ms); d = len(ms) - w - l
    tf = sum(m['for'] for m in ms); ta = sum(m['against'] for m in ms)
    cards = []
    for m in reversed(ms):
        r = result(m)
        if m.get('photos'):
            cov = m.get('cover', m['photos'][0]['file'])
            src = f"s{s}/md{m['md']}/{cov}"; alt = next(p['alt'] for p in m['photos'] if p['file'] == cov)
        else:
            src = 'assets/team.jpg'; alt = 'The Holy Hand Grenadiers knights on their bases'
        cards.append(f'''<a class="card match" href="s{s}/md{m['md']}/">
  <div class="img"><img loading="lazy" src="{E(src)}" alt="{E(alt)}"><span class="kind">Matchday {m['md']}</span></div>
  <div class="meta"><h3>vs {E(m['opponent'])}</h3>
    <div class="sub"><span class="res {r}">{r} {m['for']}–{m['against']}</span><span>{E(m['race'])}</span></div>
    <p class="blurb">{E(m['summary'])}</p>
  </div>
</a>''')
    title = f"{data['team']} · Blood Bowl Season {s} match reports"
    desc = f"{data['intro']} Record {w}–{l}–{d}."
    team = os.path.join(SEC, 'assets/team.jpg')
    body = f'''<header class="hhg-hero home">
  <div class="wrap">
    <p class="kicker">{E(data['league'])} · Season {s}</p>
    <h1>{E(data['team'])}</h1>
    <p class="intro">{E(data['intro'])}</p>
    <div class="stats">
      <div><b>{w}–{l}–{d}</b><span>Record</span></div>
      <div><b>{tf}–{ta}</b><span>Touchdowns</span></div>
      <div><b>{len(ms)}</b><span>Matches reported</span></div>
    </div>
  </div>
</header>
<main class="wrap">
  <div class="section-head"><h2>Match reports</h2></div>
  <div class="grid">{''.join(cards)}</div>
  <div class="box opp-list"><h2>This season's opponents</h2><ul>{''.join(f'<li>MD{m["md"]}: <a href="{E(m["opponent_url"])}" rel="noopener">{E(m["opponent"])}</a> ({E(m["race"])}) · <a href="{E(m["tourplay_match"])}" rel="noopener">match ↗</a></li>' for m in ms)}</ul>
    <p class="small"><a href="{E(data['league_url'])}" rel="noopener">{E(data['league'])} on TourPlay ↗</a></p></div>
</main>
'''
    open(os.path.join(SEC, 'index.html'), 'w').write(
        head(title, desc, SITE_URL + 'grenadiers/', rel, SITE_URL + 'grenadiers/assets/team.jpg', size(team)) + body + foot(rel, data))


def main():
    for path in sorted(glob.glob(os.path.join(SEC, 'season*.json'))):
        data = json.load(open(path))
        ms = sorted(data['matches'], key=lambda m: m['md'])
        data['matches'] = ms
        for i, m in enumerate(ms):
            build_match(data, m, ms[i - 1] if i else None, ms[i + 1] if i + 1 < len(ms) else None)
        build_index(data)
        print(f"Season {data['season']}: {len(ms)} match pages")


if __name__ == '__main__':
    main()
