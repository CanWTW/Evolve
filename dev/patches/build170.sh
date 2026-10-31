#!/bin/bash
set -e
SP=/tmp/claude-0/-home-claude/83fb3698-30c5-58f9-bdc7-80bd93563198/scratchpad
python3 $SP/patch_p170a.py /home/claude/evolve/index.html $SP/v170a.html
python3 $SP/patch_p170b.py $SP/v170a.html $SP/v170b.html
python3 $SP/patch_p170c.py $SP/v170b.html $SP/v170c.html
LAST=$SP/v170c.html
for p in d e f; do if [ -f $SP/patch_p170$p.py ]; then python3 $SP/patch_p170$p.py $LAST $SP/v170$p.html; LAST=$SP/v170$p.html; fi; done
python3 $SP/patch_p170z.py $LAST $SP/index_v0170.html
node -e "const fs=require('fs');const a=require('$SP/node_modules/acorn');const h=fs.readFileSync('$SP/index_v0170.html','utf8');const re=/<script[^>]*>([\s\S]*?)<\/script>/g;let m,bad=0;while((m=re.exec(h))){if(!m[1].trim())continue;try{a.parse(m[1],{ecmaVersion:2022})}catch(e){bad=1;const L=m[1].split('\n');console.log('SYNTAX',e.message, L[e.loc.line-1].slice(Math.max(0,e.loc.column-150),e.loc.column+60))}}process.exit(bad)"
rm -rf $SP/site170 && cp -r $SP/site161 $SP/site170 && cp $SP/index_v0170.html $SP/site170/index.html
echo built
