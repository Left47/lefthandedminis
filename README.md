# Left-Handed Minis

Final photos and captions for [@lefthandedminis](https://instagram.com/lefthandedminis) posts, plus the web gallery served by GitHub Pages.

## Layout

```
index.html              gallery (static, no build step)
posts/index.json        list of post folders, newest added to the end
posts/<date>-<slug>/
  01-*.jpg …            4:5 photos at 1080×1350, carousel order
  instagram.md          Instagram caption as posted
  threads.md            Threads caption as posted
  post.json             title, date, game, result, alt text, Buffer post IDs
```

Images here are public on purpose: Buffer pulls them from the raw GitHub URLs when it publishes.
