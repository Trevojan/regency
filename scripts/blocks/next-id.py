"""next-id - the next free number of an id series: ORD-####, EMS-###, SRL-###, GT-##, C-##.

Every occurrence counts, in file names and in text, so a number cited anywhere is never handed out again.
"""
import re
from collections import Counter
from pathlib import Path

CARD = {
    "id": "next-id",
    "intent": "the next free number of an id series such as ORD-0007, EMS-012, SRL-003 or GT-04",
    "when": ["next id", "next number", "new order number", "numbering", "id series", "increment id", "new entry id",
             "sequence number"],
    "args": {
        "prefix": {"type": "str", "help": "the id's fixed part with its separator: ORD-, EMS-, SRL-"},
        "path": {"type": "path", "default": ".", "help": "a file, or a folder whose file names and text are scanned"},
        "width": {"type": "int", "default": 0, "help": "digits; 0 keeps the most common width found (3 when none)"},
    },
    "confirm": "read",
    "returns": "{next, last, found, width}",
}
TEXT = {".md", ".txt", ".json", ".xml", ".pgml", ".hgml", ".yml", ".yaml", ".toml", ".csv", ".py"}
SKIP = {".git", "node_modules", "__pycache__", "dist"}
MAX_BYTES = 1 << 20


def scan(target, pattern):
    found = []
    entries = [target] if target.is_file() else [p for p in target.rglob("*")
                                                  if not SKIP.intersection(p.relative_to(target).parts)]
    for p in entries:
        found += pattern.findall(p.name)
        if p.is_file() and p.suffix.lower() in TEXT and p.stat().st_size <= MAX_BYTES:
            found += pattern.findall(p.read_text(encoding="utf-8", errors="replace"))
    return found


def run(a, root):
    prefix = a["prefix"]
    if not prefix or prefix[-1].isdigit():
        raise ValueError("prefix must be the fixed part before the digits, e.g. ORD-")
    target = Path(root) / a["path"]
    if not target.exists():
        raise ValueError(f"{a['path']} does not exist")
    pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(prefix) + r"(\d+)(?!\d)")
    digits = scan(target, pattern)
    numbers = sorted({int(d) for d in digits})
    widths = Counter(len(d) for d in digits).most_common()
    width = a["width"] or (max(w for w, n in widths if n == widths[0][1]) if widths else 3)
    last = numbers[-1] if numbers else 0
    nxt = f"{prefix}{str(last + 1).zfill(width)}"
    last_id = f"{prefix}{str(last).zfill(width)}" if numbers else None
    return {"summary": f"next {nxt} (last {last_id or 'none'}, {len(numbers)} number(s) found under {a['path']})",
            "result": {"next": nxt, "last": last_id, "found": len(numbers), "width": width}}


def selftest(tmp):
    (tmp / "orders").mkdir()
    (tmp / "orders" / "ORD-0001.pgml").write_text("x", encoding="utf-8")
    (tmp / "orders" / "ORD-0003.md").write_text("follows ORD-0005, not XORD-0999 nor ORD-00071", encoding="utf-8")
    (tmp / ".git").mkdir()
    (tmp / ".git" / "ORD-0099").write_text("", encoding="utf-8")
    r = run({"prefix": "ORD-", "path": ".", "width": 0}, str(tmp))["result"]
    assert r["next"] == "ORD-0072" and r["width"] == 4, r
    r = run({"prefix": "ORD-", "path": "orders/ORD-0001.pgml", "width": 0}, str(tmp))["result"]
    assert r["next"] == "ORD-0002", r
    r = run({"prefix": "SRL-", "path": ".", "width": 0}, str(tmp))["result"]
    assert r["next"] == "SRL-001" and r["last"] is None, r
    assert run({"prefix": "SRL-", "path": ".", "width": 2}, str(tmp))["result"]["next"] == "SRL-01"
    for bad in ({"prefix": "", "path": ".", "width": 0}, {"prefix": "ORD-", "path": "missing", "width": 0}):
        try:
            run(bad, str(tmp))
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")
