#!/usr/bin/env python3
"""Local preview server for the Strange Leaflet Bear Blog theme.

    python3 dev.py fetch   # snapshot the pages listed in README.md
    python3 dev.py serve   # serve snapshots with the local theme.css, hot-reloaded

Snapshots are stored as raw HTML from the live site. At serve time the blog's
custom styles (the <style data-name="default"> block) are swapped for a link to
the local theme.css, the head directive's theme toggle is swapped for the local
theme-toggle.html, analytics scripts are stripped, and a small dev toolbar is
injected for hot reload and forcing light/dark mode.
"""

import argparse
import html
import json
import re
import sys
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
THEME = ROOT / "theme.css"
TOGGLE = ROOT / "theme-toggle.html"
README = ROOT / "README.md"
SNAPSHOTS = ROOT / "snapshots"

# Bear returns 404 to non-browser user agents
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)


# --- fetch -------------------------------------------------------------------


def readme_urls():
    """URLs listed under the README's "Blog pages to check" heading."""
    urls, in_section = [], False
    for line in README.read_text().splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == "## blog pages to check"
            continue
        match = re.match(r"\s*[-*]\s+(https?://\S+)", line)
        if in_section and match:
            urls.append(match.group(1))
    return urls


def snapshot_path(url):
    path = urlparse(url).path.strip("/")
    return SNAPSHOTS / path / "index.html" if path else SNAPSHOTS / "index.html"


def fetch(_args=None):
    urls = readme_urls()
    if not urls:
        sys.exit('No URLs found under "## Blog pages to check" in README.md')
    for url in urls:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
        except Exception as error:
            print(f"  failed  {url}  ({error})")
            continue
        dest = snapshot_path(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        print(f"  saved   {url}  ->  {dest.relative_to(ROOT)}")


# --- transform ---------------------------------------------------------------

CUSTOM_STYLES = re.compile(r'<style data-name="default">(.*?)</style>', re.S)
# Bear appends its own upvote button CSS after the blog's custom styles
BEAR_UPVOTE_CSS = re.compile(r"\n[ \t]*\.upvote-button \{\s*padding: 0;\s*margin: 0;\s*border: 0;.*", re.S)
SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.S)
ANALYTICS = ("goatcounter", "/hit/")
LIVE_TOGGLE = "data-theme-toggle"  # the live site's copy of theme-toggle.html


def replace_custom_styles(match):
    builtin = BEAR_UPVOTE_CSS.search(match.group(1))
    tags = '<link rel="stylesheet" href="/theme.css" data-dev-theme>'
    if builtin:
        tags += f'\n<style data-name="bear-builtin">{builtin.group(0)}</style>'
    return tags


def transform(page):
    page, count = CUSTOM_STYLES.subn(replace_custom_styles, page, count=1)
    if not count:
        page = page.replace(
            "</head>", '<link rel="stylesheet" href="/theme.css" data-dev-theme>\n</head>', 1
        )
    page = SCRIPT.sub(
        lambda m: "" if any(a in m.group(0) for a in (*ANALYTICS, LIVE_TOGGLE)) else m.group(0), page
    )
    page = page.replace("</head>", TOGGLE.read_text() + "</head>", 1)
    return page.replace("</body>", DEV_CLIENT + "\n</body>", 1)


DEV_CLIENT = """<script data-dev-client>
(() => {
  // Shares theme-toggle.html's storage key and data-theme attribute
  const KEY = "theme";
  const doc = document.documentElement;
  let version = null, toggleVersion = null;
  let link = document.querySelector("link[data-dev-theme]");

  function reload() {
    // Load the new stylesheet before dropping the old one to avoid a flash
    const next = link.cloneNode();
    next.href = `/theme.css?v=${version}`;
    next.onload = () => {
      document.querySelectorAll("link[data-dev-theme]").forEach(l => l !== next && l.remove());
      link = next;
    };
    link.after(next);
  }

  async function poll() {
    try {
      const [v, t] = (await (await fetch("/__dev/version", { cache: "no-store" })).text()).split(" ");
      if (toggleVersion !== null && t !== toggleVersion) return location.reload();
      toggleVersion = t;
      if (v !== version) { const first = version === null; version = v; if (!first) reload(); }
    } catch {}
    setTimeout(poll, 400);
  }

  const host = document.createElement("div");
  const root = host.attachShadow({ mode: "open" });
  root.innerHTML = `<style>
    :host { all: initial; position: fixed; right: 12px; bottom: 12px; z-index: 2147483647; }
    div { display: flex; gap: 2px; padding: 3px; border-radius: 8px; background: #222c; backdrop-filter: blur(4px);
          font: 12px/1 system-ui, sans-serif; box-shadow: 0 2px 8px #0004; }
    button, a { all: unset; cursor: pointer; padding: 6px 9px; border-radius: 6px; color: #ddd; }
    button:hover, a:hover { background: #fff2; }
    button[aria-pressed="true"] { background: #fff; color: #111; }
  </style><div>
    <button data-mode="auto">Auto</button><button data-mode="light">Light</button><button data-mode="dark">Dark</button>
    <a href="/__dev/" target="_top">Pages</a>
  </div>`;
  const paint = () => root.querySelectorAll("button").forEach(b =>
    b.setAttribute("aria-pressed", b.dataset.mode === (doc.dataset.theme || "auto")));
  root.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b) return;
    const theme = b.dataset.mode === "auto" ? null : b.dataset.mode;
    try { theme ? localStorage.setItem(KEY, theme) : localStorage.removeItem(KEY); } catch {}
    // theme-toggle.html applies it, as if another tab had changed it
    dispatchEvent(new StorageEvent("storage", { key: KEY, newValue: theme }));
  });
  // Follow the page's own toggle; theme-toggle.html keeps other tabs and preview iframes in sync
  new MutationObserver(paint).observe(doc, { attributes: true, attributeFilter: ["data-theme"] });
  if (window.self === window.top || new URLSearchParams(location.search).has("toolbar")) document.body.append(host);
  paint();
  poll();
})();
</script>"""


# --- index pages -------------------------------------------------------------

PAGE_STYLE = """<style>
  :root { color-scheme: light dark; --fg: #111; --bg: #f6f6f6; --muted: #666; --line: #ddd; --link: #0055cc; }
  @media (prefers-color-scheme: dark) { :root { --fg: #e7e7e7; --bg: #16181b; --muted: #999; --line: #333; --link: #99ccff; } }
  body { margin: 0; padding: 24px 16px; font: 15px/1.5 system-ui, sans-serif; color: var(--fg); background: var(--bg); }
  a { color: var(--link); }
  h1 { font-size: 18px; margin: 0 0 4px; }
  p { color: var(--muted); margin: 0 0 16px; }
  ul { padding: 0; list-style: none; }
  li { padding: 10px 0; border-top: 1px solid var(--line); display: flex; gap: 12px; flex-wrap: wrap; align-items: baseline; }
  li .title { flex: 1 1 280px; }
  code { font-size: 13px; color: var(--muted); }
  .frames { display: flex; gap: 16px; align-items: flex-start; overflow-x: auto; }
  .frames figure { margin: 0; }
  .frames figcaption { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
  iframe { border: 1px solid var(--line); border-radius: 6px; height: calc(100vh - 110px); background: white; }
</style>"""


def snapshot_pages():
    pages = []
    for file in sorted(SNAPSHOTS.rglob("index.html")):
        rel = file.parent.relative_to(SNAPSHOTS).as_posix()
        path = "/" if rel == "." else f"/{rel}/"
        match = re.search(r"<title>(.*?)</title>", file.read_text(errors="replace"), re.S)
        pages.append((path, html.unescape(match.group(1).strip()) if match else path))
    return pages


def index_page():
    items = "\n".join(
        f'<li><a class="title" href="{p}">{html.escape(t)}</a> <code>{p}</code> '
        f'<a href="/__dev/frames?path={p}">phone + desktop</a></li>'
        for p, t in snapshot_pages()
    )
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Theme Preview</title>{PAGE_STYLE}</head><body>
<h1>Strange Leaflet theme preview</h1>
<p>Snapshots of the pages in README.md, styled with the local <code>theme.css</code>.
Saving <code>theme.css</code> hot-reloads every open page. Run <code>python3 dev.py fetch</code> to refresh snapshots.</p>
<ul>{items}</ul></body></html>"""


def frames_page(path):
    src = html.escape(path)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Theme Preview</title>{PAGE_STYLE}</head><body>
<h1><a href="/__dev/">Pages</a> / <code>{src}</code></h1>
<div class="frames">
  <figure><figcaption>390px</figcaption><iframe src="{src}" style="width:390px"></iframe></figure>
  <figure><figcaption>1024px</figcaption><iframe src="{src}?toolbar" style="width:1024px"></iframe></figure>
</div></body></html>"""


# --- serve -------------------------------------------------------------------


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SNAPSHOTS), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def respond(self, body, content_type="text/html; charset=utf-8", status=200):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/theme.css":
            return self.respond(THEME.read_text(), "text/css; charset=utf-8")
        if url.path == "/__dev/version":
            return self.respond(
                f"{THEME.stat().st_mtime_ns} {TOGGLE.stat().st_mtime_ns}", "text/plain"
            )
        if url.path in ("/__dev", "/__dev/"):
            return self.respond(index_page())
        if url.path == "/__dev/frames":
            return self.respond(frames_page(parse_qs(url.query).get("path", ["/"])[0]))
        if url.path.startswith("/upvote-info/"):
            return self.respond(
                json.dumps({"upvote_count": 0, "upvoted": False, "token": ""}),
                "application/json",
            )

        file = Path(self.translate_path(url.path))
        if file.is_dir() and (file / "index.html").exists():
            if not url.path.endswith("/"):
                self.send_response(301)
                self.send_header("Location", url.path + "/")
                return self.end_headers()
            return self.respond(transform((file / "index.html").read_text()))
        if file.is_file():
            return super().do_GET()
        return self.respond(
            f"<p>No snapshot for <code>{html.escape(url.path)}</code>. "
            'Add it to README.md under "Blog pages to check" and run '
            "<code>python3 dev.py fetch</code>.</p><p><a href='/__dev/'>Snapshot list</a></p>",
            status=404,
        )

    def do_POST(self):
        # The upvote form posts here; swallow it
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        if not self.path.startswith("/__dev/version"):
            super().log_message(format, *args)


def serve(args):
    if not any(SNAPSHOTS.rglob("index.html")):
        print("No snapshots yet, fetching...")
        fetch()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"\nServing theme preview at http://{args.host}:{args.port}/__dev/")
    print(f"Watching {THEME.name} and {TOGGLE.name} for changes. Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fetch", help="snapshot the pages listed in README.md").set_defaults(func=fetch)
    serve_parser = commands.add_parser("serve", help="serve snapshots with the local theme.css")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.set_defaults(func=serve)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
