# Left-Handed Minis

Source for the Left-Handed Minis site: every post's photos and captions, plus a small build script that turns them into a static, crawlable site on GitHub Pages.

**Live site:** https://www.lefthandedminis.com/

## Adding or editing a post

1. Add `posts/<date>-<slug>/` with photos (`01.jpg`…), `instagram.md` / `threads.md` / `tiktok.md`, and `post.json`.
2. Append the slug to `posts/index.json`.
3. Run `python3 build.py` and commit everything it generates.

## What the build generates

- `index.html`: home page with the full gallery, About, and a gear preview
- `posts/<slug>/index.html`: one page per post, with its own title, description, social preview, and structured data
- `posts/<slug>/thumb.jpg`: 600×750 grid thumbnail
- `games/<slug>/index.html`: one page per game
- `gear/index.html`: every affiliate item, with links to the posts it shows up in
- `sitemap.xml`, `robots.txt`

Gear-to-post links come from the `match` pattern on each item in `gear.json`, checked against post titles and captions. Moving to a custom domain means changing `SITE_URL` in `build.py` and rebuilding.

Photos here are public on purpose: Buffer pulls them from raw GitHub URLs when it publishes.

## Holy Hand Grenadiers match reports

A separate Blood Bowl section at `/grenadiers/`, kept out of the Instagram gallery so match reports can be shared on the league Discord.

1. Add the match to `grenadiers/season<N>.json` (Cabalvision transcript, SPP, timeline, injuries, standouts). Public-facing only: no coach's notes, prep or scouting.
2. Put photos in `grenadiers/s<N>/md<M>/` and list them in the JSON. With no photos, the page falls back to the team shot.
3. Run `python3 build_grenadiers.py` and commit what it generates.

Share links look like `https://www.lefthandedminis.com/grenadiers/s9/md5/`.
