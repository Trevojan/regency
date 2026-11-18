"""D4 oracle: carried = bytes of only the lines an earlier session read at the same path and sha256.
Independent of reconstruction.py: a set of (path, sha, line) per earlier session, bytes summed from the file.
Usage: python3 -B q4_oracle.py <scripts dir> <seed> [rounds]"""
import sys, os, re, random, tempfile, hashlib, importlib.util, collections
sys.dont_write_bytecode = True
S = sys.argv[1]; sys.path.insert(0, S)
import hook_wire as wire, reconstruction as rc
spec = importlib.util.spec_from_file_location("hr", S + "/hook-reads.py"); hr = importlib.util.module_from_spec(spec); spec.loader.exec_module(hr)
seed = int(sys.argv[2]); rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 20
rnd = random.Random(seed)
bad = 0
for rd in range(rounds):
    tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
    root = wire.build_fixture(tmp + "/proj")
    files = [root / ".guidelines/f_utf8.md", root / ".guidelines/f_crlf.md", root / ".guidelines/f_nonl.md"]
    def content(i, gen):
        n = rnd.randint(5, 40)
        if i == 0:
            return "".join(f"{k} ação ✓ {'é' * rnd.randint(0, 5)}{gen}\n" for k in range(n)).encode()
        if i == 1:
            return "".join(f"crlf {k} {'x' * rnd.randint(0, 9)}{gen}\r\n" for k in range(n)).encode()
        return ("\n".join(f"nonl {k} {'y' * rnd.randint(0, 9)}{gen}" for k in range(n))).encode()
    for i, f in enumerate(files):
        f.write_bytes(content(i, 0))
    sessions = [f"s{k}" for k in range(rnd.randint(2, 6))]
    log = []  # (session, path, sha, set of line numbers, {line: bytes})
    gen = 0
    for sid in sessions:
        for _ in range(rnd.randint(1, 8)):
            if rnd.random() < 0.15:
                gen += 1; j = rnd.randrange(3); files[j].write_bytes(content(j, gen))
            f = rnd.choice(files)
            raw = f.read_bytes()
            lines = re.findall(rb"[^\n]*\n|[^\n]+$", raw)
            ti = {"file_path": str(f)}
            if rnd.random() < 0.8:
                ti["offset"] = rnd.randint(1, len(lines) + 3)
            if rnd.random() < 0.8:
                ti["limit"] = rnd.randint(1, len(lines) + 3)
            first = ti.get("offset", 1); count = ti.get("limit", 2000)
            got = {k: len(lines[k - 1]) for k in range(first, min(first + count - 1, len(lines)) + 1)}
            hr.respond({"hook_event_name": "PostToolUse", "tool_name": "Read", "session_id": sid, "cwd": str(root),
                        "tool_input": ti})
            log.append((sid, f.name, hashlib.sha256(raw).hexdigest(), got))
    # oracle
    order = []
    for sid, *_ in log:
        if sid not in order:
            order.append(sid)
    seen = collections.defaultdict(set)   # session -> {(path, sha, line)}
    want = collections.OrderedDict((s, [0, 0]) for s in order)
    for sid, p, h, got in log:
        earlier = set().union(*[seen[s] for s in order[:order.index(sid)]]) if order.index(sid) else set()
        want[sid][0] += sum(got.values())
        want[sid][1] += sum(b for k, b in got.items() if (p, h, k) in earlier)
        seen[sid] |= {(p, h, k) for k in got}
    m = rc.measure(rc.load(root)[0], sessions=100)
    tool = collections.OrderedDict((x["session"], [x["read"], x["carried"]]) for x in m["sessions"])
    if dict(tool) != dict(want):
        bad += 1
        print("MISMATCH round", rd, "oracle", dict(want), "tool", dict(tool))
print(f"seed {seed}: {rounds - bad}/{rounds} rounds agree with the hand oracle")
