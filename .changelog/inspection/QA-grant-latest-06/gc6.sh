#!/bin/bash
# gc6.sh <dir>: proj (git, one commit) with untracked tmp/clone (git init), vendor.git (bare), keep/, src/f, x.log,
# junk/inner.git (bare, deeper), nest/clone2 (git init) holding inner.git (bare, inside a clone); plain: data/ shaped like bare
set -e; D=$1; rm -rf $D; mkdir -p $D; cd $D
for k in $(env | grep -oE '^GIT_CONFIG_[A-Z0-9_]+'); do unset $k; done
G="git -c user.name=t -c user.email=t@t.invalid -c init.defaultBranch=main -c commit.gpgsign=false"
$G init -q proj; cd proj; echo t > tracked; $G add tracked; $G commit -qm t
mkdir -p tmp keep src junk nest; $G init -q tmp/clone; echo c > tmp/clone/c; $G init -q --bare vendor.git
echo f > src/f; echo l > x.log; echo k > keep/k; $G init -q --bare junk/inner.git; $G init -q nest/clone2; $G init -q --bare nest/clone2/inner.git
mkdir -p data/objects data/refs; echo "not a repo" > data/HEAD
