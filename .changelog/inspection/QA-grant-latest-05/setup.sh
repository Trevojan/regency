#!/bin/bash
# setup.sh <dir>: bare remote with main/master/feat, a work clone with hook-refs installed (core.hooksPath way)
set -e
Q=/tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa3
D=$1; rm -rf "$D"; mkdir -p "$D"; cd "$D"
for k in $(env | grep -oE '^GIT_CONFIG_[A-Z0-9_]+'); do unset $k; done
unset CLAUDE_CODE_SESSION_ID CLAUDECODE
G="git -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false"
$G init -q --bare -b main remote.git
$G clone -q remote.git work 2>/dev/null; cd work
$G checkout -q -b main; echo A > A; $G add A; $G commit -qm A
$G branch master; $G branch feat
$G push -q origin main master feat
$G checkout -q feat; echo C > C; $G add C; $G commit -qm C
$G checkout -q main; echo B > B; $G add B; $G commit -qm B
$G checkout -q feat
python3 $Q/x/0cbf13d/scripts/hook-refs.py --install "$D/work"
