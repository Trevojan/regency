#!/bin/bash
# reg7.sh <commit>: QA-05's hz, ko, ex, sib, stack, cdl probes against one export; one file per probe
C=$1; Q=/tmp/claude-0/-home-user-regency/dc20ab22-eaa8-5c2e-958b-8e9e75950e62/scratchpad/qa7; P=/home/user/regency/.changelog/inspection/QA-grant-latest-05; S=$Q/x-$C/scripts; O=$Q/reg-$C; rm -rf $O; mkdir -p $O/tmp
export TMPDIR=$O/tmp HOME=$O/home; mkdir -p $HOME
unset CLAUDE_PROJECT_DIR CLAUDE_PLUGIN_DATA REGENCY_JD REGENCY_HOOK_STATE REGENCY_JUDGE_HOME
for k in $(env | grep -oE '^GIT_CONFIG_[A-Z0-9_]+'); do unset $k; done; unset CLAUDE_CODE_SESSION_ID CLAUDECODE
for p in hz ko ex; do python3 -I $P/$p.py $S > $O/$p.txt 2>&1; done
bash $P/sib-fixture.sh $O/sibfx >/dev/null 2>&1; python3 -I $P/sib.py $S $O/sibfx > $O/sib.txt 2>&1; python3 -I $P/stack.py $S $O/sibfx > $O/stack.txt 2>&1
bash $P/cdl-fixture.sh $O/cdlfx >/dev/null 2>&1; python3 -I $P/cdl.py $S $O/cdlfx > $O/cdl.txt 2>&1
for p in hz ko ex sib stack cdl; do sed -i -E "s#$O/[a-z]*/?tmp[A-Za-z0-9_]*#<T>#g; s#$O/(sibfx|cdlfx)#<F>#g" $O/$p.txt; done
