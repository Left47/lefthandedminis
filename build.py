#!/usr/bin/env python3
"""Build the Left-Handed Minis static site from posts/*/post.json and gear.json.

Generates:
  index.html                 home: hero, full gallery grid, about, gear preview
  posts/<slug>/index.html    one crawlable page per post
  games/<slug>/index.html    one page per game
  gear/index.html            full gear list with "seen in" post links
  tips/index.html            hobby tips shelves (from tips/tips.json)
  tips/<slug>/index.html     one long-form guide per tip (from tips/<slug>/article.md)
  posts/<slug>/thumb.jpg     600x750 grid thumbnail (only if missing)
  sitemap.xml, robots.txt

Run after adding or editing a post:  python3 build.py
Review draft tips locally:          python3 build.py --drafts   (never commit that output)
To move to a custom domain, change SITE_URL below and rebuild.
"""
import html, json, os, re, datetime
from PIL import Image, ImageOps

SITE_URL = "https://www.lefthandedminis.com/"
SITE_NAME = "Left-Handed Minis"
ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Anton&family=Lato:wght@400;700;900&display=swap" rel="stylesheet">')
KINDS = {'match-report': 'Match report', 'build': 'Build', 'wip': 'WIP', 'finished': 'Finished', 'game-night': 'Game night',
         'tip': 'Hobby tip', 'roundup': 'Roundup', 'team': 'Team shot'}
LABELS = {'instagram': 'Instagram', 'threads': 'Threads', 'tiktok': 'TikTok', 'bluesky': 'Bluesky'}
SOCIALS = [('Instagram', 'https://instagram.com/lefthandedminis'), ('Threads', 'https://www.threads.net/@lefthandedminis'),
           ('TikTok', 'https://tiktok.com/@lefthandedminis'), ('YouTube', 'https://www.youtube.com/@lefthandedminis'),
           ('Bluesky', 'https://bsky.app/profile/lefthandedminis.bsky.social'), ('Facebook', 'https://www.facebook.com/530614806807869'),
           ('Reddit', 'https://www.reddit.com/user/lefthandedminis')]
E = lambda s: html.escape(str(s), quote=True)
LAZY, EAGER, PRIMARY = ' loading="lazy"', ' fetchpriority="high"', ' class="primary"'


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def fmt_date(d):
    if not d:
        return 'From the archive'
    return datetime.date.fromisoformat(d).strftime('%b %-d, %Y')


def clean_text(t):
    """Caption text without hashtags, mentions, dot-spacer lines, or extra whitespace."""
    t = re.sub(r'(^|\s)[#@][\w.]+', ' ', t)
    t = re.sub(r'^\s*[.•·]\s*$', '', t, flags=re.M)
    return re.sub(r'\s+', ' ', t).strip()


def description(p):
    cap = p['caps'].get('instagram') or next(iter(p['caps'].values()), '')
    t = clean_text(cap)
    if len(t) < 40:
        t = f"{p['title']}: painted {p.get('game', 'tabletop')} miniatures by {SITE_NAME}." + (f' {t}' if t else '')
    if len(t) > 158:
        t = t[:155].rsplit(' ', 1)[0].rstrip(',;:–-') + '…'
    return t


def caption_html(t):
    out = []
    for para in re.split(r'\n\s*\n', t.strip()):
        lines = [l for l in para.split('\n') if not re.fullmatch(r'\s*[.•·]\s*', l)]
        if not lines:
            continue
        s = '<br>'.join(E(l) for l in lines)
        s = re.sub(r'(^|\s|>)#([\w]+)', r'\1<span class="tag">#\2</span>', s)
        s = re.sub(r'(^|\s|>)@([\w.]+[\w])', r'\1<a href="https://instagram.com/\2" rel="noopener">@\2</a>', s)
        out.append(f'<p>{s}</p>')
    return '\n'.join(out)


def head(title, desc, canonical, rel, image=None, extra=''):
    img = image or SITE_URL + 'assets/logo-badge.png'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(canonical)}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(canonical)}">
<meta property="og:image" content="{E(img)}">
<meta property="og:type" content="{'article' if '/posts/' in canonical else 'website'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#004AAD">
<link rel="icon" type="image/png" href="{rel}assets/favicon.png">
<link rel="apple-touch-icon" href="{rel}assets/apple-touch-icon.png">
{FONTS}
<link rel="stylesheet" href="{rel}assets/site.css">
{extra}
</head>
<body>
<nav class="topnav" aria-label="Site">
  <div class="wrap">
    <a class="brand" href="{rel}" aria-label="{SITE_NAME} home"><img src="{rel}assets/logo-fist.png" alt=""><span class="brand-name">{SITE_NAME}</span></a>
    <a href="{rel}#gallery">Gallery</a>{f'{chr(10)}    <a href="{rel}tips/">Tips</a>' if TIPS_LIVE else ''}
    <a href="{rel}#about">About</a>
    <a href="{rel}gear/">Gear</a>
    <a href="{rel}grenadiers/">Blood Bowl League</a>
    <a href="mailto:lefthandedminis@gmail.com">Contact</a>
  </div>
</nav>
'''


def foot(rel):
    return f'''<footer>
  <div class="wrap">
    <img src="{rel}assets/logo-fist.png" alt="">
    <span>Photos &amp; words by {SITE_NAME} · <a href="mailto:lefthandedminis@gmail.com">lefthandedminis@gmail.com</a></span>
  </div>
</footer>
</body>
</html>
'''


def card(p, rel):
    kind = KINDS.get(p.get('type'))
    res = p.get('result')
    return f'''<a class="card" href="{rel}posts/{p['slug']}/" data-game="{E(p.get('game', ''))}">
  <div class="img"><img loading="lazy" src="{rel}posts/{p['slug']}/thumb.jpg" width="600" height="750" alt="{E(p['images'][0].get('alt') or p['title'])}">
    {f'<span class="count">{len(p["images"])} photos</span>' if len(p['images']) > 1 else ''}
    {f'<span class="kind">{kind}</span>' if kind else ''}</div>
  <div class="meta"><h3>{E(p['title'])}</h3>
    <div class="sub">{f'<span class="res {res.strip()[0].upper()}">{E(res)}</span>' if res else ''}<span>{E(p.get('game', ''))}</span><span class="when"><span aria-hidden="true">·</span><span>{fmt_date(p.get('date'))}</span></span></div>
  </div>
</a>'''


def make_thumb(p):
    d = os.path.join(ROOT, 'posts', p['slug'])
    out = os.path.join(d, 'thumb.jpg')
    src = os.path.join(d, p['images'][0]['file'])
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src):
        return
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    ImageOps.fit(im, (600, 750), Image.LANCZOS, centering=(0.5, 0.45)).save(out, quality=80, optimize=True)


def load():
    slugs = json.load(open(os.path.join(ROOT, 'posts', 'index.json')))
    posts = []
    for s in slugs:
        d = os.path.join(ROOT, 'posts', s)
        p = json.load(open(os.path.join(d, 'post.json')))
        p['slug'] = s
        p['caps'] = {}
        for k, f in (p.get('captions') or {}).items():
            fp = os.path.join(d, f)
            if os.path.exists(fp):
                p['caps'][k] = open(fp).read().strip()
        p['search'] = (p['title'] + ' ' + ' '.join(p['caps'].values())).lower()
        # Go-live time: the Instagram slot from Buffer (the gallery mirrors the
        # Instagram feed), else the earliest scheduled channel, else post.json's date.
        buf = p.get('buffer') or {}
        due = (buf.get('instagram') or {}).get('dueAt') or min(
            (v['dueAt'] for v in buf.values() if isinstance(v, dict) and v.get('dueAt')), default=None)
        p['live'] = due or p.get('date') or '0000'
        if due:
            p['date'] = due[:10]
        posts.append(p)
    posts.sort(key=lambda p: (p['live'], p['slug']), reverse=True)
    return posts


def link_gear(posts, gear):
    for gr in gear['groups']:
        for it in gr['items']:
            rx = re.compile(it['match'], re.I)
            it['posts'] = [p for p in posts if rx.search(p['search']) and (not it.get('game') or p.get('game') == it['game'])]
            for p in it['posts']:
                p.setdefault('gear', []).append(it)


def gear_card(it, rel, seen=True):
    seen_html = ''
    if seen and it.get('posts'):
        links = ', '.join(f'<a href="{rel}posts/{q["slug"]}/">{E(q["title"])}</a>' for q in it['posts'][:3])
        more = f' and {len(it["posts"]) - 3} more' if len(it['posts']) > 3 else ''
        seen_html = f'<div class="seen-in">Seen in {links}{more}</div>'
    return f'''<div class="gear-card">
  <strong>{E(it['name'])}</strong>{f'<span>{E(it["note"])}</span>' if it.get('note') else ''}
  <a class="buy" href="{E(it['url'])}" target="_blank" rel="sponsored noopener">View on Amazon →</a>
  {seen_html}
</div>'''


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w').write(text)


def build_post(p, posts, games):
    rel = '../../'
    url = f"{SITE_URL}posts/{p['slug']}/"
    game = p.get('game', '')
    desc = description(p)
    title = f"{p['title']} – {game} | {SITE_NAME}" if game else f"{p['title']} | {SITE_NAME}"
    img0 = url + p['images'][0]['file']
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p['title'], "description": desc,
          "image": [url + im['file'] for im in p['images']], "url": url,
          "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
          "publisher": {"@type": "Organization", "name": SITE_NAME, "logo": {"@type": "ImageObject", "url": SITE_URL + 'assets/logo-badge.png'}}}
    if p.get('date'):
        ld['datePublished'] = p['date']
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": SITE_NAME, "item": SITE_URL},
        {"@type": "ListItem", "position": 2, "name": game, "item": f"{SITE_URL}games/{slugify(game)}/"},
        {"@type": "ListItem", "position": 3, "name": p['title'], "item": url}]}
    extra = (f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
             f'<script type="application/ld+json">{json.dumps(crumbs, ensure_ascii=False)}</script>')
    photos = '\n'.join(
        f'<figure><img src="{im["file"]}" width="{im.get("width", "")}" height="{im.get("height", "")}" alt="{E(im.get("alt") or p["title"])}"'
        + (LAZY if i else EAGER) + '></figure>' for i, im in enumerate(p['images']))
    keys = list(p['caps'])
    if keys:
        main_cap = f'<div class="caption">{caption_html(p["caps"][keys[0]])}</div>'
        others = ''.join(f'<details class="alt-cap"><summary>{LABELS.get(k, k)} caption</summary><div class="caption">{caption_html(p["caps"][k])}</div></details>' for k in keys[1:])
    else:
        main_cap = ''
        others = ''
    meta_bits = [f'<span class="res {p["result"].strip()[0].upper()}">{E(p["result"])}</span>' if p.get('result') else '',
                 f'<a href="{rel}games/{slugify(game)}/">{E(game)}</a>' if game else '',
                 E(p.get('league') or p.get('series') or ''), fmt_date(p.get('date'))]
    meta = ' <span aria-hidden="true">·</span> '.join(b for b in meta_bits if b)
    gear_box = ''
    if p.get('gear'):
        items = ''.join(f'<li><a href="{E(it["url"])}" target="_blank" rel="sponsored noopener">{E(it["name"])}</a><span>{E(it.get("note", ""))}</span></li>' for it in p['gear'])
        gear_box = f'<div class="panel-box"><h2>Gear in this post</h2><ul>{items}</ul><p class="seen-in">Affiliate links. <a href="{rel}gear/">All gear</a></p></div>'
    if p.get('tips'):
        items = ''.join(f'<li><a href="{rel}tips/{t["slug"]}/">{E(t["title"])} →</a><span>{E(t["dek"])}</span></li>' for t in p['tips'])
        gear_box = f'<div class="panel-box guide-box"><h2>The full guide</h2><ul>{items}</ul></div>' + gear_box
    same = [q for q in games[game] if q is not p][:4]
    more = ''
    if same:
        more = f'''<section class="wrap more"><h2>More {E(game)}</h2><div class="grid">{''.join(card(q, rel) for q in same)}</div></section>'''
    i = posts.index(p)
    newer, older = (posts[i - 1] if i > 0 else None), (posts[i + 1] if i + 1 < len(posts) else None)
    pn = '<nav class="wrap pn" aria-label="More posts">' + \
         (f'<a href="{rel}posts/{newer["slug"]}/">← {E(newer["title"])}</a>' if newer else '<span></span>') + \
         (f'<a href="{rel}posts/{older["slug"]}/">{E(older["title"])} →</a>' if older else '<span></span>') + '</nav>'
    body = f'''<div class="wrap crumbs"><a href="{rel}">Home</a> › {f'<a href="{rel}games/{slugify(game)}/">{E(game)}</a> › ' if game else ''}{E(p['title'])}</div>
<article class="wrap post">
  <div class="photos">{photos}</div>
  <div class="post-side">
    <header><div class="sub">{meta}</div><h1>{E(p['title'])}</h1></header>
    {main_cap}{others}
    {gear_box}
  </div>
</article>
{more}
{pn}
'''
    write(f"posts/{p['slug']}/index.html", head(title, desc, url, rel, img0, extra) + body + foot(rel))


def build_game(game, gposts):
    rel = '../../'
    url = f"{SITE_URL}games/{slugify(game)}/"
    n = len(gposts)
    desc = f"{n} painted {game} miniature{'s' if n != 1 else ''} and posts from {SITE_NAME}: finished minis, works in progress, and game nights."
    body = f'''<div class="wrap crumbs"><a href="{rel}">Home</a> › {E(game)}</div>
<header class="wrap page-head"><h1>{E(game)}</h1><p>{E(desc)}</p></header>
<main class="wrap grid" style="padding-top:18px">{''.join(card(p, rel) for p in gposts)}</main>
'''
    write(f"games/{slugify(game)}/index.html", head(f"{game} miniature painting | {SITE_NAME}", desc, url, rel) + body + foot(rel))


def build_gear(gear):
    rel = '../'
    url = SITE_URL + 'gear/'
    desc = "The brushes, tools, and photo gear I actually use for painting and photographing miniatures, with the posts where each one shows up."
    groups = ''.join(f'<h3>{E(gr["name"])}</h3><div class="gear-grid">{"".join(gear_card(it, rel) for it in gr["items"])}</div>' for gr in gear['groups'])
    body = f'''<div class="wrap crumbs"><a href="{rel}">Home</a> › Gear</div>
<section class="gear"><div class="wrap" style="padding-top:18px">
  <h1 class="page-head" style="padding:0"><span style="font-family:Anton,Impact,sans-serif;font-weight:400;text-transform:uppercase;font-size:clamp(34px,7vw,60px)">Gear I use</span></h1>
  <p class="disclosure">{E(gear['disclosure'])}</p>
  {groups}
</div></section>
'''
    write('gear/index.html', head(f"Miniature painting gear I use | {SITE_NAME}", desc, url, rel) + body + foot(rel))


def build_home(posts, games, gear):
    rel = ''
    desc = "Painted miniatures, tabletop game nights, and painting tips from Left-Handed Minis: Marvel United, Blood Bowl, DC United, TMNT, Mass Effect, and more."
    chips = '<a class="chip on" href="#gallery">All</a>' + ''.join(
        f'<a class="chip" href="games/{slugify(g)}/">{E(g)}</a>' for g in sorted(games, key=lambda g: -len(games[g])))
    socials = ''.join(f'<a{PRIMARY if i == 0 else ""} href="{u}" rel="noopener">{n}</a>' for i, (n, u) in enumerate(SOCIALS))
    top_gear = sorted((it for gr in gear['groups'] for it in gr['items']), key=lambda it: -len(it.get('posts', [])))[:4]
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL}
    org_ld = {"@context": "https://schema.org", "@type": "Organization", "name": SITE_NAME, "url": SITE_URL,
              "logo": SITE_URL + 'assets/logo-badge.png', "sameAs": [u for _, u in SOCIALS]}
    extra = (f'<script type="application/ld+json">{json.dumps(site_ld)}</script>\n'
             f'<script type="application/ld+json">{json.dumps(org_ld)}</script>')
    tips_strip = ''
    if TIPS_LIVE:
        firsts = {}
        for t in TIPS_LIVE:
            firsts.setdefault((t['shelf']['id'], t['section']), t)
        picks = (list(firsts.values()) + [t for t in TIPS_LIVE if t not in firsts.values()])[:4]
        tips_strip = f'''<section class="tips-strip" id="tips">
  <div class="wrap">
    <div class="section-head"><h2>Hobby tips</h2><a class="btn" href="tips/">All tips →</a></div>
    <div class="grid tip-grid">{''.join(tip_card(t, rel) for t in picks)}</div>
  </div>
</section>'''
    body = f'''<header class="hero" id="top">
  <div class="wrap">
    <a class="badge" href="{rel}" aria-label="{SITE_NAME} home"><img src="assets/logo-badge.png" width="260" height="132" alt="{SITE_NAME}"></a>
    <h1 class="tagline">Small figures,<span>big adventures</span></h1>
    <p class="intro">Painted miniatures, tabletop game nights, and the occasional painting tip from a lefty who's still learning as he goes.</p>
    <nav class="socials" aria-label="Follow {SITE_NAME}">{socials}</nav>
  </div>
</header>

<section id="gallery">
<div class="wrap section-head">
  <h2>From the hobby table</h2>
  <nav class="filters" aria-label="Browse by game">{chips}</nav>
</div>
<main class="wrap grid" id="grid">
{''.join(card(p, rel) for p in posts)}
</main>
</section>
{tips_strip}
<section class="about" id="about">
  <div class="wrap">
    <figure class="panel">
      <img src="assets/about-first-minis.jpg" loading="lazy" alt="Jim smiling at the table, holding up a painted mini above a Marvel United board full of painted heroes">
      <figcaption>Me with my first minis</figcaption>
    </figure>
    <div>
      <div class="kicker">About</div>
      <h2>Hi, I'm Jim!</h2>
      <p>I'm a tech professional by day, an amateur miniature painter by night, and a dad all the time. My painting journey began in 2023 after a paint-and-take session at SDCC sparked my interest. Since then, I've focused on bringing characters from board games like Marvel United and X-Men to life with color and creativity.</p>
      <p>I live in Cary, NC, with my wonderful wife, two energetic young daughters, and our sweet old rescue poodle. Painting miniatures has become a fulfilling way to unwind, challenge myself, and add a personal touch to our favorite games.</p>
      <p><a href="mailto:lefthandedminis@gmail.com">lefthandedminis@gmail.com</a></p>
    </div>
  </div>
</section>

<section class="gear" id="gear">
  <div class="wrap">
    <h2>Gear I use</h2>
    <p class="disclosure">{E(gear['disclosure'])}</p>
    <div class="gear-grid">{''.join(gear_card(it, rel) for it in top_gear)}</div>
    <p style="margin-top:18px"><a class="btn" href="gear/" style="text-decoration:none;display:inline-block">See all the gear →</a></p>
  </div>
</section>
'''
    write('index.html', head(f"{SITE_NAME} | Miniature painting & tabletop games", desc, SITE_URL, rel, extra=extra) + body + foot(rel))


# ---------------------------------------------------------------- hobby tips
# Long-form guides live in tips/<slug>/article.md, with metadata and shelf order
# in tips/tips.json. Only tips with "status": "live" are built; run
# `python3 build.py --drafts` to also render drafts (with their [[gap: ...]]
# notes shown) for review. Never commit a --drafts build.
# Inside article.md:  ![alt](post:<post-slug>/02.jpg "caption")  or  ![alt](img:<file>.jpg "caption")
# for images (img: files live in tips/img/), and [[gap: note]] on its own line for
# questions still open (shown in drafts, stripped from live pages).

TIPS_LIVE = []   # filled by load_tips(); drives the nav link and home strip
GAP_RE = re.compile(r'^\[\[gap:\s*(.*?)\]\]\s*$', re.M | re.S)
IMG_RE = re.compile(r'^!\[([^\]]*)\]\((post|img):([^\s)]+)(?:\s+"([^"]*)")?\)\s*$', re.M)


def tip_src(kind, path):
    """(path relative to ROOT, site path) for a post: or img: reference."""
    rp = f'posts/{path}' if kind == 'post' else f'tips/img/{path}'
    if not os.path.exists(os.path.join(ROOT, rp)):
        raise SystemExit(f'tips: missing image {rp}')
    return rp


def img_size(rp):
    with Image.open(os.path.join(ROOT, rp)) as im:
        return ImageOps.exif_transpose(im).size


def render_article(md_text, rel, drafts, slug, skip=None):
    import markdown  # pip install markdown
    gaps = GAP_RE.findall(md_text)
    cover_cap = []
    if drafts:
        md_text = GAP_RE.sub(lambda m: f'\n<aside class="gap"><strong>Draft gap</strong> {E(m.group(1))}</aside>\n', md_text)
    else:
        if gaps:
            print(f'  WARNING {slug}: {len(gaps)} unresolved [[gap]] note(s) stripped from the live page')
        md_text = GAP_RE.sub('', md_text)

    def fig(m):
        alt, kind, path, cap = m.groups()
        rp = tip_src(kind, path)
        w, h = img_size(rp)
        if rp == skip:
            cover_cap.append(cap or '')
            return ''  # already shown as the page's cover image
        c = f'<figcaption>{E(cap)}</figcaption>' if cap else ''
        shape = ' tall' if h > w * 1.05 else ''
        return f'\n<figure class="tip-fig{shape}"><img src="{rel}{rp}" width="{w}" height="{h}" alt="{E(alt)}" loading="lazy">{c}</figure>\n'
    md_text = IMG_RE.sub(fig, md_text)
    return markdown.markdown(md_text, extensions=['extra', 'sane_lists']), len(gaps), (cover_cap or [''])[0]


def load_tips(drafts):
    cfg = json.load(open(os.path.join(ROOT, 'tips', 'tips.json')))
    tips = []
    for shelf in cfg['shelves']:
        for sec in shelf['sections']:
            for slug in sec['tips']:
                t = dict(cfg['tips'][slug], slug=slug, shelf=shelf, section=sec['name'])
                if t.get('status') != 'live' and not drafts:
                    continue
                t['md'] = open(os.path.join(ROOT, 'tips', slug, 'article.md')).read()
                kind, path = t['cover'].split(':', 1)
                t['cover_rp'] = tip_src(kind, path)
                t['updated'] = t.get('updated') or datetime.date.today().isoformat()
                tips.append(t)
    return cfg, tips


def make_tip_card(t):
    out = os.path.join(ROOT, 'tips', t['slug'], 'card.jpg')
    src = os.path.join(ROOT, t['cover_rp'])
    if os.path.exists(out) and os.path.getmtime(out) >= max(os.path.getmtime(src), os.path.getmtime(os.path.join(ROOT, 'tips', 'tips.json'))):
        return
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    ImageOps.fit(im, (800, 600), Image.LANCZOS, centering=(0.5, t.get('focus', 0.4))).save(out, quality=80, optimize=True)


def tip_card(t, rel):
    return f'''<a class="card tip-card" href="{rel}tips/{t['slug']}/">
  <div class="img"><img loading="lazy" src="{rel}tips/{t['slug']}/card.jpg" width="800" height="600" alt="">
    <span class="kind">{E(t['section'])}</span></div>
  <div class="meta"><h3>{E(t['title'])}</h3><p class="dek">{E(t['dek'])}</p></div>
</a>'''


def build_tip(t, by_slug, posts_by_slug, gear_by_id, drafts):
    rel = '../../'
    url = f"{SITE_URL}tips/{t['slug']}/"
    body_html, ngaps, cover_cap = render_article(t['md'], rel, drafts, t['slug'], skip=t['cover_rp'])
    cover = SITE_URL + t['cover_rp']
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": t['title'], "description": t['dek'],
          "image": [cover], "url": url, "dateModified": t['updated'],
          "author": {"@type": "Person", "name": "Jim", "url": SITE_URL + '#about'},
          "publisher": {"@type": "Organization", "name": SITE_NAME, "logo": {"@type": "ImageObject", "url": SITE_URL + 'assets/logo-badge.png'}}}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": SITE_NAME, "item": SITE_URL},
        {"@type": "ListItem", "position": 2, "name": "Tips", "item": SITE_URL + 'tips/'},
        {"@type": "ListItem", "position": 3, "name": t['title'], "item": url}]}
    extra = (f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
             f'<script type="application/ld+json">{json.dumps(crumbs, ensure_ascii=False)}</script>')
    if drafts and t.get('status') != 'live':
        extra += '\n<meta name="robots" content="noindex">'
    w, h = img_size(t['cover_rp'])
    side = []
    seen = [posts_by_slug[s] for s in t.get('posts', []) if s in posts_by_slug]
    if seen:
        items = ''.join(f'''<li><a href="{rel}posts/{p['slug']}/"><img src="{rel}posts/{p['slug']}/thumb.jpg" width="600" height="750" alt="" loading="lazy"><span><strong>{E(p['title'])}</strong><em>{E(p.get('game', ''))} · {fmt_date(p.get('date'))}</em></span></a></li>''' for p in seen)
        side.append(f'<div class="panel-box seen-posts"><h2>As seen on Instagram</h2><ul>{items}</ul></div>')
    gear = [gear_by_id[g] for g in t.get('gear', []) if g in gear_by_id]
    if gear:
        items = ''.join(f'<li><a href="{E(it["url"])}" target="_blank" rel="sponsored noopener">{E(it["name"])}</a><span>{E(it.get("note", ""))}</span></li>' for it in gear)
        side.append(f'<div class="panel-box"><h2>Gear in this guide</h2><ul>{items}</ul><p class="seen-in">Affiliate links, so using them supports me. <a href="{rel}gear/">All gear</a></p></div>')
    related = [by_slug[s] for s in t.get('related', []) if s in by_slug]
    if related:
        items = ''.join(f'<li><a href="{rel}tips/{r["slug"]}/">{E(r["title"])}</a><span>{E(r["dek"])}</span></li>' for r in related)
        side.append(f'<div class="panel-box"><h2>Keep going</h2><ul>{items}</ul></div>')
    banner = ''
    if drafts and t.get('status') != 'live':
        banner = f'<div class="wrap"><p class="draft-banner">Draft preview · {ngaps} open question{"s" if ngaps != 1 else ""} · not on the live site</p></div>'
    body = f'''<div class="wrap crumbs"><a href="{rel}">Home</a> › <a href="{rel}tips/">Tips</a> › {E(t['section'])}</div>
{banner}
<header class="wrap tip-head">
  <div class="tip-head-text">
    <div class="kicker">{E(t['shelf']['title'])} · {E(t['section'])}</div>
    <h1>{E(t['title'])}</h1>
    <p class="dek">{E(t['dek'])}</p>
  </div>
  <figure class="tip-cover"><img src="{rel}{t['cover_rp']}" width="{w}" height="{h}" alt="" fetchpriority="high" style="object-position:50% {int(t.get('focus', 0.4) * 100)}%">{f'<figcaption>{E(cover_cap)}</figcaption>' if cover_cap else ''}</figure>
</header>
<div class="wrap tip-layout">
  <article class="prose">
{body_html}
  </article>
  <aside class="tip-side">{''.join(side)}</aside>
</div>
'''
    write(f"tips/{t['slug']}/index.html", head(f"{t['title']} | {SITE_NAME}", t['dek'], url, rel, cover, extra) + body + foot(rel))


def build_tips_index(cfg, tips):
    rel = '../'
    url = SITE_URL + 'tips/'
    desc = "Hobby tips from Left-Handed Minis: beginner painting, contrast, color, OSL, basing, budget mini photography, priming, magnetizing and storage."
    groups = ''
    for shelf in cfg['shelves']:
        st = [t for t in tips if t['shelf']['id'] == shelf['id']]
        if not st:
            continue
        secs = ''
        for sec in shelf['sections']:
            cards = [t for t in st if t['section'] == sec['name']]
            if cards:
                secs += f'<h3 class="shelf-sec">{E(sec["name"])}</h3><div class="grid tip-grid">{"".join(tip_card(t, rel) for t in cards)}</div>'
        groups += f'''<section class="shelf" id="{E(shelf['id'])}">
  <div class="shelf-head"><div class="kicker">{E(shelf['kicker'])}</div><h2>{E(shelf['title'])}</h2><p>{E(shelf['intro'])}</p></div>
  {secs}
</section>'''
    body = f'''<div class="wrap crumbs"><a href="{rel}">Home</a> › Tips</div>
<header class="wrap page-head"><h1>Tips</h1><p>{E(desc)}</p></header>
<main class="wrap">{groups}</main>
'''
    write('tips/index.html', head(f"Miniature painting & hobby tips | {SITE_NAME}", desc, url, rel) + body + foot(rel))


def clean_tips(cfg, tips):
    """Remove built pages for tips that aren't being built this run (e.g. drafts)."""
    keep = {t['slug'] for t in tips}
    for slug in cfg['tips']:
        if slug not in keep:
            for f in ('index.html', 'card.jpg'):
                fp = os.path.join(ROOT, 'tips', slug, f)
                if os.path.exists(fp):
                    os.remove(fp)
    if not tips and os.path.exists(os.path.join(ROOT, 'tips', 'index.html')):
        os.remove(os.path.join(ROOT, 'tips', 'index.html'))


def build_sitemap(posts, games, tips=()):
    today = datetime.date.today().isoformat()
    urls = [(SITE_URL, today), (SITE_URL + 'gear/', today)]
    urls += [(f"{SITE_URL}games/{slugify(g)}/", max((p.get('date') or '2025-01-01') for p in games[g])) for g in games]
    urls += [(f"{SITE_URL}posts/{p['slug']}/", p.get('date') or today) for p in posts]
    if tips:
        urls.append((SITE_URL + 'tips/', max(t['updated'] for t in tips)))
        urls += [(f"{SITE_URL}tips/{t['slug']}/", t['updated']) for t in tips]
    body = ''.join(f'<url><loc>{E(u)}</loc><lastmod>{d}</lastmod></url>' for u, d in urls)
    write('sitemap.xml', f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n')
    write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n')
    return len(urls)


def main():
    import sys
    drafts = '--drafts' in sys.argv
    posts = load()
    gear = json.load(open(os.path.join(ROOT, 'gear.json')))
    link_gear(posts, gear)
    games = {}
    for p in posts:
        games.setdefault(p.get('game') or 'Other', []).append(p)
    cfg, tips = load_tips(drafts)
    TIPS_LIVE[:] = tips
    posts_by_slug = {p['slug']: p for p in posts}
    for t in tips:
        for s in t.get('posts', []):
            if s in posts_by_slug:
                posts_by_slug[s].setdefault('tips', []).append(t)
            else:
                print(f"  WARNING tip {t['slug']}: unknown post {s}")
    for p in posts:
        make_thumb(p)
        build_post(p, posts, games)
    for g, gp in games.items():
        build_game(g, gp)
    build_gear(gear)
    clean_tips(cfg, tips)
    if tips:
        by_slug = {t['slug']: t for t in tips}
        gear_by_id = {it['id']: it for gr in gear['groups'] for it in gr['items']}
        for t in tips:
            make_tip_card(t)
            build_tip(t, by_slug, posts_by_slug, gear_by_id, drafts)
        build_tips_index(cfg, tips)
    build_home(posts, games, gear)
    n = build_sitemap(posts, games, [t for t in tips if t.get('status') == 'live'])
    linked = sum(1 for p in posts if p.get('gear'))
    print(f'{len(posts)} posts, {len(games)} games, {len(tips)} tips{" (drafts included)" if drafts else ""}, {n} sitemap URLs, {linked} posts with gear links')
    for gr in gear['groups']:
        for it in gr['items']:
            print(f"  {it['name']}: {len(it['posts'])} posts")


if __name__ == '__main__':
    main()
