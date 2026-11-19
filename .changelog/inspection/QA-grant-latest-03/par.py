import sys, os, json, importlib.util, subprocess, tempfile
from pathlib import Path
S = Path(sys.argv[1]); sys.path.insert(0, str(S))
mode = sys.argv[2]
if mode == "child":
    vdir, who, n = sys.argv[3], sys.argv[4], int(sys.argv[5])
    import gov
    spec = importlib.util.spec_from_file_location("hj", S/"hook-journal.py"); hj = importlib.util.module_from_spec(spec); spec.loader.exec_module(hj)
    for i in range(n):
        gov.record(vdir, {"order": "G1", "mode": "self", "element": "action", "from": "DV", "to": "PO"}, session=f"{who}")
        hj.append(Path(vdir), {"regency.event": "par", "who": who, "i": i})
    sys.exit(0)
vdir = Path(tempfile.mkdtemp()); P, N = 8, 25
procs = [subprocess.Popen([sys.executable, __file__, str(S), "child", str(vdir), f"w{k}", str(N)]) for k in range(P)]
for p in procs: p.wait()
q = (vdir/"gov-queue.jsonl").read_text().splitlines(); j = (vdir/"checkpoints.jsonl").read_text().splitlines()
keys = json.loads((vdir/"gov-keys.json").read_text()); packets = sum(x["packets"] for x in keys["passes"])
print(f"writers={P}x{N}: gov-queue lines={len(q)} (want {P*N}, KEEP caps it), gov-keys packets={packets} (want {P*N}), journal lines={len(j)} (want {P*N}), locks left={list(vdir.glob('.*.lock'))}")
