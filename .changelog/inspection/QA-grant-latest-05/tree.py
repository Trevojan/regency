"""tree.py <root> <folders> <files per folder> [fanout]: empty files in a tree of folders, none a repository."""
import os, sys
root, nf, per = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); fan = int(sys.argv[4]) if len(sys.argv) > 4 else 30
dirs = [root]; made = 0
i = 0
while made < nf:
    parent = dirs[i // fan]; d = os.path.join(parent, f"d{made}"); os.makedirs(d, exist_ok=True); dirs.append(d); made += 1; i += 1
for d in dirs[1:]:
    for k in range(per):
        os.close(os.open(os.path.join(d, f"f{k}"), os.O_CREAT | os.O_WRONLY, 0o644))
print(len(dirs) - 1, "folders,", (len(dirs) - 1) * per, "files")
