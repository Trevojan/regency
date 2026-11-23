#!/bin/bash
# cdl-fixture.sh <dir>: proj (a git repo) with current -> releases/v2 (inside) and cache -> ../outside (a git repo); alias -> proj
F=$1; mkdir -p $F; cd $F
G="git -c user.name=t -c user.email=t@t.invalid -c init.defaultBranch=main"
$G init -q proj; mkdir -p proj/releases/v2 proj/src outside/precious; $G init -q outside
ln -sfn $F/proj/releases/v2 proj/current; ln -sfn $F/outside proj/cache; ln -sfn $F/proj alias
