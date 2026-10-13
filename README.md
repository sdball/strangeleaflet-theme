# strangeleaflet-theme

A bearblog.dev theme for strangeleaflet.com

## Local development

```sh
python3 dev.py serve   # http://127.0.0.1:8000/__dev/
```

This serves snapshots of the pages listed below, with Bear's custom styles swapped
for the local `theme.css`. Saving `theme.css` hot-reloads every open page, no refresh needed.

- The toolbar in the corner forces **Light** / **Dark** mode, or follows the OS with **Auto**.
- `/__dev/` lists the snapshots; "phone + desktop" shows a page at 390px and 1024px side by side.
- `python3 dev.py fetch` re-downloads the snapshots (the first `serve` does this automatically).
  Add a URL under "Blog pages to check" to include another page.

Requires only Python 3, no dependencies. Snapshots are kept in `snapshots/` (gitignored).
When it looks right, paste `theme.css` into the Bear dashboard.


## Blog pages to check

- https://strangeleaflet.com/
- https://strangeleaflet.com/blog/
- https://strangeleaflet.com/strange-leaflet-about-elixir-page-3/
- https://strangeleaflet.com/lets-query-the-github-graphql-api-from-a-livebook-smart-cell/
- https://strangeleaflet.com/from-awk-to-a-dockerized-ruby-script/

## References

- https://docs.bearblog.dev/styling/
- https://robertbirming.com/bearming/
- https://robertbirming.com/bear-blog-library/ 
- https://robertbirming.com/bear-blog-timeline-styles/
