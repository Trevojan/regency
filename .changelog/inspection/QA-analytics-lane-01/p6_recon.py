import sys, os, tempfile, importlib.util
sys.dont_write_bytecode = True
S = "/home/user/regency/scripts"; sys.path.insert(0, S)
import hook_wire as wire, reconstruction as rc
spec = importlib.util.spec_from_file_location("hr", S + "/hook-reads.py"); hr = importlib.util.module_from_spec(spec); spec.loader.exec_module(hr)
tmp = tempfile.mkdtemp(); os.environ["REGENCY_HOOK_STATE"] = tmp + "/state"
root = wire.build_fixture(tmp + "/proj")
doc = root / ".guidelines/big.md"
doc.write_text("".join(f"line {i:04d}\n" for i in range(1, 101)), encoding="utf-8")   # 100 lines x 10 bytes
def read(sid, **ti):
    hr.respond({"hook_event_name": "PostToolUse", "tool_name": "Read", "session_id": sid, "cwd": str(root),
                "tool_input": dict({"file_path": str(doc)}, **ti)})
read("s1", offset=1, limit=10)      # s1 reads lines 1-10   (100 bytes)
read("s2", offset=51, limit=50)     # s2 reads lines 51-100 (500 bytes) - none of them read before
m = rc.measure(rc.load(root)[0])
s2 = m["sessions"][1]
print("s2 read", s2["read"], "carried (tool)", s2["carried"], "ratio", s2["ratio"])
print("oracle by hand: bytes of s2's lines that an earlier session read = 0 -> ratio 0.0")
