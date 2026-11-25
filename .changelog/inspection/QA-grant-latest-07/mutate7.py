"""mutate6.py <src scripts dir> <work dir> [label prefix...]: remove each part of attempt 6's fix in a fresh copy; report
which self-test cases go red."""
import shutil, subprocess, sys, os
from pathlib import Path
SRC, WORK = Path(sys.argv[1]), Path(sys.argv[2]); ONLY = sys.argv[3:]
H, J = "hook-hazard.py", "judge.py"
M = {
 "H1 set never read": (H, 'if w and name(w[0]) == "set":', "if False:"),
 "H2 set: an unknown letter does not void it": (H, "    if not started and any(letter not in SET_LETTERS for _, letter, _ in options):\n        return physical", "    if False:\n        return physical"),
 "H3 set: an unknown -o name does not stop it": (H, '        if letter == "o" and not started and value not in SET_NAMES:\n            return physical', "        if False:\n            return physical"),
 "H4 set +P never turns it off": (H, "            physical = on\n    return physical", "            physical = physical or on\n    return physical"),
 "H5 '-' and '--' do not end the options": (H, ' and args[index] not in ("-", "--")', ""),
 "H6 -o takes no name": (H, '            index += letter in "oO"', "            index += 0"),
 "H7 a started shell's options never read": (H, 'started = bool(w) and name(w[0]) in ("bash", "sh") and shell_mode(w[1:], False, started=True)', "started = False"),
 "H8 a nested shell inherits the line's mode": (H, "out += acts(t, here, depth + 1, root, deadline, started)", "out += acts(t, here, depth + 1, root, deadline, physical or started)"),
 "H9 cd -L does not override physical mode": (H, 'return {"P": True, "L": False}.get("".join(flags)[-1:])', 'return {"P": True}.get("".join(flags)[-1:])'),
 "H10 a cd with no flag is logical whatever the mode": (H, "            mode = physical if option is None else option", "            mode = bool(option)"),
 "H11 pushd ignores the mode": (H, 'option = cd_mode(w[1:]) if name(w[0]) == "cd" else None', 'option = cd_mode(w[1:]) if name(w[0]) == "cd" else False'),
 "H12 --rcfile takes no file": (H, 'index += word in ("--rcfile", "--init-file")', "index += 0"),
 "H13 git clean: the exclude pattern is a path": (H, "        if takes_pattern(word):\n            next(left, None)", "        if False:\n            next(left, None)"),
 "H14 git clean: a cluster ending in e takes no pattern": (H, 'return bool(re.fullmatch(r"-[^-e]*e", word)) or', 'return word == "-e" or'),
 "H15 git clean: --exclude only in full": (H, 'or (len(word) > 2 and "--exclude".startswith(word))', 'or word == "--exclude"'),
 "H16 git clean: one -f per word": (H, 'return cluster.group(1).count("f") if cluster else 0', 'return min(1, cluster.group(1).count("f")) if cluster else 0'),
 "H17 git clean: --force not counted": (H, '    if len(word) > 2 and "--force".startswith(word):\n        return 1', "    if False:\n        return 1"),
 "H18 git clean: words after '--' dropped": (H, "return forced, paths + list(left)", "return forced, paths"),
 "H19 git clean: one -f searches nothing (attempt 5)": (H, 'below = reached(paths or ["."], where, root, deadline, bare=forced < 2)', 'below = reached(paths or ["."], where, root, deadline) if forced >= 2 else []'),
 "H20 git clean: one -f searches every repository": (H, "bare=forced < 2)", "bare=False)"),
 "H21 git clean: two -f search only bare ones": (H, "bare=forced < 2)", "bare=True)"),
 "J1 bare search: a clone is not passed whole": (J, '        return "passed"', "        return None"),
 "J2 bare search: a .git file is not passed": (J, "(not os.path.isdir(folder / GIT) or git_reads(folder / GIT))", "git_reads(folder / GIT)"),
 "J3 bare search: any HEAD/objects/refs folder is bare": (J, 'return "found" if set(BARE) <= names and git_reads(folder) else None', 'return "found" if set(BARE) <= names else None'),
 "J4 git_reads: a detached HEAD not read": (J, 'rb"ref:\\s*refs/|[0-9a-fA-F]{40}"', 'rb"ref:\\s*refs/"'),
 "J5 git_reads: 'ref:' needs a space": (J, 'rb"ref:\\s*refs/|', 'rb"ref: refs/|'),
 "J6 git_reads: a linked HEAD never reads": (J, 'return os.readlink(head).startswith("refs/")', "return False"),
 "J7 git_reads: an unreadable HEAD is no repository": (J, "    except OSError:\n        return True\n    return named", "    except OSError:\n        return False\n    return named"),
 "J8 git_reads: objects and refs not checked": (J, 'return named and all(os.access(folder / part, os.X_OK) for part in ("objects", "refs"))', "return named"),
 "J9 repositories_below ignores bare": (J, "meets = bare_meets if bare else repository_meets", "meets = repository_meets"),
 "J10 a passed folder counts as found": (J, 'found += [folder] if met == "found" else []', "found += [folder]"),
 "J11 a passed folder is searched through": (J, '        if met:\n            found += [folder] if met == "found" else []\n            continue', '        if met == "found":\n            found += [folder]\n            continue'),
 "J12 git_reads: a missing HEAD reads as one": (J, "    except FileNotFoundError:\n        return False", "    except FileNotFoundError:\n        return True"),
 "G1 rm: the own .git not added": (H, "                + own_git(written, here, root, deep) or [None])", "                or [None])"),
 "G2 find: the own .git not added": (H, '                + own_git(args[:stop] or ["."], here, root, True))', "                )"),
 "G3 relative: a path in the own .git is in the repository": (J, "if lands_in(path, repo) and not in_own_git(path, repo):", "if lands_in(path, repo):"),
 "G4 in_own_git: only the .git itself, not a path in it": (J, "    return top / GIT in [real] + list(real.parents)", "    return real == top / GIT"),
 "G5 own_git_below: never": (J, "    return [top / GIT] if real == top and os.path.lexists(top / GIT) else []", "    return []"),
 "G6 own_git_below: a .git file is not seen": (J, "real == top and os.path.lexists(top / GIT)", "real == top and os.path.isdir(top / GIT)"),
 "G7 picker: dot names matched by any wildcard": (H, '(part[:1] == "." or entry[:1] != ".")', "True"),
 "G8 own_git: a glob matching .git not read": (H, "reaches = whole if pick is None else pick(judge.GIT)", "reaches = whole if pick is None else False"),
 "G9 own_git: a recursion from the root not read": (H, "reaches = whole if pick is None else pick(judge.GIT)", "reaches = False if pick is None else pick(judge.GIT)"),
 "G10 judge check: the root's .git not added": (J, "                paths += own_git_below(p, repo)", "                pass"),
 "G11 in_own_git: the written path, links not followed": (J, "    real, top = Path(os.path.realpath(str(path))), Path(os.path.realpath(str(repo)))\n    return top / GIT in", "    real, top = Path(os.path.normpath(str(path))), Path(os.path.realpath(str(repo)))\n    return top / GIT in"),
}
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG_")}
for k in ("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_DATA", "REGENCY_JD", "REGENCY_HOOK_STATE", "REGENCY_JUDGE_HOME"):
    env.pop(k, None)
for label, (f, old, new) in M.items():
    if ONLY and not any(label.startswith(o + " ") for o in ONLY):
        continue
    d = WORK / label.split()[0]
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(SRC, d / "scripts"); shutil.copytree(SRC.parent / "library", d / "library")
    t = (d / "scripts" / f).read_text(encoding="utf-8")
    if t.count(old) != 1:
        print(f"== {label}: PATTERN COUNT {t.count(old)}", flush=True); continue
    (d / "scripts" / f).write_text(t.replace(old, new), encoding="utf-8")
    print(f"== {label}", flush=True)
    for s in ("hook-hazard", "judge", "hook-judge"):
        r = subprocess.run([sys.executable, f"scripts/{s}.py", "--selftest"], cwd=d, capture_output=True, text=True, env=env, timeout=900)
        miss = [l[6:] for l in r.stdout.splitlines() if l.startswith("MISS")]
        tail = (r.stdout.strip().splitlines() or [r.stderr.strip()[-150:]])[-1]
        print(f"   {s}: {tail[:90]}", flush=True)
        for m in miss: print(f"      MISS {m[:150]}", flush=True)
