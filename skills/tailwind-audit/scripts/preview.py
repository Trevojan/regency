#!/usr/bin/env python3
"""Render body fragments inside references/render-shell.html.

The shell is kept as the user wrote it; this script only adds, in <head>, the Tailwind v4 browser build,
references/theme.css and a small harness (pattern labels, `demo` outlines, ?theme=dark), then pastes the
fragment into <body>.

  python preview.py                      # all samples -> <tmp>/tailwind-audit-preview, prints index path
  python preview.py --out DIR --serve 8765
  python preview.py --wrap card.html     # any fragment (e.g. a project component) -> DIR/card.html

Open a page with ?theme=dark to render the dark tokens.
"""
import argparse, functools, http.server, re, socketserver, tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
REFS = SKILL / "references"
TAILWIND = '<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>'

# Harness only: makes structure visible and labels blocks. Not design, never copied into a product.
HARNESS = """
.demo { outline: 1px dashed color-mix(in oklab, currentColor 45%, transparent); outline-offset: -1px; }
.demo-fill { background: color-mix(in oklab, Canvas 88%, CanvasText); }  /* opaque, so stacking order shows */
[data-pattern] { display: block; }
[data-case="broken"] { overflow-x: clip; }  /* a broken demo spills inside its own block, not the page */
[data-force-open] [role="tooltip"] { visibility: visible !important; opacity: 1 !important; }  /* show hover-only UI */
/* room for overlays that leave their box, so samples carry no off-scale spacer classes */
[data-room~="below"] { padding-bottom: 12rem; }
[data-room~="above"] > * { padding-top: 8rem; }
[data-room~="start"] > * { margin-inline-start: 6rem; }
[data-pattern]::before { content: attr(data-pattern) " \\00B7 " attr(data-case); display: block; margin-bottom: 0.5rem;
  font: 600 12px/16px ui-monospace, monospace; opacity: 0.6; }
"""
THEME_SWITCH = "<script>if(new URLSearchParams(location.search).get('theme')==='dark')document.documentElement.dataset.theme='dark'</script>"


def render(fragment: str, title: str, tokens: bool) -> str:
    shell = (REFS / "render-shell.html").read_text(encoding="utf-8")
    lang = re.search(r"<!--\s*lang:\s*([\w-]+)\s*-->", fragment)
    if lang:
        shell = re.sub(r'(<html\b[^>]*\blang=")[^"]*"', rf'\g<1>{lang.group(1)}"', shell, count=1)
    shell = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", shell, count=1, flags=re.S)
    css = "\n".join((REFS / f).read_text(encoding="utf-8") for f in ("theme.css", "layout/utilities.css")) + HARNESS
    head = f'    {TAILWIND}\n    <style type="text/tailwindcss">\n{css}\n    </style>\n    {THEME_SWITCH}\n'
    shell = shell.replace("</head>", head + "</head>", 1)
    if tokens:  # page canvas for component samples, same as the norm's <body>
        shell = re.sub(r"<body\b[^>]*>", '<body class="bg-surface-muted text-ink antialiased font-sans">', shell, count=1)
    return re.sub(r"(<body\b[^>]*>)\s*(</body>)", lambda m: f"{m.group(1)}\n{fragment}\n{m.group(2)}", shell, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(tempfile.gettempdir()) / "tailwind-audit-preview"))
    ap.add_argument("--wrap", nargs="*", help="fragment files to render instead of the bundled samples")
    ap.add_argument("--serve", type=int, help="serve --out on this port after rendering")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if a.wrap:
        sources = [(Path(p), Path(p).stem) for p in a.wrap]
    else:
        sources = [(p, p.parent.name) for p in sorted((REFS / "layout").glob("*/samples.html"))]
        sources += [(p, "components-" + p.stem) for p in sorted((REFS / "components").glob("*.html"))]

    links = []
    for src, name in sources:
        page = render(src.read_text(encoding="utf-8"), name, tokens=True)
        (out / f"{name}.html").write_text(page, encoding="utf-8")
        links.append(name)
        print(out / f"{name}.html")

    items = "\n".join(
        f'<li><a href="{n}.html">{n}</a> · <a href="{n}.html?theme=dark">dark</a></li>' for n in links)
    (out / "index.html").write_text(render(f'<main class="mx-auto max-w-3xl p-6"><ul class="space-y-2">\n{items}\n</ul></main>',
                                           "preview", tokens=True), encoding="utf-8")
    print(out / "index.html")

    if a.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
        with socketserver.TCPServer(("127.0.0.1", a.serve), handler) as httpd:
            print(f"serving http://127.0.0.1:{a.serve}/")
            httpd.serve_forever()


if __name__ == "__main__":
    main()
