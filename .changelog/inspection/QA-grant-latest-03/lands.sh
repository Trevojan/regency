#!/bin/bash
# lands.sh <fixture dir> <who: agent|regent> <cwd> -- <git args...>  -> prints LANDED or HELD, restores remote
Q=/tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa3
D=$1; WHO=$2; CWD=$3; shift 4
for k in $(env | grep -oE '^GIT_CONFIG_[A-Z0-9_]+'); do unset $k; done
unset CLAUDE_CODE_SESSION_ID CLAUDECODE CLAUDE_PLUGIN_DATA
export REGENCY_HOOK_STATE=$D/state REGENCY_JUDGE_HOME=$D/home
before=$(git -C $D/remote.git for-each-ref --format='%(refname) %(objectname)' refs/heads)
if [ "$WHO" = agent ]; then
  export CLAUDE_CODE_SESSION_ID=${SID:-s1}
  eval "$(python3 -c 'import json,sys; [print(f"export {k}={json.dumps(v)}") for k,v in json.load(open(sys.argv[1]))["env"].items()]' $D/work/.claude/settings.local.json)"
fi
out=$(cd $CWD && git -c user.name=t -c user.email=t@t.invalid "$@" 2>&1); rc=$?
after=$(git -C $D/remote.git for-each-ref --format='%(refname) %(objectname)' refs/heads)
if [ "$before" != "$after" ]; then echo "LANDED rc=$rc :: git $*"; else echo "HELD   rc=$rc :: git $* :: $(echo "$out" | grep -m1 regency: | cut -c1-110)"; fi
# restore
for r in $(echo "$after" | awk '{print $1}'); do echo "$before" | grep -q "^$r " || git -C $D/remote.git update-ref -d $r; done
echo "$before" | while read r s; do git -C $D/remote.git update-ref $r $s; done
