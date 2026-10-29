# AGENTS.md: lefthandedminis.com (public repo)

This repo is public. It holds the posts, gallery, gear page, Tips guides, and the Grenadiers match-report section, served on GitHub Pages at https://www.lefthandedminis.com/.

Voice, caption, and workflow guidance lives in the private repo `Left47/lefthandedminis-private` (its AGENTS.md). Never copy any of that content into this repo.

## Build

- `python3 build.py`: builds the gallery, post pages, gear page, game pages, Tips (live guides only), and `sitemap.xml`.
- `python3 build.py --drafts`: renders draft guides locally for review. **Never commit this output.**
- `python3 build_grenadiers.py`: builds `/grenadiers/` (match pages, season page, share cards). It's separate; `build.py` doesn't touch it.
- `SITE_URL` in both scripts is `https://www.lefthandedminis.com/`. Keep the `CNAME` file at the repo root.
- `.gitattributes` keeps text files LF. Don't introduce CRLF.

## Adding a post

1. Add `posts/<date>-<slug>/` with photos (`01.jpg`…), the caption files and `post.json`.
2. Append the slug to `posts/index.json`.
3. Run `python3 build.py` and commit everything it generates.

## Layout

- `posts/<date>-<slug>/`: `instagram.md`, `threads.md`, `tiktok.md`, `post.json`, numbered 1080×1350 JPEGs; `reel.mp4`, `reel.md`, `tiktok-reel.md` when there's a reel.
- `gear.json`: gear and affiliate items. For a product with links at two stores, keep one item with a primary `url` plus `also`, and a `store` field for non-Amazon links.
- `tips/tips.json`, `tips/<slug>/article.md`, `tips/img/`: guides. Only `"status": "live"` guides build. Images use `post:<slug>/<file>` and `img:<file>`.
- `grenadiers/season<N>.json`, `grenadiers/s<N>/md<M>/`: match data and photos. `cover` picks the lead photo.

## post.json rules

- Gallery order and dates come from the Instagram go-live time (`dueAt`), falling back to the earliest channel, then `date`.
- Carousel Buffer IDs: `buffer`. Reel IDs: `reel.buffer`. Reshares: `reshares`. Only `buffer` drives gallery order, so the others must never go there (it would create duplicate cards).
- `"hold": true` keeps a post off the site entirely (page, card, game page, sitemap) until its Instagram go-live time. The hourly "Rebuild gallery" Action reruns `build.py` and commits only when a held post goes live.
- `status` and `note` fields are for tracking only; the build must never render them.

## Site rules

- Post pages show only the Instagram caption. Threads, TikTok, and reel captions stay in the folder but aren't rendered.
- Reel videos aren't shown yet; post pages show the carousel photos.
- Nothing internal on the public site: no "not posted yet" badges, placeholders, or bookkeeping notes.
- Brand: royal blue `#004AAD`, logo red `#BA1B2B`, yellow pop-art accent, Anton headlines, Lato body, comic-panel borders. Cards in a row stay the same height.
- Grenadiers pages use their own colors (slate blue, red, gold) and never appear in the gallery grid.
- No em dashes in site copy.

## Safety

- No secrets in this repo.
- No photos with other people's faces; crop or blur anyone who isn't Jim.
- Code changes go on a branch with a PR. Pull before committing content to `main`.
