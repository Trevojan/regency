#!/bin/bash
# sib-fixture.sh <dir>: proj (git) with current -> releases/v2 inside it; sibling (git, with a commit and a dirty file) beside it
F=$1; mkdir -p $F; cd $F
G="git -c user.name=t -c user.email=t@t.invalid -c init.defaultBranch=main -c commit.gpgsign=false"
$G init -q proj; mkdir -p proj/releases/v2; ln -sfn $F/proj/releases/v2 proj/current
$G init -q sibling; echo a > sibling/a; $G -C sibling add a; $G -C sibling commit -qm a; echo dirty > sibling/a
