#!/bin/bash
# suite.sh <export dir> <env: session|clean> : every --selftest doctor runs, one line each
X=$1; MODE=$2; Q=/tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa4
export TMPDIR=$Q/tmp HOME=$Q/home-$MODE-$(basename $X); mkdir -p $HOME
unset CLAUDE_PROJECT_DIR CLAUDE_PLUGIN_DATA REGENCY_JD REGENCY_HOOK_STATE REGENCY_JUDGE_HOME
if [ "$MODE" = clean ]; then for k in $(env | grep -oE '^GIT_CONFIG_[A-Z0-9_]+'); do unset $k; done; unset CLAUDE_CODE_SESSION_ID CLAUDECODE; fi
cd $X
for s in guard-push hook-acts-guard hook-elicit hook-gov hook-hazard hook-journal hook-judge hook-lineage hook-packs hook-reads hook-refs hook-resume hook-shortcuts hook-verbs ux gov returns idx shortcuts vp speed migrate health judge analytics alpha locate reconstruction elicit headless packs conventions_check install-automode; do
  [ -f scripts/$s.py ] || { echo "$s: absent"; continue; }
  out=$(python3 scripts/$s.py --selftest 2>&1); rc=$?
  echo "$s rc=$rc :: $(echo "$out" | grep -v '^ *$' | tail -1 | cut -c1-120) $(echo "$out" | grep -c '^MISS')miss"
done
