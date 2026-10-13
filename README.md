# strangeleaflet-theme

A bearblog.dev theme for strangeleaflet.com

## Local development

```sh
python3 dev.py serve   # http://127.0.0.1:8000/__dev/
```

This serves snapshots of the pages listed below, with Bear's custom styles swapped
for the local `theme.css` and the local `theme-toggle.html` injected. Saving `theme.css`
hot-reloads every open page, no refresh needed; saving `theme-toggle.html` reloads them.

- The toolbar in the corner forces **Light** / **Dark** mode, or follows the OS with **Auto**.
  It sets the same choice a visitor's moon/sun toggle does.
- `/__dev/` lists the snapshots; "phone + desktop" shows a page at 390px and 1024px side by side.
- `python3 dev.py fetch` re-downloads the snapshots (the first `serve` does this automatically).
  Add a URL under "Blog pages to check" to include another page.

Requires only Python 3, no dependencies. Snapshots are kept in `snapshots/` (gitignored).
When it looks right, paste `theme.css` into the Bear dashboard.

## Light/dark toggle

The theme follows the visitor's OS setting. `theme-toggle.html` adds a moon/sun button to the
nav that lets visitors pick the other scheme, remembered in `localStorage`; picking the OS's
own scheme again goes back to following the OS. Paste it into Bear's
head directive in the dashboard settings (paid plans). Without it the
theme still works, just without the button.


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
