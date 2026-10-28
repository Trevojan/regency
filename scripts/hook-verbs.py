#!/usr/bin/env python3
"""hook-verbs.py - UserPromptSubmit: the Regent spoke, and a new pass begins.

Three jobs, one line of context at most:

  confirm   the cloud commands the Regent quoted in this message become the only cloud writes
            allowed until the next message (hook-hazard.py; R5.1). Each message replaces the list.
  release   a message that opens with a release verb ends the session's hazard watch (R5.2)
  route     a short message that opens with one of the Regent's verbs is mapped to its command

Every verb, the release verbs included, is read from the table in library/conventions.md §9
(hook_wire.regent_verbs). This script holds no copy of it.

  e.g. "prossiga"  ->  Regent verb 'prossiga' = work the whole queue -> /regency:proceed (conventions §9)
       "libere"    ->  hazard watch released by the Regent ('libere')

Slash commands are never routed. Messages longer than 80 characters are not routed (a verb inside a
sentence is prose, not an order), but their quoted cloud commands still count as confirmations.

Market pattern: intent routing before the model call (router / triage agent), done by a table
instead of by inference; approvals scoped to one exact call and one pass.

Modes:  (no args) hook · --selftest · --table (print the verbs as parsed)
Pure standard library, Python 3.8+.
"""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_wire as wire  # noqa: E402

_spec = importlib.util.spec_from_file_location("hook_hazard", HERE / "hook-hazard.py")
hazard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hazard)


def respond(event, table=None):
    table = wire.regent_verbs() if table is None else table
    prompt = wire.regent_text(event.get("prompt"))
    quoted = hazard.confirmations(prompt)
    if quoted:
        wire.save_state(event, "cloud", {"commands": quoted, "at": wire.now()})
    else:
        wire.clear_state(event, "cloud")
    parts = []
    row = wire.opening_verb(prompt, table)
    if row and wire.RELEASE_COMMAND in row[2]:
        if wire.clear_state(event, "hazard"):
            parts.append(f"hazard watch released by the Regent ('{row[0]}')")
    elif row:
        parts.append(f"Regent verb '{row[0]}' = {row[1]} -> {row[2]} (conventions §9)")
    if quoted:
        parts.append(f"cloud writes confirmed for this pass: {'; '.join(quoted)}")
    return wire.context("UserPromptSubmit", wire.one_line(*parts)) if parts else None


SAMPLE = """## 9. Verbs the Regent uses (what they mean here)

| Says | Means | Command |
|---|---|---|
| prossiga, siga, continue, bora | work the whole queue | `/regency:proceed` |
| commite, mescle | split commits, merge up to main, push the other branches (never main) | `/regency:arrange-cycle-commit` |
| vê isso, diga o que mudaria, mede | report what would change; apply nothing | `/regency:measure-changes` |
| retome | reopen from the shortcuts index only | `/regency:order:resume` |
| libere, release | end the hazard watch: file writes stop asking | `hook-hazard.py --clear` |

## 10. Returning to a repository
"""


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["REGENCY_HOOK_STATE"] = str(Path(tmp) / "state")
        table = wire.verb_table(SAMPLE)

        def text(answer):
            return (answer or {}).get("hookSpecificOutput", {}).get("additionalContext", "")

        def ev(prompt, sid="s1"):
            return {"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": prompt}

        cases = [
            (len(table) == 12, f"table parsed from §9 ({len(table)} phrases)"),
            (wire.release_words(table) == ["release", "libere"], "release verbs read from §9"),
            ("/regency:proceed" in text(respond(ev("prossiga"), table)), "'prossiga' -> proceed"),
            ("/regency:proceed" in text(respond(ev("Bora!"), table)), "case and punctuation"),
            ("/regency:arrange-cycle-commit" in text(respond(ev("commite e mescle por favor"), table)), "verb opening a short order"),
            ("/regency:measure-changes" in text(respond(ev("diga o que mudaria se trocarmos o parser"), table)), "multi-word verb"),
            (respond(ev("/regency:proceed"), table) is None, "slash commands are not routed"),
            (respond(ev("please continue " + "x" * 90), table) is None, "long prose is not routed"),
            (respond(ev("explain the ledger"), table) is None, "no verb: silent"),
            (respond(ev("seguinte: o parser"), table) is None, "'siga' does not match inside 'seguinte'"),
        ]
        wire.save_state(ev(""), "hazard", {"label": "rm -rf build", "at": "t"})
        respond(ev("ok, look at what is left"), table)
        cases.append((wire.load_state(ev(""), "hazard") is not None, "an ordinary message keeps the watch on"))
        out = text(respond(ev("libere"), table))
        cases.append(("released" in out and wire.load_state(ev(""), "hazard") is None, "a release verb ends the watch"))
        cases.append((respond(ev("libere"), table) is None, "release with no watch on: silent"))
        reminder = "<system-reminder>The user's timezone is America/Sao_Paulo (UTC-03:00). Message sent at 12:27 local time.</system-reminder>"
        wire.save_state(ev(""), "hazard", {"label": "rm -rf build", "at": "t"})
        out = text(respond(ev(reminder + "release"), table))
        cases.append(("released" in out and wire.load_state(ev(""), "hazard") is None,
                      "a release verb behind a harness <system-reminder> still ends the watch"))
        respond(ev(reminder.replace("12:27 local time.", "`gcloud run deploy api --region us-east1`") + "ok"), table)
        cases.append((wire.load_state(ev(""), "cloud") is None,
                      "a command quoted inside a <system-reminder> confirms nothing"))
        long_msg = "pode seguir com o deploy, eu revisei tudo e confirmo: `gcloud run deploy api --region us-east1`"
        out = text(respond(ev(long_msg), table))
        st = wire.load_state(ev(""), "cloud")
        cases.append((st and st["commands"] == ["gcloud run deploy api --region us-east1"] and "confirmed" in out,
                      "a quoted cloud command is confirmed for the pass"))
        respond(ev("prossiga"), table)
        cases.append((wire.load_state(ev(""), "cloud") is None, "the next message ends the pass: confirmation gone"))
        real = wire.regent_verbs()
        if wire.CONVENTIONS.is_file():
            cases.append((len(real) >= 6 and wire.release_words(real), f"real conventions §9 parses ({len(real)} phrases, "
                                                                       f"release: {wire.release_words(real)})"))
        return wire.check(cases)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        sys.exit(selftest())
    if "--table" in a:
        for phrase, meaning, cmd in wire.regent_verbs():
            print(f"{phrase:<24} {cmd:<34} {meaning}")
        sys.exit(0)
    sys.exit(wire.serve(respond))
