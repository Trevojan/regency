#!/usr/bin/env python3
"""Deterministic Tailwind audit. Greps every file for every rule; prints counts, then lines.

Usage: python audit.py <path> [--ignore R02,R12] [--max 15] [--json]
Rule ids match references/norm.md. Findings are candidates: a human or agent confirms them.
"""
import argparse, json, re, sys
from pathlib import Path

EXTS = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".css", ".js", ".ts", ".mdx"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", ".nuxt", ".svelte-kit", "coverage", ".turbo"}

PALETTE = "slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose"
UTIL = "bg|text|border|ring|fill|stroke|from|to|via|divide|outline|accent|decoration|caret|placeholder|shadow"
ALLOWED_Z = {"10", "30", "40", "50", "60"}
ALLOWED_SPACE = {"0", "0.5", "1", "1.5", "2", "3", "4", "5", "6", "8", "12", "px", "auto", "full"}

# id, severity, title, regex, applies-to (None = all), per-line predicate (optional)
RULES = [
    ("R01", "high", "Raw palette colour instead of semantic token",
     re.compile(rf"(?<![\w-])(?:[a-z-]+:)*(?:{UTIL})-(?:(?:{PALETTE})-\d{{2,3}}|white|black)(?:/\d+)?(?![\w-])"), None, None),
    ("R02", "high", "Arbitrary value [..] (no arbitrary values allowed)",
     re.compile(r"(?<![\w-])(?:[a-z-]+:)*-?[a-z][a-z0-9-]*-\[[^\]\s]+\]"), None,
     lambda l, m, c: not re.search(r"(?:content|bg-\[url|\[&|\[--|\[data-|\[aria-)", m.group(0))),
    ("R03", "med", "font-bold/extrabold/black in UI (use semibold)",
     re.compile(r"(?<![\w-])(?:[a-z-]+:)*font-(?:bold|extrabold|black)(?![\w-])"), None, None),
    ("R04", "high", "outline-none without focus-visible substitute",
     re.compile(r"(?<![\w-])(?:[a-z-]+:)*outline-(?:none|0)(?![\w-])"), None,
     lambda l, m, c: "focus-visible:" not in l and "focus:ring" not in l),
    ("R05", "high", "Play CDN v3 (cdn.tailwindcss.com) - use @tailwindcss/browser@4",
     re.compile(r"cdn\.tailwindcss\.com"), None, None),
    ("R06", "med", "z-index off the scale (10/30/40/50/60)",
     re.compile(r"(?<![\w-])(?:[a-z-]+:)*-?z-(\d+)(?![\w-])"), None,
     lambda l, m, c: m.group(1) not in ALLOWED_Z),
    ("R07", "high", "Clickable div/span (use button or a)",
     re.compile(r"<(?:div|span|li|td|p)\b[^>]*\b(?:onClick|onclick|@click|v-on:click)\b"), None, None),
    ("R08", "med", "img without alt",
     re.compile(r"<img\b(?![^>]*\balt\s*=)[^>]*>"), None, None),
    ("R09", "med", "transition-all or duration over 300ms",
     re.compile(r"(?<![\w-])(?:[a-z-]+:)*(?:transition-all|duration-(\d+))(?![\w-])"), None,
     lambda l, m, c: m.group(0).endswith("transition-all") or int(m.group(1)) > 300),
    ("R10", "med", "Spacing step off the 4px scale table",
     re.compile(r"(?<![\w-])(?:[a-z-]+:)*-?(p|px|py|pt|pb|pl|pr|ps|pe|m|mx|my|mt|mb|ml|mr|ms|me|gap|gap-x|gap-y|space-x|space-y)-([\d.]+|px)(?![\w.\[-])"), None,
     # 9 on one inline side = room reserved for an icon inside a control (layout A02), not rhythm spacing
     lambda l, m, c: m.group(2) not in ALLOWED_SPACE and not (m.group(2) == "9" and m.group(1) in {"pl", "pr", "ps", "pe"})),
    ("R11", "med", "Hover changes size/border width/layout (hover only recolours)",
     re.compile(r"(?<![\w-])hover:(?:scale|w|h|p|px|py|m|mx|my|gap|border-\d|border-[xytblr]-?\d*|translate|-translate)(?:-[\w./]+)?(?![\w-])"), None, None),
    ("R12", "low", "Card-like shadow at rest (shadow only on elevation or hover)",
     re.compile(r"(?<![\w-])(?<!hover:)(?<!focus:)(?<!group-hover:)shadow-(?:sm|md|lg|xl|2xl)(?![\w-])"), None,
     # overlays are elevation by definition; the overlay class often sits on the wrapper a line or two above
     lambda l, m, c: not re.search(r"(?<![\w-])(?:absolute|fixed|z-40|z-50|z-60)(?![\w-])|\bpopover\b|<dialog|role=\"dialog\"", c)),
    ("R13", "med", "Hard-coded colour literal outside @theme/tokens",
     re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(\s*\d|\bhsla?\(\s*\d"), {".css", ".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro"},
     # skip custom-property definitions (tokens; dark overrides live outside @theme) and text such as "Pedido #1042":
     # a colour value follows ':' ',' '(' '[' '=' or a quote
     lambda l, m, c: not re.search(r"--[\w-]+\s*:\s*$", l[: m.start()])
                     and (not m.group(0).startswith("#") or re.search(r"[:,(\[=\"']\s*$", l[: m.start()]))),
    ("R14", "med", "<html> without lang",
     re.compile(r"<html\b(?![^>]*\blang\s*=)[^>]*>"), None, None),
    ("R15", "med", "<style> with @theme but no type=text/tailwindcss (browser build ignores it)",
     re.compile(r"<style\b(?![^>]*text/tailwindcss)[^>]*>\s*(?:[^<]*?)@theme"), None, None),
    ("R16", "med", "truncate inside a flex-1/grow wrapper that lacks min-w-0 (layout F02 trap)",
     re.compile(r"(?<![\w-])truncate(?![\w-])"), None,
     # The trap is the plain wrapper: <div class="flex-1"> holding <p class="truncate">. An item that has
     # `truncate` itself is safe (overflow-hidden zeroes its minimum), so only the line above is examined.
     # Static scans miss structure; `shoot.mjs --probe` (truncateNotClipping) is the reliable check.
     lambda l, m, c: (lambda prev: bool(re.search(r"(?<![\w-])(?:flex-1|grow|flex-auto)(?![\w-])", prev))
                      and "min-w-0" not in prev and not re.search(r"(?<![\w-])truncate(?![\w-])", prev))
                     (c.splitlines()[-2] if len(c.splitlines()) > 1 else "")),
    ("R17", "low", "Interactive element with class but no focus-visible style (check for a global rule)",
     re.compile(r"<(?:button|a)\b[^>]*\bclass(?:Name)?=[\"'{`][^\"'`]*[\"'`]"), None,
     lambda l, m, c: "focus-visible" not in m.group(0) and "focus:" not in m.group(0)),
    ("R18", "low", "Centred long text (text-center on prose)",
     re.compile(r"<p\b[^>]*\btext-center\b"), None, None),
    ("R19", "med", "Wrong palette word for state: raw red/green in markup for status (use danger/success)",
     re.compile(r"(?<![\w-])(?:[a-z-]+:)*(?:bg|text|border)-(?:red|green|yellow|amber|orange)-\d{2,3}(?![\w-])"), None, None),
]
# R19 overlaps R01 on purpose: it names the semantic fix. Ignore one of them if the noise is too much.


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in EXTS and not (set(p.parts) & SKIP_DIRS):
            yield p


def strip_comments(text: str) -> str:
    """Blank out <!-- --> and /* */ comments (keeping line numbers): class names in prose are not usage."""
    return re.sub(r"<!--.*?-->|/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)


def strip_theme_blocks(text: str) -> str:
    """Blank out @theme { ... } so token definitions do not trip R13."""
    out, i = [], 0
    for m in re.finditer(r"@theme\b[^{]*\{", text):
        if m.start() < i:
            continue
        depth, j = 1, m.end()
        while j < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            j += 1
        out.append(text[i:m.start()])
        out.append(re.sub(r"[^\n]", " ", text[m.start():j]))
        i = j
    out.append(text[i:])
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--ignore", default="")
    ap.add_argument("--max", type=int, default=15, help="detail lines per rule (0 = all)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    ignore = {x.strip() for x in a.ignore.split(",") if x.strip()}
    root = Path(a.path)
    if not root.exists():
        sys.exit(f"not found: {root}")

    findings = {r[0]: [] for r in RULES}
    files = classes = 0
    for f in iter_files(root):
        try:
            raw = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files += 1
        classes += len(re.findall(r"\bclass(?:Name)?\s*=", raw))
        text = strip_theme_blocks(strip_comments(raw))
        multi = {"R15"}
        for rid, sev, title, rx, exts, pred in RULES:
            if rid in ignore or (exts and f.suffix.lower() not in exts):
                continue
            if rid in multi:
                for m in rx.finditer(raw):
                    ln = raw.count("\n", 0, m.start()) + 1
                    findings[rid].append((str(f), ln, m.group(0).strip()[:100]))
                continue
            lines = text.splitlines()
            for ln, line in enumerate(lines, 1):
                for m in rx.finditer(line):
                    ctx = "\n".join(lines[max(0, ln - 4): ln])
                    if pred is None or pred(line, m, ctx):
                        findings[rid].append((str(f), ln, m.group(0).strip()[:100]))

    if a.json:
        print(json.dumps({"files": files, "class_attrs": classes,
                          "findings": {k: [{"file": x, "line": y, "text": z} for x, y, z in v] for k, v in findings.items()}},
                         indent=2, ensure_ascii=False))
        return

    print(f"Scanned {files} files, {classes} class attributes. Method: regex per line; candidates, not verdicts.\n")
    print(f"{'rule':5} {'sev':5} {'count':>5} {'files':>5}  title")
    for rid, sev, title, *_ in RULES:
        if rid in ignore:
            continue
        v = findings[rid]
        print(f"{rid:5} {sev:5} {len(v):>5} {len({x[0] for x in v}):>5}  {title}")
    print()
    for rid, sev, title, *_ in RULES:
        v = findings[rid]
        if rid in ignore or not v:
            continue
        print(f"== {rid} [{sev}] {title}  ({len(v)})")
        for x in (v if a.max == 0 else v[: a.max]):
            print(f"  {x[0]}:{x[1]}  {x[2]}")
        if a.max and len(v) > a.max:
            print(f"  ... {len(v) - a.max} more (use --max 0)")
        print()
    print("Not covered by this script: rendering, contrast, 360px overflow, dark mode, keyboard order,")
    print("label/for pairing, icon-only aria-label, loading/empty/error states, copy rules. See SKILL.md step 5.")


if __name__ == "__main__":
    main()
