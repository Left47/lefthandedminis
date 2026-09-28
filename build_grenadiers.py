#!/usr/bin/env python3
"""Build the Holy Hand Grenadiers Blood Bowl match report section.

Kept separate from the Instagram gallery (build.py): its own data, pages and
nav. Reads grenadiers/season<N>.json and writes:
  grenadiers/index.html              season landing page
  grenadiers/s<N>/md<M>/index.html   one shareable page per match

Run after adding or editing a match:  python3 build_grenadiers.py
Photos for a match go in grenadiers/s<N>/md<M>/ and are listed in the JSON.
"""
import glob, hashlib, html, json, os, re
from PIL import Image, ImageDraw, ImageFont, ImageOps

SITE_URL = "https://www.lefthandedminis.com/"
ROOT = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.join(ROOT, 'grenadiers')
E = lambda s: html.escape(str(s), quote=True)
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Anton&family=Lato:wght@400;700;900&display=swap" rel="stylesheet">')


FONT_DIR = os.path.join(SEC, 'assets', 'fonts')
INK, SLATE, SLATE_DEEP, GOLD, CRIMSON, WIN = '#212121', '#34496A', '#24344F', '#E3B341', '#BA1B2B', '#1E8E4E'
CARD_W, CARD_H, PANEL_W = 1200, 630, 470


def font(name, px):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), px)


def fill(path, w, h):
    """Center-crop an image to exactly w x h."""
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.45))


def photo_block(paths, w, h):
    """Lay 1-3 photos into a w x h block: one big, up to two stacked beside it."""
    block = Image.new('RGB', (w, h), INK)
    gap = 6
    if len(paths) == 1:
        block.paste(fill(paths[0], w, h), (0, 0))
    elif len(paths) == 2:
        half = (w - gap) // 2
        block.paste(fill(paths[0], half, h), (0, 0))
        block.paste(fill(paths[1], w - half - gap, h), (half + gap, 0))
    else:
        big = int(w * 0.62)
        small_w, small_h = w - big - gap, (h - gap) // 2
        block.paste(fill(paths[0], big, h), (0, 0))
        block.paste(fill(paths[1], small_w, small_h), (big + gap, 0))
        block.paste(fill(paths[2], small_w, h - small_h - gap), (big + gap, small_h + gap))
    return block


def wrap(draw, text, f, max_w):
    words, lines, cur = text.split(), [], ''
    for wd in words:
        t = f'{cur} {wd}'.strip()
        if draw.textlength(t, font=f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = wd
    return lines + ([cur] if cur else [])


def fit_lines(draw, text, name, start_px, max_w, max_lines, min_px=26):
    px = start_px
    while px > min_px:
        f = font(name, px)
        lines = wrap(draw, text, f, max_w)
        if len(lines) <= max_lines and all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f, lines
        px -= 2
    f = font(name, min_px)
    return f, wrap(draw, text, f, max_w)[:max_lines]


def panel(kicker, headline, score_text, sub, pill=None):
    """Right-hand slate panel with gold halftone, kicker, big gold score box and a name."""
    p = Image.new('RGB', (PANEL_W, CARD_H), SLATE)
    d = ImageDraw.Draw(p)
    for y in range(0, CARD_H, 16):
        for x in range(0, PANEL_W, 16):
            r = 2.2 * (x / PANEL_W) ** 1.4
            if r > 0.4:
                d.ellipse((x - r, y - r, x + r, y + r), fill='#46597a')
    pad = 40
    d.text((pad, 42), kicker.upper(), font=font('Lato-Black.ttf', 22), fill=GOLD)
    hf, hl = fit_lines(d, headline.upper(), 'Anton-Regular.ttf', 40, PANEL_W - 2 * pad, 2)
    y = 82
    for line in hl:
        d.text((pad, y), line, font=hf, fill='white'); y += int(hf.size * 1.18)
    sf = font('Anton-Regular.ttf', 132)
    tw = d.textlength(score_text, font=sf)
    bx0, by0 = pad, y + 18
    box = (bx0, by0, bx0 + tw + 56, by0 + 176)
    d.rectangle((box[0] + 8, box[1] + 8, box[2] + 8, box[3] + 8), fill=INK)
    d.rectangle(box, fill=GOLD, outline=INK, width=5)
    d.text((bx0 + 28, by0 + 4), score_text, font=sf, fill=INK)
    if pill:
        label, color = pill
        pf = font('Lato-Black.ttf', 22)
        pw = d.textlength(label, font=pf) + 28
        px0, py0 = box[2] + 26, box[3] - 44
        if px0 + pw > PANEL_W - 10:
            px0, py0 = bx0, box[3] + 20
        d.rectangle((px0, py0, px0 + pw, py0 + 40), fill=color, outline=INK, width=3)
        d.text((px0 + 14, py0 + 7), label, font=pf, fill='white')
    sf2, sl = fit_lines(d, sub.upper(), 'Anton-Regular.ttf', 44, PANEL_W - 2 * pad, 2)
    yy = CARD_H - 40 - len(sl) * int(sf2.size * 1.15)
    for line in sl:
        d.text((pad, yy), line, font=sf2, fill='white'); yy += int(sf2.size * 1.15)
    return p


def save_card(photos_block, pnl, out):
    card = Image.new('RGB', (CARD_W, CARD_H), INK)
    card.paste(photos_block, (0, 0))
    card.paste(pnl, (CARD_W - PANEL_W, 0))
    ImageDraw.Draw(card).rectangle((CARD_W - PANEL_W - 6, 0, CARD_W - PANEL_W - 1, CARD_H), fill=INK)
    card.save(out, 'JPEG', quality=84, optimize=True, progressive=True)
    return hashlib.md5(open(out, 'rb').read()).hexdigest()[:8]


def match_card(data, m, folder):
    photos = m.get('photos') or []
    cover = m.get('cover', photos[0]['file']) if photos else None
    order = ([cover] + [p['file'] for p in photos if p['file'] != cover])[:3] if photos else []
    paths = [os.path.join(ROOT, folder, f) for f in order] or [os.path.join(SEC, 'assets/team.jpg')]
    r = result(m)
    pill = {'W': ('WIN', WIN), 'L': ('LOSS', CRIMSON), 'D': ('DRAW', '#8A6D00')}[r]
    pnl = panel(f"Matchday {m['md']} · Season {data['season']}", data['team'],
                f"{m['for']}–{m['against']}", f"vs {m['opponent']}", pill)
    return save_card(photo_block(paths, CARD_W - PANEL_W - 6, CARD_H), pnl, os.path.join(ROOT, folder, 'share.jpg'))


def season_card(data, record):
    s = data['season']
    covers = []
    for m in reversed(data['matches']):
        if m.get('photos'):
            covers.append(os.path.join(ROOT, f"grenadiers/s{s}/md{m['md']}", m.get('cover', m['photos'][0]['file'])))
    covers = covers[:3] or [os.path.join(SEC, 'assets/team.jpg')]
    pnl = panel(f"{data['league']} · S{s}", data['team'], record, f"{len(data['matches'])} match reports")
    return save_card(photo_block(covers, CARD_W - PANEL_W - 6, CARD_H), pnl, os.path.join(SEC, 's%d-share.jpg' % s))


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


def head(title, desc, url, rel, image, image_size, og_title=None, image_alt=''):
    w, h = image_size
    ot = og_title or title
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(url)}">
<meta property="og:site_name" content="Holy Hand Grenadiers · Blood Bowl">
<meta property="og:title" content="{E(ot)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(url)}">
<meta property="og:type" content="article">
<meta property="og:image" content="{E(image)}">
<meta property="og:image:secure_url" content="{E(image)}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="{w}">
<meta property="og:image:height" content="{h}">
<meta property="og:image:alt" content="{E(image_alt or ot)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(ot)}">
<meta name="twitter:description" content="{E(desc)}">
<meta name="twitter:image" content="{E(image)}">
<meta name="twitter:image:alt" content="{E(image_alt or ot)}">
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
    ver = match_card(data, m, folder)
    og, og_size = f"{url}share.jpg?v={ver}", (CARD_W, CARD_H)
    og_title = f"MD{m['md']}: Grenadiers {score} {m['opponent']}"
    desc = m['summary']

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
    box = {}
    box['spp'] = (f'<div class="box"><h2>Scoring &amp; SPP</h2><table><thead><tr><th>Player</th><th>Events</th><th class="num">SPP</th></tr></thead><tbody>{spp}</tbody></table>'
                  + ''.join(f'<p class="skill">⭐ {md(x)}</p>' for x in m.get('skills', [])) + '</div>')
    if m.get('timeline'):
        rows = ''.join(f'<tr><td class="t">{E(t)}</td><td>{md(ev)}</td><td class="num">{E(sc)}</td></tr>' for t, ev, sc in m['timeline'])
        note = f'<p class="small">{E(m["timeline_note"])}</p>' if m.get('timeline_note') else ''
        box['timeline'] = f'<div class="box"><h2>Timeline</h2><table><thead><tr><th>{E(m.get("timeline_label", "Turn"))}</th><th>Event</th><th class="num">HG–Opp</th></tr></thead><tbody>{rows}</tbody></table>{note}</div>'
    inj = ''.join(f'<li>{md(x)}</li>' for x in m.get('injuries', []))
    cas = f'<p class="small">Casualties: {E(m["casualties"])}</p>' if m.get('casualties') else ''
    box['infirmary'] = f'<div class="box"><h2>The infirmary</h2><ul>{inj}</ul>{cas}</div>'
    if m.get('standouts'):
        box['credit'] = '<div class="box"><h2>Credit where it\'s due</h2><ul>' + ''.join(f'<li>{md(x)}</li>' for x in m['standouts']) + '</ul></div>'
    if m.get('facts'):
        box['facts'] = '<div class="box"><h2>Match facts</h2><dl>' + ''.join(f'<dt>{E(k)}</dt><dd>{E(v)}</dd>' for k, v in m['facts']) + '</dl></div>'
    box['tourplay'] = ('<div class="box"><h2>On TourPlay</h2><ul>'
                       f'<li><a href="{E(m["tourplay_match"])}" rel="noopener">Full match record ↗</a></li>'
                       f'<li><a href="{E(m["opponent_url"])}" rel="noopener">{E(m["opponent"])} team page ↗</a></li>'
                       f'<li><a href="{E(data["tourplay"])}" rel="noopener">{E(data["team"])} team page ↗</a></li>'
                       f'<li><a href="{E(data["league_url"])}" rel="noopener">{E(data["league"])} S{s} ↗</a></li></ul></div>')
    # fixed rows so every row fills the width: quick reads, then the timeline, then facts and links
    layout = [['spp', 'infirmary', 'credit'], ['timeline'], ['facts', 'tourplay']]
    blocks = [f'<div class="box-row n{len(r)}">' + ''.join(box[k] for k in r) + '</div>'
              for r in ([k for k in row if k in box] for row in layout) if r]

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
    open(out, 'w').write(head(title, desc, url, rel, og, og_size, og_title,
                              f"Holy Hand Grenadiers {score} {m['opponent']}, Matchday {m['md']}") + body + foot(rel, data))


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
    ver = season_card(data, f"{w}–{l}–{d}")
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
        head(title, desc, SITE_URL + 'grenadiers/', rel, f"{SITE_URL}grenadiers/s{s}-share.jpg?v={ver}", (CARD_W, CARD_H),
             f"{data['team']}: Season {s} match reports", f"{data['team']} Season {s} match reports, record {w}–{l}–{d}") + body + foot(rel, data))


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
