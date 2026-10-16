#!/usr/bin/env python3
"""ux.py - scaffold a project's frontend documentation (.ux/) and keep it honest.

The engine behind /regency:ux-init (skills/ux-init/SKILL.md). The template is library/templates/ux/;
in a project it lives at <guidelines>/.ux/. The token file has the Design System artifact shape
(tokens.json): `color.themes`, `color.tokens` as a LIST of {name, value, usage}, `type`, and every other
family as {"tokens": [...]}.

  python scripts/ux.py plan     <guidelines-root>                list every path the scaffold would create
  python scripts/ux.py scaffold <guidelines-root> --yes          copy the template into <root>/.ux/; never
                                                                 overwrites: an existing file gets <name>.template beside it
  python scripts/ux.py expand   <ux-dir>                         one folder per view and component the brief names;
                                                                 refreshes the index tables between ux: markers

  python scripts/ux.py check  [tokens.json]          one line per finding; exit 1 on any FAIL
  python scripts/ux.py build  [tokens.json] [--out theme.css]   write the stylesheet
  python scripts/ux.py synced [tokens.json] [--css theme.css]   FAIL when theme.css drifted (F4)
  python scripts/ux.py brief  <brief.md>                    holes left (ask), view codes, keys, mappings
  python scripts/ux.py --selftest                     every check fires on a planted defect

Token checks (.ux/.foundations/color.md, CODE-CONVENTIONS N3, U1)
  shape     families, list shape, name grammar, one name used once
  value     colour values parse: #rgb #rrggbb #rrggbbaa, rgb(), or an alias {token} that exists
  roles     every colour role of the template exists (a project may add, never drop)
  naming    no colour named by value (cyan, red-600, gray, slate ...): name by role (N3)
  contrast  WCAG ratios per theme, computed: text 4.5:1 on its grounds and its -soft fill,
            control borders 3:1, label on the accent fill and the agent chip 4.5:1
  ground    the first theme is the brand theme; its ground is pure black (U1)            WARN
  grey      a neutral with HSL saturation under 0.12 reads grey (U1: nothing greyish)    WARN

Brief checks (.ux/BRIEF.md)
  holes     every ⟨…⟩ left is one ask line, with its section: asks never block (README §2)
  views     codes are three uppercase letters, unique; archetypes from views.md
  keys      a shortcut is used once across views and commands; a command lands in a known view
  mapping   the severity table covers fix, ask, note, ok; the lifecycle table its five states
  catalogue every component the brief names has a contract in .components/README.md

Pure standard library, Python 3.8+. `check` and `synced` read only.
"""
import colorsys
import datetime
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UX_TEMPLATE = ROOT / "library" / "templates" / "ux"
TEMPLATE = UX_TEMPLATE / ".tokens" / "tokens.json"
THEME_CSS = UX_TEMPLATE / ".tokens" / "theme.css"

NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
HEX = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
RGB = re.compile(r"^rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)(?:[\s,/]+[\d.]+%?)?\s*\)$")
ALIAS = re.compile(r"^\{([A-Za-z0-9][A-Za-z0-9_.-]*)\}$")
VALUE_WORDS = {"red", "orange", "amber", "yellow", "lime", "green", "emerald", "teal", "cyan", "sky", "blue", "indigo",
               "violet", "purple", "fuchsia", "pink", "rose", "slate", "gray", "grey", "zinc", "neutral", "stone",
               "black", "white", "brown", "magenta", "navy", "gold", "silver"}
SCALE_STEP = re.compile(r"-(50|[1-9]00|950)$")

GROUNDS = ("ground", "surface", "surface-raised")
TEXTS = ("ink", "ink-muted", "ink-faint")
HUES = ("accent", "human", "ok", "system", "fix", "ask")
NEUTRALS = ("surface", "surface-raised", "line", "line-strong") + TEXTS
ROLES = GROUNDS + ("line", "line-strong") + TEXTS + ("on-accent", "link", "scrim") + HUES + tuple(h + "-soft" for h in HUES)


def contrast_pairs():
    """(foreground, background, minimum, why) - the pairs every theme must pass."""
    out = []
    for fg in TEXTS:
        for bg in GROUNDS:
            out.append((fg, bg, 4.5, "text"))
    for h in HUES:
        out.append(("ink", h + "-soft", 4.5, "text on a soft fill"))
        out.append((h, h + "-soft", 4.5, "hue on its soft fill"))
        for bg in GROUNDS:
            out.append((h, bg, 4.5, "hue as text"))
    for bg in GROUNDS:
        out.append(("line-strong", bg, 3.0, "control border"))
    out.append(("on-accent", "accent", 4.5, "label on the primary fill"))
    out.append(("ink", "line-strong", 4.5, "agent chip"))
    return out


# ---------- colour maths -------------------------------------------------------------------------

def parse_rgb(value):
    """(r, g, b, alpha) in 0..1 floats, or None when the value is not a plain colour."""
    v = value.strip()
    m = HEX.match(v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a
    m = RGB.match(v)
    if m:
        return tuple(int(x) / 255 for x in m.groups()) + (1.0,)
    return None


def luminance(rgb):
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def saturation(rgb):
    return colorsys.rgb_to_hls(*rgb[:3])[2]


# ---------- model --------------------------------------------------------------------------------

class Tokens:
    def __init__(self, data):
        self.data = data
        color = data.get("color") or {}
        self.themes = [t.get("id") for t in color.get("themes", []) if isinstance(t, dict)]
        self.colors = {t["name"]: t for t in color.get("tokens", []) if isinstance(t, dict) and "name" in t}

    def raw(self, name, theme, depth=0):
        """The literal value of a colour token in a theme, aliases followed; None when absent."""
        tok = self.colors.get(name)
        if tok is None or depth > 8:
            return None
        v = tok.get("value")
        if isinstance(v, dict):
            v = v.get(theme, v.get(self.themes[0]) if self.themes else None)
        if not isinstance(v, str):
            return None
        m = ALIAS.match(v.strip())
        return self.raw(m.group(1), theme, depth + 1) if m else v

    def rgb(self, name, theme):
        v = self.raw(name, theme)
        return parse_rgb(v) if v else None

    def families(self):
        for fam, body in self.data.items():
            if fam in ("name", "version", "meta", "type", "color") or not isinstance(body, dict):
                continue
            yield fam, body


def check(data):
    out = []

    def rec(level, kind, msg):
        out.append((level, kind, msg))

    t = Tokens(data)
    # shape
    if not t.themes:
        rec("FAIL", "shape", "color.themes is empty: at least one theme")
    if not isinstance((data.get("color") or {}).get("tokens"), list):
        rec("FAIL", "shape", "color.tokens must be a LIST of {name, value, usage}")
    seen = {}
    lists = [("color", (data.get("color") or {}).get("tokens") or [])]
    for fam, body in t.families():
        if not isinstance(body.get("tokens"), list):
            rec("FAIL", "shape", f"{fam}: must be {{\"tokens\": [...]}}, a list")
            continue
        lists.append((fam, body["tokens"]))
    for fam, items in lists:
        for tok in items:
            name = tok.get("name", "") if isinstance(tok, dict) else ""
            if not NAME.match(name):
                rec("FAIL", "shape", f"{fam}: bad token name {name!r}")
                continue
            if name in seen:
                rec("FAIL", "shape", f"{name}: used in {seen[name]} and {fam}; a name is used once")
            seen[name] = fam
            if not tok.get("usage"):
                rec("WARN", "shape", f"{name}: no usage note")
    # value
    for name, tok in t.colors.items():
        values = tok.get("value")
        values = values.values() if isinstance(values, dict) else [values]
        for v in values:
            if not isinstance(v, str):
                rec("FAIL", "value", f"{name}: value {v!r} is not a string")
                continue
            m = ALIAS.match(v.strip())
            if m:
                if m.group(1) not in t.colors or m.group(1) == name:
                    rec("FAIL", "value", f"{name}: alias {v} names no other colour token")
            elif parse_rgb(v) is None:
                rec("FAIL", "value", f"{name}: {v!r} is not #hex, rgb() or an alias (named colours, var() and color-mix() drop)")
    # roles
    missing = [r for r in ROLES if r not in t.colors]
    if missing:
        rec("FAIL", "roles", f"missing colour roles: {', '.join(missing)}")
    else:
        rec("OK", "roles", f"all {len(ROLES)} colour roles present")
    # naming
    for name in seen:
        parts = set(re.split(r"[-_.]", name.lower()))
        if parts & VALUE_WORDS or (seen[name] == "color" and SCALE_STEP.search(name)):
            rec("FAIL", "naming", f"{name}: named by value; name it by role (N3)")
    # contrast
    measured = failed = 0
    for theme in t.themes:
        for fg, bg, need, why in contrast_pairs():
            a, b = t.rgb(fg, theme), t.rgb(bg, theme)
            if not a or not b:
                continue
            measured += 1
            r = ratio(a, b)
            if r + 1e-9 < need:
                failed += 1
                rec("FAIL", "contrast", f"{theme}: {fg} on {bg} = {r:.2f}:1, needs {need}:1 ({why})")
    if measured and not failed:
        rec("OK", "contrast", f"{measured} pairs across {len(t.themes)} theme(s) pass (computed, WCAG 2)")
    # ground and grey (U1)
    if t.themes:
        brand = t.themes[0]
        g = t.rgb("ground", brand)
        if g and g[:3] != (0.0, 0.0, 0.0):
            rec("WARN", "ground", f"{brand}: ground is {t.raw('ground', brand)}, not pure black (U1); the first theme is the brand theme")
        for n in NEUTRALS:
            c = t.rgb(n, brand)
            if c and saturation(c) < 0.12:
                rec("WARN", "grey", f"{brand}: {n} {t.raw(n, brand)} reads grey (saturation {saturation(c):.2f}); tint it (U1)")
    return out


# ---------- build ----------------------------------------------------------------------------------

def css_value(t, name, theme):
    tok = t.colors[name]
    v = tok.get("value")
    if isinstance(v, dict):
        v = v.get(theme)
        if v is None:
            return None
    m = ALIAS.match(v.strip())
    return f"var(--{m.group(1)})" if m else v


def build(data, source="tokens.json"):
    t = Tokens(data)
    brand = t.themes[0] if t.themes else "default"
    lines = [f"/* GENERATED by scripts/ux.py from {source}. Never edit by hand (F4): edit the",
             "   tokens file, then run: python scripts/ux.py build. Plain CSS reads the custom",
             "   properties; Tailwind v4 reads the @theme blocks (browsers ignore them). */", "",
             f':root, [data-theme="{brand}"] {{']
    for name in t.colors:
        v = css_value(t, name, brand)
        if v is not None:
            lines.append(f"  --{name}: {v};")
    fams = (data.get("type") or {}).get("families", {})
    for fam, stack in fams.items():
        lines.append(f"  --font-{fam}: {stack};")
    for group in (data.get("type") or {}).get("groups", []):
        for st in group.get("styles", []):
            lines.append(f"  --type-{st['name']}: {st['fontWeight']} {st['fontSize']}/{st['lineHeight']} var(--font-{group['family']});")
            if st.get("letterSpacing"):
                lines.append(f"  --type-{st['name']}-tracking: {st['letterSpacing']};")
    themed = []
    for fam, body in t.families():
        for tok in body.get("tokens", []):
            v = tok["value"]
            if isinstance(v, dict):
                themed.append((tok["name"], v))
                v = v.get(brand)
            lines.append(f"  --{tok['name']}: {v};")
    lines.append("}")
    for theme in t.themes[1:]:
        lines += ["", f'[data-theme="{theme}"] {{']
        for name in t.colors:
            tok_v = t.colors[name].get("value")
            if isinstance(tok_v, dict) and theme in tok_v:
                lines.append(f"  --{name}: {css_value(t, name, theme)};")
        for name, v in themed:
            if theme in v:
                lines.append(f"  --{name}: {v[theme]};")
        lines.append("}")
    lines += ["", "@theme inline {"]
    for name in t.colors:
        lines.append(f"  --color-{name}: var(--{name});")
    lines.append("}")
    radius = (data.get("radius") or {}).get("tokens", [])
    literal = [f"  --font-{fam}: {stack};" for fam, stack in fams.items()] + [f"  --{r['name']}: {r['value']};" for r in radius]
    if literal:
        lines += ["", "@theme {"] + literal + ["}"]
    for theme in t.themes[1:]:
        lines += ["", f'@custom-variant {theme} (&:where([data-theme="{theme}"], [data-theme="{theme}"] *));']
    lines.append("")
    return "\n".join(lines)


# ---------- brief ----------------------------------------------------------------------------------

ARCHETYPES = {"workspace", "library", "template-form", "run", "problems", "settings"}
SEVERITIES = ("fix", "ask", "note", "ok")
LIFECYCLE = ("draft", "issued", "reissued", "stale", "blocked")
HOLE = re.compile(r"⟨[^⟩]*⟩")


def sections(text):
    """{heading: [lines]} for every '## ' section (the title section under '')."""
    out, cur = {"": []}, ""
    for line in text.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            out[cur] = []
        else:
            out[cur].append(line)
    return out


def table(lines):
    """Rows of the first markdown table in lines, header and separator dropped."""
    rows = [l for l in lines if l.strip().startswith("|")]
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    return [c for c in cells[2:] if c and not set("".join(c)) <= set("-: ")]


def table_rows(lines):
    """Rows of every markdown table in lines."""
    out, cur = [], []
    for line in lines + [""]:
        if line.strip().startswith("|"):
            cur.append(line)
        elif cur:
            out += table(cur)
            cur = []
    return out


def catalogue(ux_dir=None):
    """Component names with a contract row ('| **Name** |') in .components/README.md."""
    readme = Path(ux_dir or UX_TEMPLATE) / ".components" / "README.md"
    if not readme.is_file():
        return set()
    return set(re.findall(r"^\| \*\*([A-Za-z][A-Za-z0-9]*)\*\* \|", readme.read_text(encoding="utf-8"), re.M))


def brief_check(text, known=None):
    out = []

    def rec(level, kind, msg):
        out.append((level, kind, msg))

    secs = sections(text)
    holes = 0
    for name, lines in secs.items():
        for line in lines:
            for h in HOLE.findall(re.sub(r"`[^`]*`", "", line)):  # a hole quoted in backticks is prose
                holes += 1
                rec("ASK", "holes", f"{name or 'title'}: {h}")
    views = table(secs.get("Views", []))
    codes, keys = {}, {}
    for row in views:
        if len(row) < 4 or HOLE.search(" ".join(row)):
            continue
        code, arch, _, key = row[:4]
        if not re.match(r"^[A-Z]{3}$", code):
            rec("FAIL", "views", f"{code!r}: a view code is three uppercase letters")
        if code in codes:
            rec("FAIL", "views", f"{code}: used by two views")
        codes[code] = arch
        if arch.lower() not in ARCHETYPES:
            rec("FAIL", "views", f"{code}: archetype {arch!r} is not one of {', '.join(sorted(ARCHETYPES))}")
        if key in ("", "—", "-"):
            rec("FAIL", "keys", f"{code}: a view needs a shortcut")
        else:
            keys.setdefault(key.lower(), []).append(code)
    for row in table(secs.get("Commands", [])):
        if len(row) < 4 or HOLE.search(" ".join(row)):
            continue
        _, cmd, view, key = row[:4]
        if view.lower() != "any" and view not in codes:
            rec("FAIL", "keys", f"command {cmd!r} lands in {view!r}, which no view row defines")
        if key not in ("", "—", "-"):
            keys.setdefault(key.lower(), []).append(cmd)
    for key, users in keys.items():
        if len(users) > 1:
            rec("FAIL", "keys", f"{key}: used by {', '.join(users)}")
    known = catalogue() if known is None else known
    for row in table(secs.get("Components", [])):
        if row and not HOLE.search(row[0]) and row[0] not in known:
            rec("FAIL", "catalogue", f"{row[0]}: no contract in .components/README.md; add the contract first")
    found = {r[0] for r in table_rows(secs.get("The engine", [])) if r}
    for label, want in (("severity", SEVERITIES), ("lifecycle", LIFECYCLE)):
        missing = [w for w in want if w not in found]
        if missing:
            rec("FAIL", "mapping", f"{label} table lacks: {', '.join(missing)}")
    arch_row = next((r for r in table(secs.get("Product", [])) if r and r[0] == "Archetype"), None)
    if arch_row and not HOLE.search(arch_row[1]) and "workspace" not in arch_row[1].lower():
        rec("WARN", "archetype", "not a workspace: use skills/tailwind-audit/references/norm.md instead")
    if not any(l == "FAIL" for l, _, _ in out):
        rec("OK", "brief", f"{len(codes)} view(s), {sum(len(u) for u in keys.values())} shortcut(s), {holes} hole(s) left")
    return out


# ---------- scaffold -------------------------------------------------------------------------------

SKIP_NAMES = {"__pycache__", ".DS_Store"}


def template_files():
    """Every file of the template, relative to it, in a stable order."""
    return sorted(p.relative_to(UX_TEMPLATE) for p in UX_TEMPLATE.rglob("*")
                  if p.is_file() and not SKIP_NAMES.intersection(p.parts))


def plan(root):
    """[(relative path under .ux/, 'create' | 'exists')] for a scaffold into <root>/.ux/."""
    ux = Path(root) / ".ux"
    return [(rel.as_posix(), "exists" if (ux / rel).exists() else "create") for rel in template_files()]


def scaffold(root, today=None):
    """Copy the template into <root>/.ux/. Never overwrites: an identical file is skipped ('same'); a
    different one gets <name>.template beside it ('beside'), once ('kept' after that)."""
    ux = Path(root) / ".ux"
    stamp = today or datetime.date.today().isoformat()
    done = []
    for rel in template_files():
        dst = ux / rel
        src = UX_TEMPLATE / rel
        body = src.read_bytes()
        if rel.suffix == ".md":
            body = body.decode("utf-8").replace("{{date}}", stamp).encode("utf-8")
        if dst.exists() and dst.read_bytes() == body:
            done.append((rel.as_posix(), "same"))
            continue
        if dst.exists():
            dst = dst.with_name(dst.name + ".template")
            if dst.exists():
                done.append((rel.as_posix(), "kept"))
                continue
            kind = "beside"
        else:
            kind = "created"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(body)
        done.append((rel.as_posix() + (".template" if kind == "beside" else ""), kind))
    return done


def fill(template, values):
    for k, v in values.items():
        template = template.replace("{{" + k + "}}", v)
    return template


def set_block(text, name, rows, header):
    begin, end = f"<!-- ux:{name}:begin -->", f"<!-- ux:{name}:end -->"
    if begin not in text or end not in text:
        return text, False
    head, rest = text.split(begin, 1)
    _, tail = rest.split(end, 1)
    body = "\n".join([header, "|" + "---|" * (header.count("|") - 1)] + rows)
    return f"{head}{begin}\n{body}\n{end}{tail}", True


def expand(ux_dir):
    """One folder per filled Views and Components row of BRIEF.md; refresh the index tables."""
    ux = Path(ux_dir)
    brief = (ux / "BRIEF.md").read_text(encoding="utf-8-sig")
    secs = sections(brief)
    known = catalogue(ux)
    out, view_rows, comp_rows = [], [], []
    view_tpl = (ux / ".views" / "_view.template.md").read_text(encoding="utf-8")
    comp_tpl = (ux / ".components" / "_component.template.md").read_text(encoding="utf-8")
    for row in table(secs.get("Views", [])):
        if len(row) < 4 or HOLE.search(" ".join(row)) or not re.match(r"^[A-Z]{3}$", row[0]):
            continue
        code, arch, purpose, keys = row[:4]
        view_rows.append(f"| [{code}]({code}/README.md) | {arch} | {purpose} | {keys} |")
        dst = ux / ".views" / code / "README.md"
        if dst.exists():
            out.append((f".views/{code}/README.md", "kept"))
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(fill(view_tpl, {"code": code, "archetype": arch, "purpose": purpose, "keys": keys}),
                       encoding="utf-8", newline="\n")
        out.append((f".views/{code}/README.md", "created"))
    for row in table(secs.get("Components", [])):
        if not row or HOLE.search(row[0]):
            continue
        name, used = row[0], (row[1] if len(row) > 1 else "")
        if name not in known:
            out.append((f".components/{name}/", "skipped: no contract"))
            continue
        comp_rows.append(f"| [{name}]({name}/README.md) | {used} | `{name}/` |")
        dst = ux / ".components" / name / "README.md"
        if dst.exists():
            out.append((f".components/{name}/README.md", "kept"))
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(fill(comp_tpl, {"name": name, "used_by": used}), encoding="utf-8", newline="\n")
        out.append((f".components/{name}/README.md", "created"))
    for rel, name, rows, header in ((".views/README.md", "views", view_rows, "| Code | Archetype | Purpose | Keys |"),
                                    (".components/README.md", "components", comp_rows, "| In use | Used by | Folder |")):
        path = ux / rel
        text, ok = set_block(path.read_text(encoding="utf-8"), name, rows, header)
        if ok:
            path.write_text(text, encoding="utf-8", newline="\n")
            out.append((rel, f"index: {len(rows)} row(s)"))
        else:
            out.append((rel, "index markers missing: table not refreshed"))
    return out


# ---------- self-test --------------------------------------------------------------------------------

def selftest():
    base = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    cases = []
    real = check(base)
    fails = [m for lvl, _, m in real if lvl == "FAIL"]
    cases.append((not fails, f"the template passes ({len(fails)} FAIL)" + ("" if not fails else ": " + fails[0])))

    def planted(label, mutate, kind, needle, level="FAIL"):
        d = json.loads(json.dumps(base))
        mutate(d)
        hit = any(lv == level and k == kind and needle in m for lv, k, m in check(d))
        cases.append((hit, f"{kind}: {label}"))

    def col(d, name):
        return next(x for x in d["color"]["tokens"] if x["name"] == name)

    planted("a role dropped", lambda d: d["color"]["tokens"].remove(col(d, "ask-soft")), "roles", "ask-soft")
    planted("value-named token", lambda d: d["color"]["tokens"].append({"name": "blue-600", "value": "#2563eb", "usage": "x"}), "naming", "blue-600")
    planted("hue word in a name", lambda d: col(d, "accent").update(name="cyan"), "naming", "cyan")
    planted("faint text too dark", lambda d: col(d, "ink-faint")["value"].update(void="#2a3a4a"), "contrast", "ink-faint on ground")
    planted("weak control border", lambda d: col(d, "line-strong")["value"].update(paper="#e0e8ef"), "contrast", "line-strong")
    planted("alias to nothing", lambda d: col(d, "link").update(value="{nowhere}"), "value", "{nowhere}")
    planted("named colour", lambda d: col(d, "fix")["value"].update(paper="red"), "value", "'red'")
    planted("duplicate name", lambda d: d["spacing"]["tokens"].append({"name": "ink", "value": "4px", "usage": "x"}), "shape", "used in")
    planted("map instead of list", lambda d: d.update(radius={"radius-xs": {"$value": "2px"}}), "shape", "radius")
    planted("grey neutral", lambda d: col(d, "ink-muted")["value"].update(void="#a0a0a0"), "grey", "ink-muted", "WARN")
    planted("grey ground", lambda d: col(d, "ground")["value"].update(void="#121212"), "ground", "not pure black", "WARN")
    css = build(base, "tokens.template.json")
    cases.append(("--accent: #22d3ee;" in css and '[data-theme="paper"]' in css and "--color-accent: var(--accent);" in css
                  and "--link: var(--system);" in css and "--type-body: 400 13px/20px var(--font-sans);" in css,
                  "build: custom properties, paper override, Tailwind map, alias, type shorthand"))
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "theme.css"
        p.write_text(css + "/* hand edit */\n", encoding="utf-8")
        cases.append((synced(base, p, "tokens.template.json")[0] == "FAIL", "synced: a hand edit is a drift"))
    tpl = (UX_TEMPLATE / "BRIEF.md").read_text(encoding="utf-8")
    res = brief_check(tpl)
    asks = sum(1 for l, _, _ in res if l == "ASK")
    cases.append((not any(l == "FAIL" for l, _, _ in res) and asks > 20, f"brief: the template has only asks ({asks})"))
    filled = HOLE.sub("x", tpl)
    filled = re.sub(r"(## Views.*?\n\|---\|---\|---\|---\|\n).*?(\n\n)",
                    lambda m: m.group(1) + "| EXP | workspace | a | Ctrl 1 |\n| EXP | gallery | b | Ctrl 1 |\n| ex | settings | c | — |" + m.group(2),
                    filled, flags=re.S)
    filled = re.sub(r"(## Commands.*?\n\|---\|---\|---\|---\|\n).*?(\n\n)",
                    lambda m: m.group(1) + "| View | Palette | any | Ctrl K |\n| Edit | Thing | NOP | Ctrl 1 |" + m.group(2),
                    filled, flags=re.S)
    filled = filled.replace("| reissued | x |\n", "")
    filled = re.sub(r"(## Components.*?\n\|---\|---\|\n).*?(\n\n)", lambda m: m.group(1) + "| Gizmo | EXP |" + m.group(2), filled, flags=re.S)
    res = brief_check(filled)
    for kind, needle, label in (("views", "used by two views", "duplicate view code"),
                                ("views", "'gallery'", "unknown archetype"),
                                ("views", "'ex'", "bad view code"),
                                ("keys", "a view needs a shortcut", "view without a key"),
                                ("keys", "ctrl 1: used by", "shortcut used twice"),
                                ("keys", "'NOP'", "command to an unknown view"),
                                ("mapping", "reissued", "lifecycle state unmapped"),
                                ("catalogue", "Gizmo", "component without a contract")):
        cases.append((any(l == "FAIL" and k == kind and needle in m for l, k, m in res), f"brief {kind}: {label}"))
    with tempfile.TemporaryDirectory() as tmp:
        g = Path(tmp) / ".guidelines"
        (g / ".ux").mkdir(parents=True)
        (g / ".ux" / "README.md").write_text("mine\n", encoding="utf-8")
        planned = dict(plan(g))
        cases.append((planned.get("README.md") == "exists" and planned.get("BRIEF.md") == "create"
                      and ".views/_view.template.md" in planned, f"plan: {len(planned)} paths, existing ones flagged"))
        done = dict(scaffold(g, today="2026-01-02"))
        ux = g / ".ux"
        cases.append(((ux / "README.md").read_text(encoding="utf-8") == "mine\n" and (ux / "README.md.template").is_file()
                      and done.get("README.md.template") == "beside", "scaffold: an existing file is never overwritten"))
        cases.append(("2026-01-02" in (ux / ".changelog" / "README.md").read_text(encoding="utf-8")
                      and (ux / ".tokens" / "theme.css").is_file(), "scaffold: dated changelog line, stylesheet copied"))
        again = dict(scaffold(g, today="2026-01-02"))
        cases.append((again.get("README.md") == "kept" and again.get("BRIEF.md") == "same"
                      and not any(v in ("created", "beside") for v in again.values()),
                      "scaffold twice: identical files skipped, the .template kept, nothing written"))
        b = ux / "BRIEF.md"
        text = b.read_text(encoding="utf-8")
        text = re.sub(r"(## Views.*?\n\|---\|---\|---\|---\|\n).*?(\n\n)",
                      lambda m: m.group(1) + "| EXP | workspace | Edit and issue items | Ctrl 1 |\n| CFG | settings | Settings | Ctrl , |" + m.group(2),
                      text, flags=re.S)
        text = re.sub(r"(## Components.*?\n\|---\|---\|\n).*?(\n\n)",
                      lambda m: m.group(1) + "| AppFrame | all |\n| Gizmo | EXP |" + m.group(2), text, flags=re.S)
        b.write_text(text, encoding="utf-8")
        res = dict(expand(ux))
        view = (ux / ".views" / "EXP" / "README.md").read_text(encoding="utf-8")
        cases.append((view.startswith("# EXP — Edit and issue items") and "{{" not in view, "expand: view folder from the brief, slots bound"))
        cases.append(((ux / ".components" / "AppFrame" / "README.md").is_file()
                      and res.get(".components/Gizmo/") == "skipped: no contract", "expand: component with a contract only"))
        idx = (ux / ".views" / "README.md").read_text(encoding="utf-8")
        cases.append(("[EXP](EXP/README.md)" in idx and "[CFG](CFG/README.md)" in idx, "expand: views index refreshed between markers"))
        (ux / ".views" / "EXP" / "README.md").write_text("edited\n", encoding="utf-8")
        expand(ux)
        cases.append(((ux / ".views" / "EXP" / "README.md").read_text(encoding="utf-8") == "edited\n", "expand twice: an edited view is kept"))
    bad = 0
    for ok, label in cases:
        bad += not ok
        print(f"{'pass' if ok else 'MISS'}  {label}")
    print(f"ux selftest: {len(cases) - bad}/{len(cases)} ok")
    return 1 if bad else 0


def synced(data, css_path, source):
    want = build(data, source)
    if not css_path.is_file():
        return "FAIL", f"{css_path.name} missing: run ux.py build"
    if css_path.read_text(encoding="utf-8") != want:
        return "FAIL", f"{css_path.name} differs from its tokens: never hand-edit it; run ux.py build (F4)"
    return "OK", f"{css_path.name} matches its tokens"


def main(argv):
    if "--selftest" in argv:
        return selftest()
    opts = {}
    pos = []
    i = 0
    while i < len(argv):
        if argv[i] in ("--out", "--css") and i + 1 < len(argv):
            opts[argv[i][2:]] = argv[i + 1]
            i += 2
        else:
            pos.append(argv[i])
            i += 1
    if not pos or pos[0] not in ("check", "build", "synced", "brief", "plan", "scaffold", "expand"):
        print(__doc__)
        return 2
    if pos[0] in ("plan", "scaffold", "expand"):
        if len(pos) < 2:
            print(f"{pos[0]}: name the {'.ux directory' if pos[0] == 'expand' else 'guidelines root'}")
            return 2
        if pos[0] == "plan":
            rows = plan(pos[1])
            for rel, state in rows:
                print(f"{state:<7} .ux/{rel}")
            print(f"{sum(1 for _, s in rows if s == 'create')} to create, {sum(1 for _, s in rows if s == 'exists')} existing "
                  "(an existing file gets <name>.template beside it)")
            return 0
        if pos[0] == "scaffold":
            if "--yes" not in argv:
                print("scaffold: run plan first, show the paths, then pass --yes (the Regent's yes)")
                return 2
            for rel, state in scaffold(pos[1]):
                print(f"{state:<8} .ux/{rel}")
            return 0
        for rel, state in expand(pos[1]):
            print(f"{state:<8} {rel}")
        return 0
    if pos[0] == "brief":
        if len(pos) < 2:
            print("brief: name the filled brief file")
            return 2
        found = brief_check(Path(pos[1]).read_text(encoding="utf-8-sig"))
        order = {"FAIL": 0, "WARN": 1, "ASK": 2, "OK": 3}
        for lvl, kind, msg in sorted(found, key=lambda x: order[x[0]]):
            print(f"{lvl:<4}  {kind}: {msg}")
        return 1 if any(l == "FAIL" for l, _, _ in found) else 0
    src = Path(pos[1]) if len(pos) > 1 else TEMPLATE
    data = json.loads(src.read_text(encoding="utf-8-sig"))
    label = src.name
    if pos[0] == "check":
        found = check(data)
        order = {"FAIL": 0, "WARN": 1, "OK": 2}
        for lvl, kind, msg in sorted(found, key=lambda x: order[x[0]]):
            print(f"{lvl:<4}  {kind}: {msg}")
        return 1 if any(l == "FAIL" for l, _, _ in found) else 0
    if pos[0] == "build":
        css = build(data, label)
        out = Path(opts["out"]) if "out" in opts else (THEME_CSS if src == TEMPLATE else None)
        if out:
            out.write_text(css, encoding="utf-8", newline="\n")
            print(f"wrote {out}")
        else:
            sys.stdout.write(css)
        return 0
    lvl, msg = synced(data, Path(opts["css"]) if "css" in opts else THEME_CSS, label)
    print(f"{lvl:<4}  synced: {msg}")
    return 1 if lvl == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
